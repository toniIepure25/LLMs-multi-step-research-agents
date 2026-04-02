# v1 Tier 1 Eval Set 002

## Scope

Second full 3-question live Tier 1 evaluation set for v1-minimal after the
narrow candidate-generation hardening pass for 2008 stability.

This step tests whether the focused 2008 recovery from `v1_2008_probe_013`
holds in a full live evaluation without unacceptable regressions on the other
two questions.

Frozen v0 remains the reference baseline:

- `experiments/notes/v0_tier1_eval_set_004.md`

The first full v1 comparison record remains:

- `experiments/notes/v1_tier1_eval_set_001.md`

No Phase 2 features were introduced in this step.

## Questions

1. `What were the main causes of the 2008 financial crisis?`
2. `What were the main causes of the Great Depression?`
3. `What were the main causes of the dot-com crash?`

## Provider Configuration

- `ASAR_MODEL_PROVIDER=openai`
- `ASAR_MODEL_MODEL=llama3.1:8b`
- `ASAR_OPENAI_BASE_URL=https://inference.ccrolabs.com/v1`
- `ASAR_SEARCH_PROVIDER=tavily`

Secrets were supplied via `.secrets` at runtime and are intentionally omitted
here.

## Exact Commands Used

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
  --output-dir experiments/runs/v1_tier1_eval_set_002/financial_crisis_2008
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
  --output-dir experiments/runs/v1_tier1_eval_set_002/great_depression
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
  --output-dir experiments/runs/v1_tier1_eval_set_002/dot_com_crash
```

## New Artifact Paths

### Run A: 2008 Financial Crisis

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/financial_crisis_2008/20260319T190810Z_what-were-the-main-causes-of-the-2008-fi_experiment_5bd807dc5d3c/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/financial_crisis_2008/20260319T190810Z_what-were-the-main-causes-of-the-2008-fi_experiment_5bd807dc5d3c/experiment.json`

### Run B: Great Depression

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/great_depression/20260319T190820Z_what-were-the-main-causes-of-the-great-d_experiment_05fe062ea391/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/great_depression/20260319T190820Z_what-were-the-main-causes-of-the-great-d_experiment_05fe062ea391/experiment.json`

### Run C: Dot-Com Crash

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/dot_com_crash/20260319T190815Z_what-were-the-main-causes-of-the-dot-com_experiment_ec1213952bf0/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_002/dot_com_crash/20260319T190815Z_what-were-the-main-causes-of-the-dot-com_experiment_ec1213952bf0/experiment.json`

## Comparison Targets

- frozen v0 baseline: `v0_tier1_eval_set_004`
- first full v1 comparison record: `v1_tier1_eval_set_001`
- focused 2008 recovery probe: `v1_2008_probe_013`

## Run A: 2008 Financial Crisis

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_001`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count: stayed at `7` versus `v1_001`, still below frozen `004` (`8`).
- Evidence utilization:
  - improved versus `v1_001`: `0.2857 -> 0.4286`
  - improved versus frozen `004`: `0.375 -> 0.4286`
- Groundedness:
  - improved versus `v1_001`: `0.5 -> 0.6667`
  - still worse than frozen `004`: `1.0 -> 0.6667`
- Claim count:
  - improved versus `v1_001`: `2 -> 3`
  - matched frozen `004`: `3`
- Verification:
  - improved versus `v1_001`: `supported=1, insufficient=1 -> supported=2, insufficient=1`
  - still worse than frozen `004`: `supported=3`
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_002`

- key events:
  - `Financial Crisis and Recovery: Financial Crisis Timeline`
  - `The 2008 Financial Crisis Explained - Investopedia`
  - `Why did the global financial crisis of 2007-09 happen?`
- deregulation:
  - `Did Deregulation Cause the Financial Crisis of 2008? - QuantGov`
  - `[PDF] Foreword: Deregulation: A Major Cause of the Financial Crisis`
  - `Lesson 8: Deregulation and the 2008 Financial Crisis`
- securitization:
  - `The Role of Securitization in Bank Liquidity and Financial Stability`

### Claims

`v1_002`

- `Securitization contributed to the 2008 financial crisis.`
- `The failure of subprime mortgage-backed securities contributed to the 2008 financial crisis.`
- `Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.`

### Assessment

- This is better than the weak 2008 run inside `v1_tier1_eval_set_001`.
- The sharper OTC-derivatives claim returned.
- Claim count recovered to `3`.
- But the focused `v1_2008_probe_013` recovery did not fully hold:
  - `groundedness` fell from `1.0` to `0.6667`
  - the securitization claim became `insufficient` again
- Net result: improved versus `v1_001`, but still not stably as strong as `v1_2008_probe_013` or frozen `004`.

## Run B: Great Depression

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_001`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count:
  - improved over both `v0_004` and `v1_001`: `12 -> 10`
- Evidence utilization:
  - improved over both `v0_004` and `v1_001`: `0.25 -> 0.4`
- Groundedness: unchanged at `1.0`.
- Claim count: unchanged at `3`.
- Verification: unchanged at `supported=3`.
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_002`

