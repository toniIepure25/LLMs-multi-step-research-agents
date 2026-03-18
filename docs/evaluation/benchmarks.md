# Benchmarks

> See also: [evaluation-plan.md](evaluation-plan.md) · [OQ-E1](../research/open-questions.md) · [experiment templates](../../experiments/templates/)

## Benchmark Tiers

### Tier 1: Simple Factual Research
- Single-topic questions with known answers
- Example: "What are the main causes of the 2008 financial crisis?"
- **Purpose:** test basic pipeline (`planning` → `execution` → `memory` → output)
- **Ground truth:** available from existing datasets or expert annotation
- **Target phase:** Phase 1

### Tier 2: Multi-Source Synthesis
- Questions requiring information from multiple sources
- Example: "Compare approaches to universal basic income in Finland, Kenya, and Stockton, CA"
- **Purpose:** test parallel `execution`, evidence integration, conflict handling in `deliberation`
- **Ground truth:** expert-annotated coverage rubrics
- **Target phase:** Phase 2–3

### Tier 3: Nuanced / Controversial Topics
- Questions where evidence conflicts or is ambiguous
- Example: "What is the current scientific consensus on long-term effects of intermittent fasting?"
- **Purpose:** test `deliberation`, conflict preservation, `EpistemicStatus` calibration
- **Ground truth:** expert evaluation of balance and accuracy
- **Target phase:** Phase 3

### Tier 4: Deep Technical Research
- Questions requiring domain expertise and multi-step reasoning
- Example: "Tradeoffs between transformer and state-space architectures for long-context language modeling?"
- **Purpose:** test plan depth, `memory` management, technical accuracy
- **Ground truth:** expert evaluation
- **Target phase:** Phase 4

## Existing Datasets to Consider

| Dataset | Useful for | Layer tested |
|---------|-----------|-------------|
| **FEVER** | Fact verification | `verification` |
| **HotpotQA** | Multi-hop QA | `planning`, `execution` |
| **QASPER** | QA over scientific papers | `execution`, `grounding` |
| **SciFact** | Scientific claim verification | `verification`, `grounding` |
| **Natural Questions** | Factoid QA | baseline comparison |

## Custom Benchmark Requirements

Each custom benchmark task needs:
- Research question
- Ground-truth answer or evaluation rubric
- Expected source materials (for controlled experiments)
- Difficulty tier (1–4)
- Which evaluation dimensions apply (from [evaluation-plan.md](evaluation-plan.md))

## Next Action

Build initial set of 10–20 Tier 1 tasks for Phase 1 evaluation. See [tasks/next_steps.md](../../tasks/next_steps.md) item 6.
