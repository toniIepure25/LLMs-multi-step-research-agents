# v1 Tier 1 Eval Set 001

## Scope

First full 3-question live Tier 1 evaluation set for v1-minimal after:

- the candidate-claim generation boundary was introduced
- the deterministic `ClaimSelector` was added
- the focused 2008 probe sequence culminated in `v1_2008_probe_012`

This step tests whether the focused v1-minimal gains generalize to the full
live Tier 1 set without unacceptable regressions.

Frozen v0 remains the reference baseline:

- `experiments/notes/v0_tier1_eval_set_004.md`

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
  --output-dir experiments/runs/v1_tier1_eval_set_001/financial_crisis_2008
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
  --output-dir experiments/runs/v1_tier1_eval_set_001/great_depression
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
  --output-dir experiments/runs/v1_tier1_eval_set_001/dot_com_crash
```

## New Artifact Paths

### Run A: 2008 Financial Crisis

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/financial_crisis_2008/20260319T180720Z_what-were-the-main-causes-of-the-2008-fi_experiment_7259bb7c6438/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/financial_crisis_2008/20260319T180720Z_what-were-the-main-causes-of-the-2008-fi_experiment_7259bb7c6438/experiment.json`

### Run B: Great Depression

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/great_depression/20260319T180732Z_what-were-the-main-causes-of-the-great-d_experiment_237d12f83faf/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/great_depression/20260319T180732Z_what-were-the-main-causes-of-the-great-d_experiment_237d12f83faf/experiment.json`

### Run C: Dot-Com Crash

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/dot_com_crash/20260319T180725Z_what-were-the-main-causes-of-the-dot-com_experiment_48af7499c9c9/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_001/dot_com_crash/20260319T180725Z_what-were-the-main-causes-of-the-dot-com_experiment_48af7499c9c9/experiment.json`

## Comparison Target

- frozen v0 live baseline: `v0_tier1_eval_set_004`
- focused 2008 live checkpoint: `v1_2008_probe_012`

## Run A: 2008 Financial Crisis

### Before / After vs `v0_tier1_eval_set_004`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count: regressed from `8` to `7`.
- Evidence utilization: regressed from `0.375` to `0.2857`.
- Groundedness: regressed from `1.0` to `0.5`.
- Claim count: regressed from `3` to `2`.
- Verification: regressed from `supported=3` to `supported=1, insufficient=1`.
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_001`

- key events:
  - `Financial Crisis and Recovery: Financial Crisis Timeline`
  - `The 2008 Financial Crisis Explained - Investopedia`
  - `Why did the global financial crisis of 2007-09 happen?`
- deregulation:
  - `Lesson 8: Deregulation and the 2008 Financial Crisis`
  - `Did Deregulation Cause the Financial Crisis of 2008? - QuantGov`
  - `[PDF] Foreword: Deregulation: A Major Cause of the Financial Crisis`
- securitization:
  - `The Role of Securitization in Bank Liquidity and Financial Stability`

### Claims

`v0_004`

- `Securitization is more than just a capital markets innovation—it’s a multifaceted process that bridges the gap between lending institutions and investors seeking income-generating assets.`
- `The securitization of loans into securities provides an additional funding source and potentially eliminates assets from banks' balance sheets.`
- `The deregulation of the OTC derivatives market contributed to the 2008 financial crisis.`

`v1_001`

- `Deregulation of the Financial System contributed to the 2008 financial crisis.`
- `Securitization of subprime mortgages contributed to the 2008 financial crisis.`

### Assessment

- The strong focused gains from `v1_2008_probe_012` did not hold in the full 3-question run.
- The `housing crisis` drift did not return, but the sharper OTC-derivatives claim disappeared.
- The broad same-family umbrella deregulation claim returned.
- The securitization claim became over-specific again and verified as `insufficient`.
- Net result: worse than both `v1_2008_probe_012` and frozen `004`.

## Run B: Great Depression

