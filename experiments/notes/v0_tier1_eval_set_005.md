# v0 Tier 1 Eval Set 005

## Scope

Rerun of the same 3-question live Tier 1 evaluation set after the narrow synthesis-quality hardening pass, compared against:

- `v0_tier1_eval_set_004` as the current reference live baseline
- `v0_dotcom_probe_005` as the focused confirmation of the dot-com retrieval fix
- `v0_2008_probe_006` as the focused confirmation of the 2008 synthesis-quality fix

Constraints preserved:

- Frozen v0 architecture unchanged
- No Phase 2 features introduced
- Same live provider path used across all runs
- Goal: determine whether the focused dot-com retrieval and 2008 synthesis improvements hold together in the full 3-question set without unacceptable regressions

## Questions

1. `What were the main causes of the 2008 financial crisis?`
2. `What were the main causes of the Great Depression?`
3. `What were the main causes of the dot-com crash?`

## Provider Configuration

- `ASAR_MODEL_PROVIDER=openai`
- `ASAR_MODEL_MODEL=llama3.1:8b`
- `ASAR_OPENAI_BASE_URL=https://inference.ccrolabs.com/v1`
- `ASAR_SEARCH_PROVIDER=tavily`

Secrets were supplied via `.secrets` at runtime and are intentionally omitted here.

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
  --output-dir experiments/runs/v0_tier1_eval_set_005/financial_crisis_2008
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
  --output-dir experiments/runs/v0_tier1_eval_set_005/great_depression
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
  --output-dir experiments/runs/v0_tier1_eval_set_005/dot_com_crash
```

## New Artifact Paths

### Run A: 2008 Financial Crisis

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/financial_crisis_2008/20260318T233148Z_what-were-the-main-causes-of-the-2008-fi_experiment_124fd3a669e8/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/financial_crisis_2008/20260318T233148Z_what-were-the-main-causes-of-the-2008-fi_experiment_124fd3a669e8/experiment.json`

### Run B: Great Depression

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/great_depression/20260318T233144Z_what-were-the-main-causes-of-the-great-d_experiment_b4810296f44b/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/great_depression/20260318T233144Z_what-were-the-main-causes-of-the-great-d_experiment_b4810296f44b/experiment.json`

### Run C: Dot-Com Crash

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/dot_com_crash/20260318T233153Z_what-were-the-main-causes-of-the-dot-com_experiment_f15fb7fe110e/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_005/dot_com_crash/20260318T233153Z_what-were-the-main-causes-of-the-dot-com_experiment_f15fb7fe110e/experiment.json`

## Comparison Targets

- Reference baseline: `v0_tier1_eval_set_004`
- Focused dot-com probe: `v0_dotcom_probe_005`
- Focused 2008 probe: `v0_2008_probe_006`

## Run A: 2008 Financial Crisis

### Before / After vs `004` and `006`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count: improved from `8` in `004` to `7`.
- Evidence utilization: improved from `0.375` in `004` to `0.4286`, but stayed below the focused `006` probe (`0.5`).
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Surviving Evidence Titles By Step

`005`
- key events: `Timeline: Key events in financial crisis - USA Today`, `The 2008 Financial Crisis Explained - Investopedia`, `Financial Crisis and Recovery: Financial Crisis Timeline`
- deregulation: `Foreword: Deregulation: A Major Cause of the Financial Crisis`, `Did Deregulation Cause the Financial Crisis?`, `DEREGULATION AND THE 2008 FINANCIAL CRISIS IN ...`
- securitization: `The Role of Securitization in Bank Liquidity and Financial Stability`

### Claims

`005`
- `The deregulated OTC derivatives market posed dangers to the financial system.`
- `Securitization provided an additional funding source, potentially eliminating assets from banks' balance sheets.`
- `The repeal of Glass-Steagall contributed to the financial crisis.`

### Assessment

- The focused synthesis win from `006` did not generalize cleanly.
- Copied/snippet-like phrasing was reduced relative to `004`, but one securitization claim is still essentially lifted from evidence wording.
- Only one claim is framed as a clean direct causal answer.
- This is better than `004` on evidence efficiency, but not better than `006` on answer quality.
- Net result: mixed. The targeted 2008 synthesis improvement did not hold reliably in the full rerun.

## Run B: Great Depression

### Before / After vs `004`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: unchanged at `12`.
- Evidence utilization: improved from `0.25` to `0.4167`.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Surviving Evidence Titles By Step

`005`
- primary-source step: `Primary Sources: The Great Depression and the 1930s`, `Great Depression 1929-1939 - Primary Resources`, `Great Depression & New Deal - Primary Sources`
- categorization step: `5 Causes of the Great Depression`, `Top 5 Causes of the Great Depression`, `Causes of the Great Depression`
- scholarly step: `High School History Textbooks and the Causes of the Great ...`, `Causes of the Great Depression – Alex J. Pollock - Law & Liberty`, `Financial factors and the propagation of the Great Depression`
- synthesis step: `5 Causes of the Great Depression - History.com`, `Causes of the Great Depression - Wikipedia`, `Causes of the Great Depression.pdf - Course Hero`

### Claims

`005`
- `The stock market crash of 1929 contributed to the start of the Great Depression.`
- `Bank failures and a collapse in confidence were main causes of the Great Depression.`
- `Forward-looking financial factors contributed to the propagation of the Great Depression.`

