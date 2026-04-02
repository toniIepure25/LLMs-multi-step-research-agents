# v0 Tier 1 Eval Set 003

## Scope

Rerun of the same 3-question live Tier 1 evaluation set after the execution-side lexical relevance hardening pass.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used across all runs
- Goal: compare the execution-hardened v0 pipeline against `v0_tier1_eval_set_002`

## Questions

1. `What were the main causes of the 2008 financial crisis?`
2. `What were the main causes of the Great Depression?`
3. `What were the main causes of the dot-com crash?`

## Provider Configuration

- `ASAR_MODEL_PROVIDER=openai`
- `ASAR_MODEL_MODEL=llama3.1:8b`
- `ASAR_OPENAI_BASE_URL=https://inference.ccrolabs.com/v1`
- `ASAR_SEARCH_PROVIDER=tavily`

Secrets were supplied via environment variables at runtime and are intentionally omitted here.

## Run A: 2008 Financial Crisis

### Question

`What were the main causes of the 2008 financial crisis?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/financial_crisis_2008/20260318T211718Z_what-were-the-main-causes-of-the-2008-fi_experiment_12632615bbe6/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/financial_crisis_2008/20260318T211718Z_what-were-the-main-causes-of-the-2008-fi_experiment_12632615bbe6/experiment.json`

### Before / After vs `002`

- Plan quality: unchanged. The same 3-step plan was generated.
- Evidence count: unchanged at `9`.
- Evidence utilization: unchanged at `0.3333`.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Surviving Evidence Titles By Step

`002`
- key events: `[PDF] The Global Economic & Financial Crisis: A Timeline`, `2008 financial crisis - Wikipedia`, `Financial Crisis and Recovery: Financial Crisis Timeline`
- deregulation: `Did Deregulation Cause the Financial Crisis?`, `Foreword: Deregulation: A Major Cause of the Financial Crisis`, `Financial Engineering and Deregulation: The biggest causes of ...`
- securitization: `Securitization and financial markets...`, `The Role of Securitization in Bank Liquidity and Financial Stability`, `Mechanics and Benefits of Securitization`

`003`
- key events: `[PDF] The Global Economic & Financial Crisis: A Timeline`, `The 2008 Financial Crisis Explained - Investopedia`, `Financial crisis: timeline - The Guardian`
- deregulation: `Did Deregulation Cause the Financial Crisis?`, `Foreword: Deregulation: A Major Cause of the Financial Crisis`, `Rolling the rock: The cycle of deregulation, crisis and regulation`
- securitization: `Securitization of Financial Instruments: Mechanisms, Benefits, and ...`, `The Role of Securitization in Bank Liquidity and Financial Stability`, `Mechanics and Benefits of Securitization`

### Claims

`002`
- `The primary benefit of securitization is to reduce funding costs.`
- `A liquidity crisis spread to global institutions by mid-2007 and climaxed with the bankruptcy of Lehman Brothers in September 2008.`
- `Deregulation of the financial services sector in the years leading up to the 2008 crisis was—and continues to be—a major cause of the financial crisis.`

`003`
- `The primary benefit of securitization is to reduce funding costs.`
- `Deregulation of the financial services sector in the years leading up to the 2008 crisis was—and continues to be—a major cause of the financial crisis.`
- `The securitization of illiquid assets such as loans allows institutions like banks, mortgage lenders, and corporations to convert these assets into liquid securities.`

### Assessment

- The surviving evidence titles are slightly cleaner, especially in the timeline step.
- The answer remains broadly on-question.
- Claim quality did not materially improve.
- One timeline/context claim disappeared, but it was replaced by another descriptive securitization-mechanics claim rather than a cleaner direct cause.
- Net result: mild evidence-title improvement, but no meaningful answer-quality gain.

## Run B: Great Depression

### Question

`What were the main causes of the Great Depression?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/great_depression/20260318T211749Z_what-were-the-main-causes-of-the-great-d_experiment_e2b45ac8bad1/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/great_depression/20260318T211749Z_what-were-the-main-causes-of-the-great-d_experiment_e2b45ac8bad1/experiment.json`

