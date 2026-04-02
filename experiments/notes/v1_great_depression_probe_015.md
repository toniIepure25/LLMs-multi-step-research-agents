# v1_great_depression_probe_015

## Question

`What were the main causes of the Great Depression?`

## Exact command used

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
  --output-dir experiments/runs/v1_great_depression_probe_015
```

## Artifact paths

- Output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_great_depression_probe_015/20260319T231457Z_what-were-the-main-causes-of-the-great-d_experiment_e1c09be4aa54/output.json)
- Experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_great_depression_probe_015/20260319T231457Z_what-were-the-main-causes-of-the-great-d_experiment_e1c09be4aa54/experiment.json)

## Comparison baseline choice

I used:

- the Great Depression run inside [v1_tier1_eval_set_003.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_003.md) as the previous v1 comparison
- the Great Depression run inside [v1_tier1_eval_set_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_002.md) as the strongest prior acceptable Great Depression run

## Result

### Final claims

1. `Stock market crashes contributed to the Great Depression.`
2. `Bank failures contributed to the Great Depression.`
3. `Reduced consumer spending contributed to the Great Depression.`

### Metrics

- Evidence items: `12`
- Claim count: `3`
- Evidence utilization: `0.0833`
- Groundedness: `1.0`
- Supported claims: `3`
- Verification summary: `supported=3, unsupported=0, insufficient=0, contradicted=0`

## Comparison

### Versus the Great Depression run inside v1_tier1_eval_set_003

- `015` recovered raw completeness:
  - claim count `2 -> 3`
  - supported claims `2 -> 3`
- `015` also restored the stock-market-crash family, which had disappeared in `v1_003`
- groundedness stayed `1.0`

But:

- `015` lost the protectionism / world-trade-collapse family that `v1_003` still had
- evidence utilization got worse: `0.1667 -> 0.0833`
- all 3 claims were supported by the same broad evidence item, which is a brittle recovery

### Versus the strongest prior acceptable run: v1_tier1_eval_set_002

- `v1_002` is still clearly stronger overall
- both runs have:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- but `v1_002` had the better mechanism mix:
  - stock market crash
  - Smoot-Hawley / world trade collapse
  - money supply collapse
- `015` is less specific and less diverse:
  - stock market crashes
  - bank failures
  - reduced consumer spending
- `v1_002` also had much better evidence utilization: `0.4` vs `0.0833`

## Assessment

- Direct causal phrasing remained acceptable.
- The stock-market-crash family did appear when supported.
- A banking/bank-failure family also appeared.
- The protectionism / world-trade-collapse family did **not** survive in this run.
- The money-supply / monetary-contraction family also did **not** survive.
- So completeness improved versus the weak `v1_003` run, but not in the strongest or most stable way.

## Answers

- Did claim count return to 3?
  - Yes.
- Did groundedness remain acceptable?
  - Yes, `1.0`.
- Did the stock-market-crash family appear?
  - Yes.
- Did a monetary-contraction / banking-panics family appear?
  - Only partially. `Bank failures` appeared, but not the stronger monetary-contraction form.
- Did the protectionism / world-trade-collapse family appear?
  - No.

## Bottom line

`v1_great_depression_probe_015` is better than the weak Great Depression run inside `v1_tier1_eval_set_003`, because it recovers 3 supported claims and keeps groundedness at `1.0`. But it is still weaker than the strongest prior acceptable Great Depression run, because mechanism diversity and evidence utilization both regressed.