### Assessment

- This run is stronger than `004` on evidence utilization and still fully grounded.
- Claim phrasing is more compact, though the third claim is more academic/jargon-heavy than ideal.
- Evidence quality remains imperfect: `Wikipedia` and `Course Hero` still survive in the synthesis step.
- Net result: improved overall, with acceptable but not especially elegant final phrasing.

## Run C: Dot-Com Crash

### Before / After vs `004` and `v0_dotcom_probe_005`

- Plan quality: remained good, but with planner variance in step 3.
- Evidence count: unchanged from `004` at `12`, slightly higher than the focused probe (`11`).
- Evidence utilization: unchanged from `004` at `0.25`, slightly lower than the focused probe (`0.2727`).
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Planner / Query Behavior

`004` step 3:
- `Analyze the role of technological over-saturation in the crash`

`005` step 3:
- `Analyze the role of speculation and hype in the dot-com bubble`

This is acceptable v0 planner variance, not a regression. The new step stayed properly anchored to the dot-com domain.

### Key Surviving Evidence

`005`
- economic step: `The Dot Com Crash: Causes and Consequences - Eccuity`, `Dotcom Bubble - Overview, Characteristics, Causes`, `Surviving the next DotCom Stock Market Crash in 2026 - YouTube`
- speculation/hype step: `The Dot.com bubble (docx) - CliffsNotes`, `Dotcom Bubble - Overview, Characteristics, Causes`, `From Hype to Bust: Investigating the Underlying Factors of the Dot ...`
- regulatory step: `The Dot Com Crash: Causes and Consequences - Eccuity`, `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`, `Impact of the Dot-Com Bubble Burst - LinkedIn`

### Claims

`005`
- `Overvaluation of tech companies contributed to the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in tech companies caused the dot-com bubble.`

### Assessment

- The targeted dot-com retrieval failure remained fixed.
- The car-crash / vehicle-safety / distractive-driving / intersection-style noise from `003` did not return.
- This agrees with the focused `v0_dotcom_probe_005` result on the main failure mode.
- Residual provider/search noise still exists in other forms, especially `YouTube` and `CliffsNotes`, but the specific wrong-domain technology-step failure is gone.
- Net result: the dot-com improvement generalized successfully.

## Aggregate Comparison

### Did The Synthesis Hardening Generalize Beyond The Focused 2008 Probe?

Not reliably.

- The focused `006` probe showed a clear 2008 improvement.
- In the full `005` rerun, 2008 evidence efficiency improved, but the claim phrasing did not stay as direct or clean as in `006`.
- This looks like acceptable v0 synthesis variance, not a hard regression in architecture, but it means the improvement is not yet robust enough to call solved.

### Did Dot-Com Stay Clean?

Yes.

- The prior wrong-domain traffic-safety retrieval failure did not return.
- The dot-com plan stayed domain-anchored even with minor planner wording changes.
- This matches the focused confirmation from `v0_dotcom_probe_005`.

### Did Evidence Utilization Improve Or Remain Acceptable?

Improved overall.

- 2008 financial crisis: `0.375 -> 0.4286`
- Great Depression: `0.25 -> 0.4167`
- Dot-com crash: `0.25 -> 0.25`

The main retrieval/evidence discipline remained acceptable, and average utilization improved versus `004`.

### Did Claim Specificity Improve Overall?

Mixed.

- 2008 financial crisis: mixed to weak; still not a clean direct-causal answer set
- Great Depression: acceptable, though one claim became jargon-heavy
- Dot-com crash: stable to slightly improved, and fully on-question

Overall specificity did not clearly improve enough to declare a new best baseline.

### Did Groundedness Stay Acceptable?

Yes.

- 2008 financial crisis: `1.0`
- Great Depression: `1.0`
- Dot-com crash: `1.0`

### Is `005` Better Than `004` Overall?

Not clearly enough.

Why `005` is stronger in some ways:
- dot-com stayed clean on the exact targeted failure mode
- Great Depression improved on evidence utilization while staying fully grounded
- overall evidence utilization improved

Why `005` is not a clean replacement:
- the focused 2008 synthesis improvement from `006` did not generalize in the full set
- 2008 remains the weakest run and still contains descriptively grounded but not crisp causal claims
- some provider/search noise remains in dot-com (`YouTube`, `CliffsNotes`) and Great Depression (`Course Hero`, `Wikipedia`)

## Overall Assessment

`v0_tier1_eval_set_005` is a useful comparison record and shows that the dot-com retrieval fix generalized, but it does not clearly surpass `004` as the best overall live reference set. The strongest reason is that the main targeted synthesis win on 2008 did not hold cleanly in the full rerun.

This means:

- the dot-com retrieval improvement is now stable enough to trust
- retrieval/evidence quality remains acceptable for frozen v0
- synthesis quality, especially on 2008-style causal answers, is still the main unstable bottleneck

## Conclusion

`v0_tier1_eval_set_005` should **not** replace `v0_tier1_eval_set_004` as the reference live baseline.

Reason:

- dot-com stayed fixed, but that was already established by `004` plus the focused probe
- Great Depression improved, but not enough to outweigh the unresolved 2008 synthesis inconsistency
- `004` remains the stronger reference point for baseline stability

Caveat:

- keep `005` as the comparison artifact that shows the dot-com fix generalized while 2008 synthesis quality remained variable