### Before / After vs `002`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: improved from `12` to `10`.
- Evidence utilization: regressed from `0.3333` to `0.1`.
- Groundedness: improved from `0.6667` to `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: improved from `supported=2, insufficient=1` to `supported=3`.

### Surviving Evidence Titles By Step

`002`
- categorize causes: `The Under-Registration of Births in Mexico`, `EU AI Act: Prohibited and high-risk systems in employment`, `Nature on the brink...`
- scholarly step: `The Depression of 2026`, `Causes of the Great Depression – Alex J. Pollock`, `High School History Textbooks and the Causes of the Great ...`
- synthesis step: `The Depression of 2026`, `Causes of the Great Depression - Wikipedia`, `Great Depression - Wikipedia`

`003`
- categorize causes: `economic-support-specialist-1-00161586 | Job Details tab`
- scholarly step: `High School History Textbooks and the Causes of ...`, `Financial factors and the propagation of the Great ...`, `Causes of the Great Depression – Alex J. Pollock`
- synthesis step: `Causes of the Great Depression - Wikipedia`, `What caused the Great Depression? What are its economic effects?`, `5 Causes of the Great Depression - History.com`

### Claims

`002`
- `The stock market crash of 1929 triggered the Great Depression.`
- `Monetary policy mistakes by the Federal Reserve contributed to the Great Depression.`
- `Overproduction and underconsumption led to a surplus of goods, which contributed to the Great Depression.`

`003`
- `The stock market crash was a key cause of the Great Depression.`
- `Banking panic was another significant cause of the Great Depression.`
- `A decline in aggregate demand was also a major cause of the Great Depression.`

### Assessment

- This is the clearest evidence-title improvement in the set.
- Several obviously off-topic artifacts from `002` were removed.
- Claim specificity stayed good and groundedness improved to `1.0`.
- However, all 3 claims were supported by the same evidence item in the final output, which explains the sharp drop in `evidence_utilization`.
- Net result: better surviving evidence and better verification, but also a new evidence-utilization regression due claim consolidation onto one source.

## Run C: Dot-Com Crash

### Question

`What were the main causes of the dot-com crash?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/dot_com_crash/20260318T211815Z_what-were-the-main-causes-of-the-dot-com_experiment_af7cba51c1b5/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/dot_com_crash/20260318T211815Z_what-were-the-main-causes-of-the-dot-com_experiment_af7cba51c1b5/experiment.json`

### Before / After vs `002`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: unchanged at `12`.
- Evidence utilization: improved from `0.25` to `0.3333`.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Surviving Evidence Titles By Step

`002`
- technology over-saturation: `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`, `Characterizing Technology's Influence on Distractive Behavior...`, `How Technological Advancements are Reshaping Accident ...`
- regulatory failures: `How Regulatory Failures Led to the 2007-2008 Financial Crisis`, `The Great Depression as Regulatory Failure`, `Regulatory Failure - Examples`
- economic factors: `Quora`, `What Caused the Stock Market Crash of 1929?`, `Stock Market Crash: Causes, Impacts & How to Prepare`

`003`
- technology over-saturation: `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`, `Characterizing Technology's Influence on Distractive Behavior...`, `Exploring the mechanism of crashes with automated vehicles...`
- regulatory failures: `How Regulatory Failures Led to the 2007-2008 Financial Crisis`, `Regulatory Failure - Examples`, `Dangers of Regulatory Overreaction to the October 1987 Crash`
- economic factors: `What Causes the Economy to Crash?`, `A Brief History of Economic Crises, Crashes and Recoveries`, `What Is Economic Collapse?`

### Claims

`002`
- `Regulatory shortcomings exposed by the crisis included a lack of tools for supervisors to manage the financial system.`
- `Speculation in dot-com businesses caused a stock market bubble that led to the crash.`
- `Regulatory failures contributed to the crash by failing to stop or exacerbate financial crises.`

`003`
- `Speculation in dotcom or internet-based businesses from 1995 to 2000 caused the dotcom bubble.`
- `Regulatory failures contributed to the 2007-2008 global financial crisis, which was related to the dot-com crash.`
- `Artificially low interest rates distorted market signals and led to an unsustainable boom.`

### Assessment

- The execution-side filter did not materially reduce obviously off-topic search results here.
- The technology step still contains car-crash / vehicle-safety noise.
- One claim improved: the speculation claim is more specific.
- The regulatory claim remains off-target by drifting toward the 2007-2008 crisis.
- Net result: modest metric improvement, but the dot-com relevance problem was not actually solved.

## Aggregate Comparison

### Did Execution-Side Filtering Reduce Obviously Off-Topic Search Results?

Partially, but not consistently.

- 2008 financial crisis: slight improvement in surviving titles, but the difference was modest.
- Great Depression: yes, clearly improved. Several obvious junk titles from `002` were removed.
- Dot-com crash: no meaningful improvement. The most obvious noise still survived in the technology step.

### Did Evidence Utilization Improve Further?

Mixed.

- 2008 financial crisis: unchanged at `0.3333`
- Great Depression: regressed from `0.3333` to `0.1`
- Dot-com crash: improved from `0.25` to `0.3333`

There was no uniform evidence-utilization gain from this pass.

### Did Claim Specificity Improve Or Remain Stable?

Mixed.

- 2008 financial crisis: roughly stable, but still not cleanly causal
- Great Depression: remained good, with a better final claim set overall
- Dot-com crash: mixed, with one stronger claim and one still clearly off-target claim

### Did Groundedness Stay Acceptable?

Yes.

- 2008 financial crisis: `1.0 -> 1.0`
- Great Depression: `0.6667 -> 1.0`
- Dot-com crash: `1.0 -> 1.0`

Groundedness stayed acceptable across the entire set.

### Is `003` Better Than `002` Overall?

No, not clearly enough to replace it.

Why `003` is better in some ways:
- Great Depression evidence noise was reduced
- Great Depression groundedness improved
- Dot-com evidence utilization improved

Why `003` is not better overall:
- 2008 answer quality did not materially improve
- dot-com still retained obviously bad evidence in the technology step
- Great Depression evidence utilization regressed sharply because all claims leaned on one evidence item
- the gains are uneven and not yet strong enough to call this the new best live reference set

## Overall Assessment

The execution-side lexical filter helped in a narrow and real way, but only partially:

- it can remove some obvious junk when the query and goal share strong lexical anchors
- it did not robustly fix noisier cases like the dot-com crash technology step
- it did not create a clean overall improvement across the full 3-question set

This looks like a useful v0 hardening step, but not a decisive live-baseline upgrade.

## Conclusion

`v0_tier1_eval_set_003` is a mixed result. It contains real local improvements, especially on the Great Depression run, but it is not clearly better than `v0_tier1_eval_set_002` overall. `002` should remain the reference live baseline for now.
