# v1 Tier 1 Eval Set 003

## Scope

Third full 3-question live Tier 1 evaluation set for v1-minimal after:

- the focused 2008 recovery in `v1_2008_probe_014`
- the focused dot-com completeness recovery in `v1_dotcom_probe_014`

This step tests whether those focused gains hold together in a full live
evaluation without unacceptable regressions on the third question.

Frozen v0 remains the reference baseline:

- `experiments/notes/v0_tier1_eval_set_004.md`

The latest full v1 comparison record remains:

- `experiments/notes/v1_tier1_eval_set_002.md`

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
  --output-dir experiments/runs/v1_tier1_eval_set_003/financial_crisis_2008
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
  --output-dir experiments/runs/v1_tier1_eval_set_003/great_depression
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
  --output-dir experiments/runs/v1_tier1_eval_set_003/dot_com_crash
```

## New Artifact Paths

### Run A: 2008 Financial Crisis

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/financial_crisis_2008/20260319T220235Z_what-were-the-main-causes-of-the-2008-fi_experiment_a7e4c7c20b49/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/financial_crisis_2008/20260319T220235Z_what-were-the-main-causes-of-the-2008-fi_experiment_a7e4c7c20b49/experiment.json`

### Run B: Great Depression

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/great_depression/20260319T220241Z_what-were-the-main-causes-of-the-great-d_experiment_2d6200ca0f65/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/great_depression/20260319T220241Z_what-were-the-main-causes-of-the-great-d_experiment_2d6200ca0f65/experiment.json`

### Run C: Dot-Com Crash

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/dot_com_crash/20260319T220231Z_what-were-the-main-causes-of-the-dot-com_experiment_c1cd9db1d9e2/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_tier1_eval_set_003/dot_com_crash/20260319T220231Z_what-were-the-main-causes-of-the-dot-com_experiment_c1cd9db1d9e2/experiment.json`

## Comparison Targets

- frozen v0 baseline: `v0_tier1_eval_set_004`
- latest full v1 comparison record: `v1_tier1_eval_set_002`
- focused 2008 recovery probe: `v1_2008_probe_014`
- focused dot-com completeness probe: `v1_dotcom_probe_014`

## Run A: 2008 Financial Crisis

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_002`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count:
  - matched frozen `004`: `8`
  - improved over `v1_002`: `7 -> 8`
- Evidence utilization:
  - regressed versus both frozen `004` and `v1_002`: `0.375 / 0.4286 -> 0.25`
- Groundedness:
  - improved versus `v1_002`: `0.6667 -> 1.0`
  - matched frozen `004`: `1.0`
- Claim count:
  - regressed versus both frozen `004` and `v1_002`: `3 -> 2`
- Verification:
  - improved versus `v1_002`: `supported=2, insufficient=1 -> supported=2`
  - still worse than frozen `004`: `supported=3`
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_003`

- key events:
  - `The 2008 Financial Crisis Explained - Investopedia`
  - `Financial Crisis and Recovery: Financial Crisis Timeline`
  - `The U.S. Financial Crisis | Council on Foreign Relations`
- deregulation:
  - `In what ways did deregulation help create the 2008 ...`
  - `[PDF] Foreword: Deregulation: A Major Cause of the Financial Crisis`
  - `Lesson 8: Deregulation and the 2008 Financial Crisis`
- securitization:
  - `Securitization of Financial Instruments: Mechanisms, Benefits, and ...`
  - `The Role of Securitization in Bank Liquidity and Financial Stability`

### Claims

`v1_003`

- `The securitization of financial instruments contributed to the 2008 financial crisis.`
- `Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.`

### Assessment

- The focused `v1_2008_probe_014` recovery did not hold in the full set.
- Groundedness recovered to `1.0`, which is better than `v1_002`.
- But claim count collapsed back to `2`, losing the healthier 3-mechanism coverage from the focused probe.
- Net result: support quality improved relative to `v1_002`, but 2008 full-set stability is still not solved.

