# v0 Tier 1 Eval Set 004

## Reference Status

This is the current reference live baseline for frozen v0.

## Scope

Rerun of the same 3-question live Tier 1 evaluation set after the narrow domain-anchor hardening pass.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used across all runs
- Goal: determine whether the domain-anchor fix generalizes beyond the focused dot-com probe without unacceptable regressions

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
  --output-dir experiments/runs/v0_tier1_eval_set_004/financial_crisis_2008
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
  --output-dir experiments/runs/v0_tier1_eval_set_004/great_depression
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
  --output-dir experiments/runs/v0_tier1_eval_set_004/dot_com_crash
```

## New Artifact Paths

### Run A: 2008 Financial Crisis

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/financial_crisis_2008/20260318T225511Z_what-were-the-main-causes-of-the-2008-fi_experiment_5831dc41eeb9/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/financial_crisis_2008/20260318T225511Z_what-were-the-main-causes-of-the-2008-fi_experiment_5831dc41eeb9/experiment.json`

### Run B: Great Depression

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/great_depression/20260318T230332Z_what-were-the-main-causes-of-the-great-d_experiment_5ca15859f04c/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/great_depression/20260318T230332Z_what-were-the-main-causes-of-the-great-d_experiment_5ca15859f04c/experiment.json`

### Run C: Dot-Com Crash

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/dot_com_crash/20260318T231031Z_what-were-the-main-causes-of-the-dot-com_experiment_948742386749/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_004/dot_com_crash/20260318T231031Z_what-were-the-main-causes-of-the-dot-com_experiment_948742386749/experiment.json`

## Comparison Targets

- Reference baseline: `v0_tier1_eval_set_002`
- Comparison record: `v0_tier1_eval_set_003`
- Focused confirmation for dot-com: `v0_dotcom_probe_005`

## Run A: 2008 Financial Crisis

### Before / After vs `002` and `003`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count: improved from `9` / `9` to `8`.
- Evidence utilization: improved from `0.3333` / `0.3333` to `0.375`.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Surviving Evidence Titles By Step

`004`
- key events: `2008 financial crisis - Wikipedia`, `Financial Crisis and Recovery: Financial Crisis Timeline`, `Understanding History: A Review of the 2008 Financial Crisis`
- deregulation: `Foreword: Deregulation: A Major Cause of the Financial Crisis`, `Did Deregulation Cause the Financial Crisis? - Mercatus Center`, `DEREGULATION AND THE 2008 FINANCIAL CRISIS IN AMERICA`
- securitization: `Securitization of Financial Instruments: Mechanisms, Benefits, and ...`, `The Role of Securitization in Bank Liquidity and Financial Stability`

### Claims

`004`
- `Securitization is more than just a capital markets innovation—it’s a multifaceted process that bridges the gap between lending institutions and investors seeking income-generating assets.`
- `The securitization of loans into securities provides an additional funding source and potentially eliminates assets from banks' balance sheets.`
- `The deregulation of the OTC derivatives market contributed to the 2008 financial crisis.`

### Assessment

- Evidence pool discipline improved slightly.
- Evidence titles remain broadly relevant.
- Claim specificity regressed.
- Two securitization claims are descriptive/mechanical rather than clean direct causes.
- Net result: mild retrieval improvement, but weaker answer quality than `002`.

## Run B: Great Depression

### Before / After vs `002` and `003`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: unchanged from `12`, but higher than `003` (`10`).
- Evidence utilization: regressed from `0.3333` in `002`, but improved from `0.1` in `003`, landing at `0.25`.
- Groundedness: improved from `0.6667` in `002` and stayed equal to `003` at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: improved over `002` to `supported=3`, matching `003`.

### Surviving Evidence Titles By Step

`004`
- primary-source step: `Primary Sources: The Great Depression and the 1930s`, `Great Depression 1929-1939 - Primary Resources`, `Great Depression & New Deal - Primary Sources`
- categorization step: `5 Causes of the Great Depression`, `Top 5 Causes of the Great Depression`, `Causes of the Great Depression`
- scholarly step: `High School History Textbooks and the Causes of the Great ...`, `Causes of the Great Depression – Alex J. Pollock`, `Financial factors and the propagation of the Great Depression`
- synthesis step: `5 Causes of the Great Depression - History.com`, `Causes of the Great Depression - Wikipedia`, `Causes of the Great Depression.pdf - Course Hero`

### Claims

`004`
- `The stock market crash of 1929 triggered the Great Depression.`
- `Bank failures and reduced consumer spending contributed to the Great Depression.`
- `A collapse in confidence, tariffs reducing trade, and a gold standard contributed to the Great Depression.`