### Before / After vs `v0_tier1_eval_set_004`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: unchanged at `12`.
- Evidence utilization: unchanged at `0.25`.
- Groundedness: unchanged at `1.0`.
- Claim count: unchanged at `3`.
- Verification: unchanged at `supported=3`.
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_001`

- primary-source step:
  - `Great Depression 1929-1939 - Primary Resources`
  - `Great Depression & New Deal - Primary Sources: America (U.S.A. ...`
  - `Primary Sources: The Great Depression and the 1930s: General`
- categorization step:
  - `What Caused the Great Depression? | St. Louis Fed`
  - `Political Causes of the Great Depression - ThoughtCo`
  - `Causes of the Great Depression | Britannica`
- scholarly step:
  - `Causes of the Great Depression | Britannica`
  - `[PDF] What Caused the Great Depression? - Social Studies`
  - `The Great Depression(s) of 1929-1933 and 2007-2009? Parallels ...`
- synthesis step:
  - `5 Causes of the Great Depression - History.com`
  - `The Great Depression: Overview, Causes, and Effects - Investopedia`
  - `Causes of the Great Depression - Wikipedia`

### Claims

`v0_004`

- `The stock market crash of 1929 triggered the Great Depression.`
- `Bank failures and reduced consumer spending contributed to the Great Depression.`
- `A collapse in confidence, tariffs reducing trade, and a gold standard contributed to the Great Depression.`

`v1_001`

- `The stock market crash of 1929 contributed to the start of the Great Depression.`
- `The collapse of world trade due to the Smoot-Hawley Tariff contributed to the Great Depression.`
- `War reparations post-World War I and protectionism may have triggered the Great Depression.`

### Assessment

- Great Depression remained strong on groundedness and claim count.
- Specificity is mixed:
  - better on trade mechanism naming via Smoot-Hawley
  - weaker on confidence and naturalness because the third claim becomes more speculative (`may have triggered`)
- Evidence pool quality is acceptable but still noisy in places (`ThoughtCo`, `Social Studies`, parallels article).
- Net result: broadly acceptable and comparable to frozen `004`, but not clearly better overall.

## Run C: Dot-Com Crash

### Before / After vs `v0_tier1_eval_set_004`

- Plan quality: slightly improved. The plan shifted from `technological over-saturation` to `speculation and hype`, which is more directly tied to the dot-com bubble.
- Evidence count: unchanged at `12`.
- Evidence utilization: improved from `0.25` to `0.3333`.
- Groundedness: unchanged at `1.0`.
- Claim count: unchanged at `3`.
- Verification: unchanged at `supported=3`.
- Plan coverage: unchanged at `1.0`.

### Technology / Speculation Step

`v0_004`

- step: `Analyze the role of technological over-saturation in the crash`
- query: `Analyze the role of technological over-saturation in the crash about What were the main causes of the dot-com crash?`

`v1_001`

- step: `Analyze the role of speculation and hype in the dot-com bubble`
- query: `Analyze the role of speculation and hype in the dot-com bubble`

### Surviving Evidence Titles By Step

`v1_001`

- timeline:
  - `Dot-com Bubble & Bust | Definition, History, & Facts | Britannica Money`
  - `Dotcom Bubble - Overview, Characteristics, Causes`
  - `Dot-com bubble | Economics | Research Starters - EBSCO`
- economic factors:
  - `The Dot Com Crash: Causes and Consequences - Eccuity`
  - `Dotcom Bubble - Overview, Characteristics, Causes`
  - `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`
- speculation/hype:
  - `Dotcom Bubble - Overview, Characteristics, Causes`
  - `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`
  - `The dot-com Bubble - EconPort.org`
- regulation:
  - `The Dot Com Crash: Causes and Consequences - Eccuity`
  - `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`
  - `Impact of the Dot-Com Bubble Burst - LinkedIn`

### Claims

`v0_004`

- `Overvaluation of tech companies was a cause of the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com bubble.`

`v1_001`

- `Overvaluation of tech companies contributed to the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com bubble and subsequent crash.`

### Assessment

- Dot-com remained clean.
- The old wrong-domain car-crash / vehicle-safety / distractive-driving noise did not return.
- The plan is arguably better targeted than frozen `004`.
- Claim specificity improved slightly in the speculation claim.
- Net result: this is a real improvement over frozen `004`.

## Aggregate Comparison

### Did v1-minimal maintain the 2008 improvements from `v1_2008_probe_012`?

No.

The full-set 2008 run regressed materially relative to the focused `012` probe:

- `groundedness: 1.0 -> 0.5`
- `claim count: 3 -> 2`
- the sharper OTC-derivatives claim disappeared
- the broad same-family umbrella deregulation claim returned
- the securitization claim became over-specific and insufficient again

### Did dot-com remain clean?

Yes.

- the old wrong-domain crash/vehicle noise did not return
- the plan stayed anchored to dot-com mechanisms
- evidence utilization improved
- final claims stayed on-question and grounded

### Did Great Depression remain strong?

Mostly yes.

- groundedness stayed at `1.0`
- claim count stayed at `3`
- specificity was mixed but acceptable
- no major regression appeared, though the third claim became more speculative

### Did groundedness remain acceptable across all 3?

No.

- 2008 financial crisis: `0.5`
- Great Depression: `1.0`
- dot-com crash: `1.0`

The aggregate v1-minimal set does not meet the bar for a stronger overall live
baseline because the 2008 run regressed too much.

### Did claim specificity improve overall versus frozen v0?

Mixed.

- 2008: cleaner in phrasing shape, but worse overall because support and claim count regressed
- Great Depression: mixed, with one clearer tariff/trade claim and one more speculative claim
- dot-com: improved modestly

So claim specificity improved in some slices, but not strongly enough overall
to offset the 2008 regression.

## Conclusion

### Is `v1_tier1_eval_set_001` strong enough to treat as the first live v1-minimal baseline?

Not yet.

`v1_tier1_eval_set_001` is a valuable comparison record and it confirms that:

- dot-com benefits from the v1-minimal path
- Great Depression stays broadly acceptable

But it does not yet beat frozen `v0_tier1_eval_set_004` as an overall live
baseline because the 2008 run is not stable enough in the full-set setting.
