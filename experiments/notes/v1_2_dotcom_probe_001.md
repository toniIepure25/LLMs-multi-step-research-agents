# v1_2_dotcom_probe_001

## Question

`What were the main causes of the dot-com crash?`

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
  "What were the main causes of the dot-com crash?" \
  --mode live \
  --output-dir experiments/runs/v1_2_dotcom_probe_001
```

## Artifact paths

- Note: [v1_2_dotcom_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_dotcom_probe_001.md)
- Output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_2_dotcom_probe_001/20260325T232510Z_what-were-the-main-causes-of-the-dot-com_experiment_2555a78480a1/output.json)
- Experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_2_dotcom_probe_001/20260325T232510Z_what-were-the-main-causes-of-the-dot-com_experiment_2555a78480a1/experiment.json)

## Comparison baselines

- active v1-minimal full-set dot-com baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- strongest focused v1-minimal dot-com probe:
  - [v1_dotcom_probe_014.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_dotcom_probe_014.md)
- frozen v0 full-set dot-com baseline:
  - [v0_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v0_tier1_eval_set_004.md)

## Result

### Final claims

1. `Dot-com speculation contributed to the dot-com bubble.`
2. `Tech overvaluation caused a rapid decline in the value of tech stocks.`
3. `Monetary policy and low interest rates contributed to the dot-com bubble.`

### Metrics

- Evidence items: `12`
- Claim count: `3`
- Evidence utilization: `0.25`
- Groundedness: `1.0`
- Verification summary: `supported=3, unsupported=0, insufficient=0, contradicted=0`

## Comparison

### Versus `v1_tier1_eval_set_004` dot-com

`v1_004` claims:
- `Overvaluation of tech companies contributed to the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com crash.`

Assessment:
- `v1_2_001` matches the core metrics:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- wrong-domain crash / vehicle noise stayed gone
- but `v1_2_001` is not clearly better:
  - utilization regressed: `0.3333 -> 0.25`
  - target wording regressed from `the dot-com crash` to `the dot-com bubble` / stock-value wording
  - the regulation / weak-oversight family disappeared
  - a monetary-policy family appeared instead

### Versus `v1_dotcom_probe_014`

`014` claims:
- `Overvaluation of tech companies contributed to the crash.`
- `Lack of regulation in the tech industry contributed to the crash.`
- `Speculation in dotcom businesses caused the crash.`

Assessment:
- both runs have `3` supported claims and `groundedness=1.0`
- `v1_2_001` is more explicit than `014` about a third mechanism family, but it is a different third mechanism
- `014` is still cleaner on the intended dot-com causal framing because it preserved:
  - speculation
  - overvaluation
  - regulation
- `v1_2_001` trades away the regulation family for `Monetary policy and low interest rates...`

### Versus `v0_tier1_eval_set_004` dot-com

`v0_004` claims:
- `Overvaluation of tech companies was a cause of the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com bubble.`

Assessment:
- `v1_2_001` matches `v0_004` on the core metrics:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- but it is not clearly stronger in coherence:
  - `v0_004` keeps the cleaner speculation / overvaluation / regulation triad
  - `v1_2_001` replaces regulation with monetary policy and low interest rates
  - `v0_004` is more directly aligned with the strongest prior dot-com mechanism organization

## Answers

- Did claim count remain healthy?
  - Yes, `3`.
- Did groundedness remain acceptable?
  - Yes, `1.0`.
- Did the speculation family survive when supported?
  - Yes.
- Did the overvaluation / bubble family survive when supported?
  - Yes, though the wording drifted to a stock-value decline claim.
- Did the regulation / weak oversight family survive when supported?
  - No.
- Did wrong-domain crash/vehicle noise stay gone?
  - Yes.
- Did `v1.2` improve dot-com mechanism completeness/coherence?
  - No, not clearly. It stayed complete by count, but the mechanism organization regressed relative to the stronger prior dot-com runs because the regulation family disappeared and target wording became less clean.

## Bottom line

`v1_2_dotcom_probe_001` shows that `v1.2` can stay grounded and avoid wrong-domain retrieval noise on dot-com.

But it does not clearly improve the dot-com completeness/coherence problem:
- claim count stayed healthy
- groundedness stayed `1.0`
- yet the regulation family was lost
- utilization fell back to `0.25`
- final wording became less target-clean than the active v1-minimal baseline

So this is not a strong enough dot-com result to justify a full `v1.2` Tier 1 comparison yet.

## Recommended next step

Stop `v1.2` tuning here.

Across the focused live probes:
- 2008 was mixed
- Great Depression showed a meaningful gain
- dot-com did not clearly improve the strongest prior behavior

That is enough evidence to treat `v1.2` as a promising but unproven exploratory branch rather than the next promoted comparison candidate.
