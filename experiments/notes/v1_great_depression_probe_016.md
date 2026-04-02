# v1_great_depression_probe_016

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
  --output-dir experiments/runs/v1_great_depression_probe_016
```

## Artifact paths

- Output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_great_depression_probe_016/20260319T235519Z_what-were-the-main-causes-of-the-great-d_experiment_ba884ba54bbe/output.json)
- Experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_great_depression_probe_016/20260319T235519Z_what-were-the-main-causes-of-the-great-d_experiment_ba884ba54bbe/experiment.json)

## Comparison baseline choice

I used:

- the Great Depression run inside [v1_tier1_eval_set_003.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_003.md) as the weak previous v1 comparison
- the Great Depression run inside [v1_tier1_eval_set_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_002.md) as the strongest prior acceptable Great Depression run

## Result

### Final claims

1. `The stock market crash of 1929 contributed to the Great Depression.`
2. `The collapse of world trade due to the Smoot-Hawley Tariff contributed to the Great Depression.`
3. `War reparations post-World War I contributed to the Great Depression.`

### Metrics

- Evidence items: `11`
- Claim count: `3`
- Evidence utilization: `0.1818`
- Groundedness: `1.0`
- Supported claims: `3`
- Verification summary: `supported=3, unsupported=0, insufficient=0, contradicted=0`

## Comparison

### Versus v1_great_depression_probe_015

- `016` is a real improvement in final-set composition.
- `015` had all 3 claims backed by one source; `016` spreads support across two sources.
- `015` had broad claim mix:
  - stock market crashes
  - bank failures
  - reduced consumer spending
- `016` restores sharper mechanism families:
  - stock market crash of 1929
  - Smoot-Hawley / world trade collapse
  - war reparations
- evidence utilization improved from `0.0833 -> 0.1818`
- groundedness stayed `1.0`

### Versus the Great Depression run inside v1_tier1_eval_set_003

- `016` improves claim count from `2 -> 3`
- `016` keeps groundedness at `1.0`
- `016` is more complete and more specific than `v1_003`
- both runs retain a political/trade family, but `016` adds the stock-market-crash family that `v1_003` lacked

### Versus the strongest prior acceptable run: v1_tier1_eval_set_002

- `v1_002` is still stronger overall
- both runs have:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- but `v1_002` had the better diversity mix:
  - stock market crash
  - world trade collapse / Smoot-Hawley
  - money supply collapse
- `016` still misses the monetary-contraction family
- `v1_002` also keeps better evidence utilization: `0.4` vs `0.1818`

## Assessment

- Direct causal phrasing remained acceptable.
- The stock-market-crash family appeared.
- The protectionism / world-trade-collapse family appeared.
- The monetary-contraction / money-supply-collapse family did **not** appear.
- Support is less concentrated than in `015`, but still not as diverse as the best prior run.

## Answers

- Did claim count remain at 3?
  - Yes.
- Did groundedness remain near 1.0?
  - Yes, `1.0`.
- Did the stock-market-crash family appear when supported?
  - Yes.
- Did the protectionism / world-trade-collapse family appear when supported?
  - Yes.
- Did the monetary contraction / banking-panics family appear when supported?
  - No.
- Did support become less concentrated in one broad source?
  - Yes, partially. The final set now uses two sources instead of one, but still not as many distinct sources as the strongest prior acceptable run.

## Bottom line

`v1_great_depression_probe_016` is a meaningful improvement over `v1_great_depression_probe_015`: it keeps `3` supported claims, preserves groundedness, and improves mechanism and source diversity. But it is still not as strong as the best prior acceptable Great Depression run because the monetary-contraction family is still missing and evidence diversity remains only partial.