- primary-source step:
  - `Great Depression & New Deal - Primary Sources: America (U.S.A. ...`
  - `Great Depression 1929-1939 - Primary Resources`
  - `Primary Sources: The Great Depression and the 1930s: General`
- categorization step:
  - `American History Topic 6, Lesson 1: Causes of the ...`
  - `What Caused the Great Depression? | St. Louis Fed`
  - `Political Causes of the Great Depression`
- scholarly step:
  - `Essays on the Great Depression - jstor`
- synthesis step:
  - `The Great Depression: Overview, Causes, and Effects - Investopedia`
  - `Causes of the Great Depression - Wikipedia`
  - `5 Causes of the Great Depression - History.com`

### Claims

`v1_002`

- `The stock market crash of 1929 contributed to the Great Depression.`
- `The collapse of world trade due to the Smoot-Hawley Tariff contributed to the Great Depression.`
- `The worldwide collapse in national money supplies contributed to the Great Depression.`

### Assessment

- Great Depression is the strongest run in `v1_002`.
- It is cleaner than `v1_001`, more specific than frozen `004`, and better grounded than needed.
- The evidence pool is smaller and more efficient.
- Net result: clear improvement over both frozen `004` and `v1_001`.

## Run C: Dot-Com Crash

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_001`

- Plan quality: stayed on the improved `speculation and hype` path from `v1_001`.
- Evidence count: unchanged at `12`.
- Evidence utilization:
  - regressed versus `v1_001`: `0.3333 -> 0.25`
  - returned to frozen `004` level: `0.25`
- Groundedness: unchanged at `1.0`.
- Claim count:
  - regressed versus both `v0_004` and `v1_001`: `3 -> 2`
- Verification: `supported=2`.
- Plan coverage: unchanged at `1.0`.

### Technology / Speculation Step

`v1_002`

- step: `Analyze the role of speculation and hype in the dot-com bubble`
- query: `Analyze the role of speculation and hype in the dot-com bubble`

Surviving speculation-step titles:

- `From Hype to Bust: Investigating the Underlying Factors of ...`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `The Dot-Com Bubble Explained`

### Claims

`v1_002`

- `Speculation in dotcom or internet-based businesses from 1995 to 2000 caused the dotcom bubble.`
- `Overvaluation of tech companies contributed to the dot-com crash.`

### Assessment

- Dot-com remained clean in retrieval terms.
- The old wrong-domain car-crash / vehicle-safety / distractive-driving noise did not return.
- But final claim count regressed from `3` to `2`, and the regulation claim disappeared.
- Net result: retrieval stayed good, but final answer quality regressed versus `v1_001`.

## Aggregate Comparison

### Did v1-minimal maintain the 2008 recovery from `v1_2008_probe_013`?

No, not fully.

`v1_002` did better than the weak 2008 run in `v1_tier1_eval_set_001`, but it
did not hold the full recovery from `v1_2008_probe_013`:

- claim count stayed healthy at `3`
- OTC stayed preserved
- but groundedness fell from `1.0` to `0.6667`
- and the securitization claim became `insufficient` again

### Did dot-com remain clean?

Yes, on retrieval cleanliness.

- the speculation path remained on-topic
- wrong-domain crash/vehicle noise did not return

But answer completeness regressed because claim count fell to `2`.

### Did Great Depression remain acceptable?

Yes, and more than acceptable.

It is the clearest win in this full set:

- groundedness stayed `1.0`
- evidence utilization improved strongly
- evidence count shrank
- claims are specific and on-question

### Did groundedness remain acceptable across all 3?

Mixed.

- 2008 financial crisis: `0.6667`
- Great Depression: `1.0`
- dot-com crash: `1.0`

So groundedness remained acceptable on 2 of 3 questions, but 2008 still did
not reach the bar set by the stronger focused probe.

### Did claim specificity improve overall versus frozen v0?

Mixed.

- 2008: cleaner claim shapes than frozen `004`, but still unstable
- Great Depression: improved
- dot-com: mixed, because specificity rose in one claim but the final answer set shrank

Overall, specificity improved in parts of the set but not strongly enough to
declare a full-set win over frozen v0.

## Conclusion

### Is `v1_tier1_eval_set_002` strong enough to become the active experimental baseline for v1-minimal?

Not yet.

`v1_tier1_eval_set_002` is a better comparison record than `v1_tier1_eval_set_001`
because:

- 2008 improved over the first full v1 attempt
- Great Depression improved materially
- dot-com stayed retrieval-clean

But it still does not clearly beat frozen `v0_tier1_eval_set_004` overall
because:

- 2008 did not stably hold the focused `013` recovery
- dot-com regressed in claim count and answer completeness

So `v1_tier1_eval_set_002` should remain a comparison record, not the active
experimental baseline yet.
