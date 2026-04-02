# v1_tier1_eval_set_004

## Questions

1. `What were the main causes of the 2008 financial crisis?`
2. `What were the main causes of the Great Depression?`
3. `What were the main causes of the dot-com crash?`

## Exact commands used

```bash
set -a && source .secrets && \
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live \
  --output-dir experiments/runs/v1_tier1_eval_set_004/financial_crisis_2008
```

```bash
set -a && source .secrets && \
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the Great Depression?" \
  --mode live \
  --output-dir experiments/runs/v1_tier1_eval_set_004/great_depression
```

```bash
set -a && source .secrets && \
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the dot-com crash?" \
  --mode live \
  --output-dir experiments/runs/v1_tier1_eval_set_004/dot_com_crash
```

## Artifact paths

- Aggregate note: [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- 2008 output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/financial_crisis_2008/20260320T001657Z_what-were-the-main-causes-of-the-2008-fi_experiment_c5f84fe7b3ec/output.json)
- 2008 experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/financial_crisis_2008/20260320T001657Z_what-were-the-main-causes-of-the-2008-fi_experiment_c5f84fe7b3ec/experiment.json)
- Great Depression output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/great_depression/20260320T001652Z_what-were-the-main-causes-of-the-great-d_experiment_9201a9c6ce4d/output.json)
- Great Depression experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/great_depression/20260320T001652Z_what-were-the-main-causes-of-the-great-d_experiment_9201a9c6ce4d/experiment.json)
- Dot-com output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/dot_com_crash/20260320T001703Z_what-were-the-main-causes-of-the-dot-com_experiment_82285efe4a1c/output.json)
- Dot-com experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_004/dot_com_crash/20260320T001703Z_what-were-the-main-causes-of-the-dot-com_experiment_82285efe4a1c/experiment.json)

## Per-question assessment

### 2008 financial crisis

- Metrics: evidence `9`, utilization `0.3333`, groundedness `1.0`, claims `3`, `supported=3`
- Final claims:
  - `Financial deregulation ... was a significant factor in preparing the conditions for the 2008 financial crisis.`
  - `The securitization of loans into securities that are then sold to investors contributed to the 2008 financial crisis.`
  - `Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.`
- Assessment:
  - The focused recovery from [v1_2008_probe_016.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2008_probe_016.md) held on the core metrics.
  - Claim count stayed at `3`, groundedness stayed `1.0`, and OTC derivatives remained present.
  - The subprime-family wording from the focused probe shifted back toward a securitization claim, but it stayed grounded and direct.
  - This is clearly stronger than the 2008 run inside [v1_tier1_eval_set_003.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_003.md).

### Great Depression

- Metrics: evidence `11`, utilization `0.1818`, groundedness `1.0`, claims `3`, `supported=3`
- Final claims:
  - `War reparations post-World War I contributed to the Great Depression.`
  - `The stock market crash of 1929 contributed to the Great Depression.`
  - `The Smoot-Hawley Tariff contributed to the Great Depression.`
- Assessment:
  - The focused recovery from [v1_great_depression_probe_016.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_great_depression_probe_016.md) broadly held.
  - Claim count stayed at `3`, groundedness stayed `1.0`, and the world-trade / Smoot-Hawley family remained present.
  - Mechanism diversity is better than the weak prior full-set run, though still not as strong as the best earlier Great Depression run because the monetary-contraction family is absent.

### Dot-com crash

- Metrics: evidence `12`, utilization `0.3333`, groundedness `1.0`, claims `3`, `supported=3`
- Final claims:
  - `Overvaluation of tech companies contributed to the dot-com crash.`
  - `Lack of regulation in the tech industry contributed to the dot-com crash.`
  - `Speculation in dotcom or internet-based businesses caused the dot-com crash.`
- Assessment:
  - Dot-com remained clean and complete.
  - Wrong-domain crash/vehicle noise did not return.
  - This is as clean as [v1_dotcom_probe_014.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_dotcom_probe_014.md), with slightly better target wording because claims explicitly name `the dot-com crash`.

## Aggregate comparison

### Versus v1_tier1_eval_set_003

- `v1_004` is clearly stronger overall.
- 2008 improved from `2` claims to `3` and held `groundedness=1.0`.
- Great Depression improved from `2` claims to `3` and retained better mechanism diversity.
- Dot-com stayed strong and complete.

### Versus frozen v0_tier1_eval_set_004

- 2008 is materially better in claim specificity and directness.
  - `v0_004` had two snippet-like securitization claims.
  - `v1_004` has three direct causal claims, all supported.
- Great Depression is mixed versus frozen v0.
  - `v1_004` is more specific on stock crash and Smoot-Hawley.
  - `v0_004` still had somewhat broader mechanism coverage.
- Dot-com is at least as strong as frozen v0 and remains clean.

## Answers

- Did v1-minimal maintain the 2008 recovery from `v1_2008_probe_016`?
  - Yes, on the core metrics and main mechanism coverage.
- Did Great Depression maintain the diversity/completeness gains from `v1_great_depression_probe_016`?
  - Yes, mostly. Claim count and trade-family recovery held, though monetary-contraction did not return.
- Did dot-com remain clean and complete?
  - Yes.
- Did groundedness remain acceptable across all 3?
  - Yes, `1.0` across all 3 runs.
- Did claim specificity improve enough overall versus frozen v0?
  - Yes overall, mainly because 2008 improved substantially and dot-com stayed clean.
- Is `v1_tier1_eval_set_004` strong enough to become the active experimental baseline for v1-minimal?
  - Yes.

## Bottom line

`v1_tier1_eval_set_004` is the first full live v1-minimal set that looks strong enough to serve as the active experimental baseline for v1-minimal. It does not make frozen v0 obsolete as a historical reference, but it is the best current live v1-minimal comparison point.
