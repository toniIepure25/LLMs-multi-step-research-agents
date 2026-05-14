"""
DPO (Direct Preference Optimization) training script for the ASAR local SLM.

DPO is the reward-model-free flavor of RLHF: instead of training a separate
reward model and running PPO, we optimize directly on ``(prompt, chosen,
rejected)`` triples. This is the practical RLHF path for laptop training
(no GPU, no PPO actor/critic split, no separate reward model).

Pipeline:

    1. Optionally start from the SFT LoRA adapter produced by
       ``scripts/finetune_lora.py`` (recommended).
    2. Load Qwen2.5-0.5B-Instruct + LoRA adapters on q/k/v/o projections.
    3. Train with ``trl.DPOTrainer`` on the SciFact preference JSONL built by
       ``asar.finetune.cli_build_preference``.
    4. Save the resulting DPO-tuned adapter where ``LocalSLMClient`` can
       load it via ``ASAR_LOCAL_ADAPTER_PATH``.

Example::

    uv run python scripts/dpo_train.py \\
        --base-model Qwen/Qwen2.5-0.5B-Instruct \\
        --dataset data/dpo/scifact_pref.jsonl \\
        --output models/asar-qwen-0.5b-scifact-dpo \\
        --epochs 1 --batch-size 1 --grad-accum 8

Designed for Mac CPU / MPS — defaults stay tiny on purpose.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install local-llm extras: `uv sync --extra local-llm`.") from exc
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DPO training for the ASAR local SLM.")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument(
        "--sft-adapter",
        default=None,
        help="Optional SFT LoRA adapter directory to start from (recommended).",
    )
    parser.add_argument("--dataset", default="data/dpo/scifact_pref.jsonl")
    parser.add_argument("--output", default="models/asar-qwen-0.5b-scifact-dpo")
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--beta", type=float, default=0.1, help="DPO beta (KL trade-off).")
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--max-prompt-len", type=int, default=768)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--limit", type=int, default=None, help="Cap on number of preference pairs.")
    parser.add_argument("--logging-steps", type=int, default=10)
    args = parser.parse_args(argv)

    try:
        import torch  # type: ignore
        from datasets import Dataset  # type: ignore
        from peft import LoraConfig, PeftModel  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
        )
        from trl import DPOTrainer  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Local LLM extras are not installed. Run `uv sync --extra local-llm`.\n"
            f"Import error: {exc}"
        ) from exc

    device = _resolve_device(args.device)
    print(f"[dpo] device = {device}")

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise SystemExit(
            f"Dataset not found: {dataset_path}\n"
            "Build it first with: uv run python -m asar.finetune.cli_build_preference --prepare"
        )

    rows: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not all(k in row for k in ("prompt", "chosen", "rejected")):
                continue
            rows.append(row)
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit(f"Dataset is empty: {dataset_path}")
    print(f"[dpo] loaded {len(rows)} preference pairs")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    hf_dataset = Dataset.from_list(rows)

    torch_dtype = torch.float32  # MPS prefers float32 for stability
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )
    if args.sft_adapter:
        print(f"[dpo] loading SFT adapter from {args.sft_adapter}")
        model = PeftModel.from_pretrained(model, args.sft_adapter, is_trainable=True)
    model.to(device)

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    training_args = TrainingArguments(
        output_dir=str(Path(args.output) / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        logging_steps=args.logging_steps,
        save_strategy="no",
        report_to="none",
        seed=args.seed,
        bf16=False,
        fp16=False,
        optim="adamw_torch",
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        remove_unused_columns=False,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # DPOTrainer will use the frozen LoRA-disabled base as reference.
        args=training_args,
        train_dataset=hf_dataset,
        tokenizer=tokenizer,
        peft_config=None if args.sft_adapter else lora_config,
        beta=args.beta,
        max_length=args.max_seq_len,
        max_prompt_length=args.max_prompt_len,
    )

    print("[dpo] starting training...")
    trainer.train()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metadata = {
        "stage": "dpo",
        "base_model": args.base_model,
        "sft_adapter": args.sft_adapter,
        "dataset": str(dataset_path),
        "n_preference_pairs": len(rows),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "grad_accum": args.grad_accum,
        "learning_rate": args.learning_rate,
        "beta": args.beta,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "seed": args.seed,
        "device": device,
    }
    (output_dir / "asar_dpo_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(f"[dpo] done. DPO adapter saved to {output_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