### Assessment

- The final claim set is on-question and more useful than `002`.
- It avoids the `003` evidence-utilization collapse onto one source.
- Some evidence titles are still noisy or weak, especially `Course Hero` and the oversized Wikipedia fragment.
- Net result: better overall than both `002` and `003`, though not perfectly clean.

## Run C: Dot-Com Crash

### Before / After vs `002`, `003`, and `005`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: unchanged from `12` in `002` and `003`, slightly higher than `005` (`11`).
- Evidence utilization: unchanged from `002` at `0.25`, lower than `003` (`0.3333`) and `005` (`0.2727`).
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Technology Step Query

`004`
- `Analyze the role of technological over-saturation in the crash about What were the main causes of the dot-com crash?`

Comparison:
- This matches the anchored pattern from `v0_dotcom_probe_005`.
- The technology step remained properly anchored to the dot-com goal.

### Technology Step Survivors

`002`
- `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
- `Characterizing Technology's Influence on Distractive Behavior at ...`
- `How Technological Advancements are Reshaping Accident ...`

`003`
- `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
- `Characterizing Technology's Influence on Distractive Behavior at ...`
- `Exploring the mechanism of crashes with automated vehicles ...`

`005`
- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`

`004`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`

### Claims

`004`
- `Overvaluation of tech companies was a cause of the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com bubble.`

### Assessment

- The domain-anchor hardening clearly generalized here.
- The wrong-domain car-crash / vehicle-safety / distractive-driving / intersection-style noise did not return.
- Claim quality is cleaner than `002` and `003`, and close in shape to the focused `005` probe.
- Net result: this is the strongest dot-com run so far in the live Tier 1 set.

## Aggregate Comparison

### Did The Domain-Anchor Hardening Generalize Beyond The Focused Dot-Com Probe?

Partially yes.

- Strong direct generalization on dot-com: the targeted retrieval failure stayed fixed in the full set.
- No strong retrieval regression appeared on the other two questions.
- The change did not create a broad answer-quality jump everywhere, but it did carry the dot-com fix into the full live evaluation.

### Did Dot-Com Stay Clean?

Yes.

- The technology step stayed goal-anchored.
- The prior wrong-domain traffic-safety noise did not reappear.
- This matches the focused confirmation from `v0_dotcom_probe_005`.

### Did Evidence Utilization Improve Or Regress Overall?

Mixed, slightly regressed overall versus `002`.

- 2008 financial crisis: `0.3333 -> 0.375`
- Great Depression: `0.3333 -> 0.25`
- Dot-com crash: `0.25 -> 0.25`

The dot-com retrieval fix did not translate into a broad utilization gain across all three questions.

### Did Claim Specificity Improve Or Remain Acceptable?

Mixed.

- 2008 financial crisis: regressed; still the weakest run in the set
- Great Depression: remained acceptable and broadly useful
- Dot-com crash: improved materially over `002` and `003`

### Did Groundedness Stay Acceptable?

Yes.

- 2008 financial crisis: `1.0`
- Great Depression: `1.0`
- Dot-com crash: `1.0`

This is better than `002` overall on groundedness because Great Depression improved from `0.6667` to `1.0`.

### Is `004` Better Than `002` Overall?

Yes, but with a notable caveat.

Why `004` is better overall:
- dot-com stayed clean and is clearly better than the `002` and `003` dot-com runs
- Great Depression improved on groundedness and verification while staying on-question
- all three runs now have `groundedness=1.0`
- no obvious off-topic retrieval regression appeared

Why the win is not clean:
- 2008 claim formulation is weaker than `002`
- overall evidence utilization did not improve uniformly
- synthesis variance remains visible

## Overall Assessment

`v0_tier1_eval_set_004` is the best overall live reference set so far, but mostly because it preserves the dot-com retrieval fix and lifts Great Depression to a cleaner fully-supported result. The main caution is that the 2008 run remains noticeably weak on claim formulation, even though its metrics look healthy.

This means:
- the execution/orchestration hardening did its intended job on dot-com
- the full live baseline improved in a meaningful way
- the next visible bottleneck is still synthesis quality, not retrieval cleanliness

## Conclusion

`v0_tier1_eval_set_004` should replace `v0_tier1_eval_set_002` as the reference live baseline.

Reason:
- dot-com is now clean in the exact place where `002` and `003` were failing
- Great Depression remains strong
- groundedness is uniformly acceptable across all three runs

Caveat:
- keep the 2008 run in mind as the primary remaining quality weakness when evaluating future v0 changes
