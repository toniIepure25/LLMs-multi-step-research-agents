"""
LoRA fine-tuning script for the ASAR local SLM provider.

Trains a LoRA adapter on top of a small instruction-tuned base model using a
JSONL chat-format dataset (see ``scripts/build_sft_dataset.py``). Designed for
Mac CPU / MPS — defaults stay tiny on purpose.

Example:

    uv run python scripts/finetune_lora.py \\
        --base-model Qwen/Qwen2.5-0.5B-Instruct \\
        --dataset data/sft/scifact_qa.jsonl \\
        --output models/asar-qwen-0.5b-scifact-lora \\
        --epochs 1 \\
        --batch-size 1 \\
        --grad-accum 8 \\
        --learning-rate 2e-4 \\
        --max-seq-len 1024 \\
        --device auto

Produces a Hugging Face LoRA adapter directory that ``LocalSLMClient`` can
load via ``ASAR_LOCAL_ADAPTER_PATH``.
"""

from __future__ import annotations

import argparse
import json
import sys
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
    parser = argparse.ArgumentParser(description="LoRA SFT for the ASAR local SLM.")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--dataset", default="data/sft/scifact_qa.jsonl")
    parser.add_argument("--output", default="models/asar-qwen-0.5b-scifact-lora")
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--limit", type=int, default=None, help="Cap on number of train examples.")
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument(
        "--resume-adapter",
        default=None,
        help="Path to an existing LoRA adapter to continue training from. If set, no fresh LoRA is attached.",
    )
    parser.add_argument(
        "--lora-targets",
        default="q_proj,k_proj,v_proj,o_proj",
        help=(
            "Comma-separated LoRA target_modules. Default = attention only. "
            "Include MLP for higher capacity, e.g. "
            "`q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`."
        ),
    )
    parser.add_argument(
        "--assistant-only-loss",
        action="store_true",
        help=(
            "Mask non-assistant tokens so the loss only counts assistant-turn "
            "tokens. Recommended for chat-format SFT — makes the loss signal "
            "reflect what the model actually has to generate."
        ),
    )
    args = parser.parse_args(argv)

    try:
        import torch  # type: ignore
        from datasets import Dataset  # type: ignore
        from peft import LoraConfig  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
        )
        from trl import SFTConfig, SFTTrainer  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Local LLM extras are not installed. Run `uv sync --extra local-llm`.\n"
            f"Import error: {exc}"
        ) from exc

    device = _resolve_device(args.device)
    print(f"[finetune] device = {device}")

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise SystemExit(
            f"Dataset not found: {dataset_path}\n"
            "Build it first with: uv run python scripts/build_sft_dataset.py --prepare"
        )

    rows: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit(f"Dataset is empty: {dataset_path}")
    print(f"[finetune] loaded {len(rows)} examples")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # When assistant_only_loss is enabled we feed the conversational format
    # (a `messages` column) to TRL directly; the trainer applies the chat
    # template itself and masks non-assistant tokens. Otherwise we pre-render
    # to a plain `text` column — the legacy behavior used by v1 / v2 adapters.
    if args.assistant_only_loss:
        hf_dataset = Dataset.from_list(rows)
    else:
        def to_text(example: dict) -> dict:
            text = tokenizer.apply_chat_template(
                example["messages"], tokenize=False, add_generation_prompt=False
            )
            return {"text": text}

        hf_dataset = Dataset.from_list(rows).map(to_text, remove_columns=["messages"])

    torch_dtype = torch.float32 if device == "cpu" else torch.float32  # MPS prefers float32 for stability
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )

    if args.resume_adapter:
        from peft import PeftModel  # type: ignore

        print(f"[finetune] resuming from adapter {args.resume_adapter}")
        model = PeftModel.from_pretrained(model, args.resume_adapter, is_trainable=True)
    model.to(device)

    lora_target_modules = [t.strip() for t in args.lora_targets.split(",") if t.strip()]
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=lora_target_modules,
    )

    sft_config_kwargs: dict = dict(
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
        lr_scheduler_type="cosine",
        warmup_steps=10,
        remove_unused_columns=False,
        max_length=args.max_seq_len,
        packing=False,
    )
    if args.assistant_only_loss:
        sft_config_kwargs["assistant_only_loss"] = True
    else:
        sft_config_kwargs["dataset_text_field"] = "text"

    training_args = SFTConfig(**sft_config_kwargs)

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=hf_dataset,
        peft_config=None if args.resume_adapter else lora_config,
        processing_class=tokenizer,
    )

    print("[finetune] starting training...")
    trainer.train()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metadata = {
        "base_model": args.base_model,
        "resume_adapter": args.resume_adapter,
        "dataset": str(dataset_path),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "grad_accum": args.grad_accum,
        "learning_rate": args.learning_rate,
        "max_seq_len": args.max_seq_len,
        "assistant_only_loss": args.assistant_only_loss,
        "lora": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
            "target_modules": lora_target_modules,
        },
        "examples": len(rows),
        "device": device,
        "seed": args.seed,
    }
    (output_dir / "asar_finetune_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"[finetune] adapter saved to {output_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