## Run B: Great Depression

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_002`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count:
  - regressed versus both frozen `004` and `v1_002`: `12 / 10 -> 12`
- Evidence utilization:
  - regressed versus both frozen `004` and `v1_002`: `0.25 / 0.4 -> 0.1667`
- Groundedness: unchanged at `1.0`.
- Claim count:
  - regressed versus both frozen `004` and `v1_002`: `3 -> 2`
- Verification:
  - regressed versus both frozen `004` and `v1_002`: `supported=3 -> supported=2`
- Plan coverage: unchanged at `1.0`.

### Surviving Evidence Titles By Step

`v1_003`

- primary-source step:
  - `Great Depression 1929-1939 - Primary Resources`
  - `Great Depression & New Deal - Primary Sources: America (U.S.A. ...`
  - `Primary Sources: The Great Depression and the 1930s: Economics`
- categorization step:
  - `Political Causes of the Great Depression - ThoughtCo`
  - `5 Causes of the Great Depression - History.com`
  - `The Great Depression: Overview, Causes, and Effects - Investopedia`
- scholarly step:
  - `Causes of the Great Depression | Britannica`
  - `[PDF] What Caused the Great Depression? - Social Studies`
  - `Causes of the Great Depression – Alex J. Pollock - Law & Liberty`
- synthesis step:
  - `What caused the Great Depression? What are its economic effects?`
  - `5 Causes of the Great Depression - History.com`
  - `Causes of the Great Depression - Wikipedia`

### Claims

`v1_003`

- `Banking panics and monetary policies contributed to the Great Depression.`
- `War reparations and protectionism triggered the Great Depression.`

### Assessment

- Great Depression did not stay as strong as `v1_002`.
- It remained grounded and on-question, but the answer became shorter, less complete, and less useful.
- Net result: acceptable but regressed.

## Run C: Dot-Com Crash

### Before / After vs `v0_tier1_eval_set_004` and `v1_tier1_eval_set_002`

- Plan quality:
  - improved versus `v1_002` only in final answer completeness, not in step phrasing
  - step wording still used `technological over-saturation`, matching frozen `004`
- Evidence count: unchanged at `12`.
- Evidence utilization:
  - improved over both frozen `004` and `v1_002`: `0.25 -> 0.3333`
- Groundedness: unchanged at `1.0`.
- Claim count:
  - improved versus `v1_002`: `2 -> 3`
  - matched frozen `004`: `3`
- Verification: `supported=3`, matching frozen `004`.
- Plan coverage: unchanged at `1.0`.

### Technology Step

`v1_003`

- step: `Analyze the role of technological over-saturation in the crash`

Surviving technology-step titles:

- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`

Assessment:

- the old wrong-domain crash/vehicle noise did not return
- retrieval stayed dot-com aligned
- the focused `v1_dotcom_probe_014` completeness gain held here

### Claims

`v1_003`

- `Overvaluation of tech companies contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the stock market bubble.`
- `The lack of regulation in the tech industry contributed to the dot-com crash.`

### Assessment

- Dot-com is the strongest run in `v1_003`.
- The missing third mechanism stayed present.
- The old wrong-domain retrieval failure remained fixed.
- There is still mild phrasing drift in the plan step, but the final claims are more explicit than the focused `v1_dotcom_probe_014` wording.
- Net result: clear improvement over `v1_002` and competitive with frozen `004`.

## Aggregate Comparison

### Did v1-minimal maintain the 2008 recovery from `v1_2008_probe_014`?

No.

`v1_003` matched the focused probe on groundedness, but not on completeness:

- groundedness held at `1.0`
- claim count regressed from `3` to `2`
- the broader regulation/supervision + subprime mix from `014` did not hold

### Did dot-com maintain the completeness gains from `v1_dotcom_probe_014`?

Yes.

- claim count stayed at `3`
- groundedness stayed `1.0`
- regulation returned and stayed present
- wrong-domain crash/vehicle noise stayed gone

### Did Great Depression remain acceptable?

Barely, but weaker than before.

- groundedness stayed `1.0`
- but claim count dropped to `2`
- evidence utilization dropped sharply
- answer usefulness regressed

### Did groundedness remain acceptable across all 3?

Yes.

All 3 runs kept `groundedness=1.0`.

### Did claim specificity improve overall versus frozen v0?

No, not overall.

- 2008 phrasing is cleaner than frozen v0, but the answer is less complete
- Great Depression is less complete than frozen v0
- dot-com is competitive and cleaner

### Is `v1_tier1_eval_set_003` strong enough to become the active experimental baseline for v1-minimal?

No.

It is a useful comparison record and it improves materially over `v1_tier1_eval_set_002`
on dot-com and 2008 groundedness, but it still does not beat frozen `v0_tier1_eval_set_004`
overall because:

- 2008 full-set stability is still not robust enough
- Great Depression regressed materially in completeness

## Overall Judgment

`v1_tier1_eval_set_003` is mixed:

- 2008: groundedness improved, but claim count collapsed
- Great Depression: still grounded, but weaker and less complete
- dot-com: clearly stronger and now stable on the main failure mode

So this run is better than `v1_tier1_eval_set_002` in some important ways, but
still not strong enough to replace frozen `004` as the benchmark to judge
against.
