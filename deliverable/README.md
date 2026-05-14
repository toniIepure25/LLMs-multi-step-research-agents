# ASAR — Final Deliverable

This zip contains the full project: **code, presentation slides, long-form documentation, the results document, and the experiment artifacts that back every claim.**

## Contents

| Path | What it is |
|------|-----------|
| `presentation.pptx` | **6-minute** slide deck (12 slides) — open in PowerPoint / Keynote / Google Slides. Speaker notes embedded — use **Presenter View**. |
| `presentation.md` | Markdown source of the longer 6-section deck (Marp-renderable, fallback if .pptx breaks) |
| `documentation.md` | Long-form project write-up with the same 6-section structure |
| `results.md` | Concrete results & numbers — test totals, RAG timings, demo provenance, safety verdicts, DPO dataset stats |
| `rubric_check.md` | **Grade-10 audit** — every rubric item with file path, test, verify command, and expected output |
| `demo_runbook.md` | **2-minute live demo** — exact commands, what to say, fallbacks if something breaks |
| `experiment_artifacts/` | The actual `output.json` / `experiment.json` / `safety.json` from the end-to-end run referenced in all docs |
| `../` (repo root) | Full source tree, **186 passing tests** |

## How to verify each rubric item in 5 minutes

```
# 1. install
uv sync --extra dev --extra rag

# 2. run the full test suite
uv run pytest -q --ignore=tests/test_live_providers.py
# expected: 186 passed

# 3. index SciFact and run a probe retrieval
uv run python -m asar.execution.rag.cli --dataset scifact --embed-backend hashing

# 4. run the end-to-end demo with RAG + safety
ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus \
    uv run python -m asar.demo "What is known about BRCA1 in breast cancer?" \
    --output-dir /tmp/asar-demo

# 5. build the SFT dataset
uv run python -m asar.finetune.cli_build_dataset \
    --prepare --output data/sft/scifact_qa.jsonl --limit 1500

# 6. build the DPO (RLHF) preference dataset
uv run python -m asar.finetune.cli_build_preference \
    --output data/dpo/scifact_pref.jsonl --limit 1000 --seed 42

# 7. (optional, GPU-friendly) train the LoRA adapters
uv sync --extra dev --extra rag --extra local-llm
uv run python scripts/finetune_lora.py \
    --dataset data/sft/scifact_qa.jsonl \
    --output models/asar-qwen-0.5b-scifact-sft
uv run python scripts/dpo_train.py \
    --sft-adapter models/asar-qwen-0.5b-scifact-sft \
    --dataset data/dpo/scifact_pref.jsonl \
    --output models/asar-qwen-0.5b-scifact-dpo
```

## Rubric mapping

| Rubric item | Where to look |
|------|---------------|
| Data ingestion (new dataset) | `../asar/execution/rag/scifact_loader.py` — BeIR/SciFact, 5,183 docs |
| RAG (chunk + embed + retrieve) | `../asar/execution/rag/{chunker,embedder,retriever}.py` |
| Task-specific fine-tuning (Q&A) | `../asar/finetune/dataset.py` + `../scripts/finetune_lora.py` |
| **RLHF** | `../asar/finetune/preference_dataset.py` + `../scripts/dpo_train.py` — DPO over SciFact preferences |
| Evaluation | `../asar/evaluation/experiment_logger.py` + 186 tests + `experiment_artifacts/` |
| Toxicity / hallucinations | `../asar/safety/` + `../asar/verification/evidence_checker.py` |

**Model tier**: `Qwen/Qwen2.5-0.5B-Instruct` (open-weights SLM), fine-tuned with both **SFT** and **DPO** — rubric ceiling **grade 10**.

## Reading order suggested

1. `rubric_check.md` — the 6-item grade-10 audit, each with verify command
2. `presentation.pptx` — open and skim (~6 min talk)
3. `demo_runbook.md` — the 2-minute live demo plan
4. `results.md` — concrete numbers and command outputs
5. `documentation.md` — long-form deep dive
6. `experiment_artifacts/output.json` — actual evidence + claims emitted by the system
7. `../experiments/runs/2026-05-14_rag_safety_e2e/README.md` — end-to-end experiment report
8. `../experiments/runs/2026-05-14_dpo_preference_dataset/README.md` — DPO experiment report
9. `../PROJECT_DOSSIER.md` — full architectural manifesto
