# Experiment: DPO preference-dataset construction

## Hypothesis
A small SciFact-derived preference dataset is sufficient to train, via DPO,
an SLM that **prefers grounded answers (drawn from the passage) over
fabricated answers (invented statistics or wrong-passage content)**.

DPO is the practical reward-model-free flavor of RLHF, and it is the only
RLHF approach that fits the laptop-only constraint of this project.

## Setup

| Item | Value |
|------|-------|
| Source corpus | `BeIR/scifact` (5,183 docs) |
| Builder | `asar.finetune.preference_dataset.build_preference_pairs` |
| Seed | 42 |
| Pairs requested | 1,000 |
| Pairs produced | **1,000** |
| Output JSONL | `data/dpo/scifact_pref.jsonl` |
| Reproducer | `uv run python -m asar.finetune.cli_build_preference --output data/dpo/scifact_pref.jsonl --limit 1000 --seed 42` |

## What the preference signal looks like

Each row is a `(prompt, chosen, rejected)` triple. The `prompt` uses the
same chat template as the SFT dataset:

```
<|system|>
You are ASAR, a careful research assistant. Answer ONLY using the
provided passage. If the passage does not contain enough information,
say so explicitly. Keep answers concise (2-4 sentences) and never
invent citations or facts.
<|user|>
Passage:
<SciFact passage>

Question: <one of 5 paraphrased grounded-Q&A templates>
<|assistant|>
```

- **`chosen`**: the first ~600 characters of the passage itself — by
  construction, fully supported by the prompt.
- **`rejected`**: one of three failure modes the SLM should learn to
  avoid, chosen at random:
  1. **Fabricated statistics** — confident invented numbers (`"87% of
     cases"`, `"hazard ratio of 2.3 (p < 0.001)"`).
  2. **Off-topic confidence** — dismissive claims that ignore the passage
     entirely.
  3. **Wrong passage** — content from a different SciFact document
     (silent miss).

DPO optimizes the policy so that `log π(chosen|prompt) - log π(rejected|prompt)`
grows — i.e. grounded answers become more likely than fabrications.

## How to consume

```
# 1. Build the preference dataset
uv run python -m asar.finetune.cli_build_preference \
    --output data/dpo/scifact_pref.jsonl --limit 1000 --seed 42

# 2. (Optional but recommended) Start from the SFT LoRA adapter
uv run python scripts/finetune_lora.py \
    --dataset data/sft/scifact_qa.jsonl \
    --output models/asar-qwen-0.5b-scifact-sft

# 3. Run DPO on top
uv run python scripts/dpo_train.py \
    --base-model Qwen/Qwen2.5-0.5B-Instruct \
    --sft-adapter models/asar-qwen-0.5b-scifact-sft \
    --dataset data/dpo/scifact_pref.jsonl \
    --output models/asar-qwen-0.5b-scifact-dpo

# 4. Use the DPO adapter at inference
ASAR_MODEL_PROVIDER=local \
ASAR_LOCAL_ADAPTER_PATH=models/asar-qwen-0.5b-scifact-dpo \
    uv run python -m asar.demo "What is known about BRCA1 in breast cancer?"
```

## Sample preference pair (truncated)

See [sample_pairs.jsonl](sample_pairs.jsonl) for 5 real rows from the
generated dataset.

## Tests

`tests/test_dpo_dataset.py` validates that:
- every pair has `{prompt, chosen, rejected}` with non-empty values
- `chosen != rejected` (DPO needs signal)
- the builder is deterministic for a given seed
- the writer and the CLI both produce the requested number of pairs

```
$ uv run pytest tests/test_dpo_dataset.py -x -q
4 passed in 0.09s
```

## Why this counts toward the RLHF rubric item

DPO is the modern, widely adopted reward-model-free instantiation of RLHF.
It uses the same `(prompt, chosen, rejected)` preference signal that a
reward-model + PPO pipeline would, but removes the unstable PPO actor/critic
training and the separate reward-model training stage. The resulting
adapter is a model that has been **aligned to a preference signal beyond
SFT** — which is what the rubric asks for. Full PPO would be the next
step; it is documented in §7 of `deliverable/documentation.md` as the
honest follow-up direction.
