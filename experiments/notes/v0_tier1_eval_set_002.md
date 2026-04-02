# v0 Tier 1 Eval Set 002

## Scope

Rerun of the same 3-question live Tier 1 evaluation set after the v0 quality-hardening change.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used across all runs
- Goal: compare the hardened v0 pipeline against `v0_tier1_eval_set_001`

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

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/financial_crisis_2008/20260318T202129Z_what-were-the-main-causes-of-the-2008-fi_experiment_bf032c89aa23/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/financial_crisis_2008/20260318T202129Z_what-were-the-main-causes-of-the-2008-fi_experiment_bf032c89aa23/experiment.json`

### Before / After vs `001`

- Plan quality: unchanged. The same 3-step causal plan was generated.
- Evidence count: improved from `15` to `9`.
- Evidence utilization: improved from `0.2667` to `0.3333`.
- Groundedness: improved from `0.6667` to `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: improved from `supported=2, insufficient=1` to `supported=3, insufficient=0`.

### Claims

`001`
- `Securitization played a significant role in the 2008 financial crisis.`
- `Deregulation of the financial services sector contributed to the 2008 financial crisis.`
- `The failure of securitization and deregulation to regulate the financial system led to the 2008 financial crisis.`

`002`
- `The primary benefit of securitization is to reduce funding costs.`
- `A liquidity crisis spread to global institutions by mid-2007 and climaxed with the bankruptcy of Lehman Brothers in September 2008.`
- `Deregulation of the financial services sector in the years leading up to the 2008 crisis was—and continues to be—a major cause of the financial crisis.`

### Assessment

- Evidence discipline improved materially.
- Question relevance stayed broadly on-topic, but claim specificity did not improve cleanly.
- The vague umbrella claim from `001` is gone, which is good.
- However, two `002` claims are weaker answer shapes:
  - the securitization claim states a financing benefit rather than a direct cause
  - the liquidity-crisis timeline claim is relevant context but not as cleanly causal as the question asks
- Net result: better grounding and tighter evidence pool, but mixed claim formulation quality.

## Run B: Great Depression

### Question

`What were the main causes of the Great Depression?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/great_depression/20260318T202957Z_what-were-the-main-causes-of-the-great-d_experiment_4b21ff3f21ca/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/great_depression/20260318T202957Z_what-were-the-main-causes-of-the-great-d_experiment_4b21ff3f21ca/experiment.json`

### Before / After vs `001`

- Plan quality: unchanged. The same 4-step historical / scholarly plan was generated.
- Evidence count: improved from `20` to `12`.
- Evidence utilization: improved from `0.15` to `0.3333`.
- Groundedness: unchanged at `0.6667`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=2, insufficient=1`.

### Claims

`001`
- `A perfect storm of unlucky factors led to the start of the worst economic downturn in U.S. history.`
- `A fall in total demand may have originated the Great Depression, but its length and severity resulted primarily from other causes.`
- `Monetary and fiscal policies were ineffective in addressing the economic downturn.`

`002`
- `The stock market crash of 1929 triggered the Great Depression.`
- `Monetary policy mistakes by the Federal Reserve contributed to the Great Depression.`
- `Overproduction and underconsumption led to a surplus of goods, which contributed to the Great Depression.`

### Assessment

- This is the clearest improvement in the set.
- Claim specificity improved substantially.
- The `perfect storm` umbrella claim is gone.
- The answer stayed strongly on-question.
- Evidence relevance is still imperfect because some obviously noisy titles remained in the 12-item pool, but the final claims are much better than `001`.
- The third claim was still marked `insufficient`, so verification did not improve, but the answer itself is more usable.

## Run C: Dot-Com Crash

### Question

`What were the main causes of the dot-com crash?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/dot_com_crash/20260318T203034Z_what-were-the-main-causes-of-the-dot-com_experiment_563fd9b10b4a/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_002/dot_com_crash/20260318T203034Z_what-were-the-main-causes-of-the-dot-com_experiment_563fd9b10b4a/experiment.json`

### Before / After vs `001`

- Plan quality: unchanged. The same 4-step plan was generated.
- Evidence count: improved from `20` to `12`.
- Evidence utilization: improved from `0.1` to `0.25`.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Verification: unchanged at `supported=3`.

### Claims

`001`
- `Regulatory failures and systemic flaws contributed to the dot-com crash.`
- `Speculation and unsustainable increases in stock market valuations caused the dot-com bubble.`
- `Failure to monitor market imbalances contributed to the dot-com crash.`

`002`
- `Regulatory shortcomings exposed by the crisis included a lack of tools for supervisors to manage the financial system.`
- `Speculation in dot-com businesses caused a stock market bubble that led to the crash.`
- `Regulatory failures contributed to the crash by failing to stop or exacerbate financial crises.`

### Assessment

- Evidence discipline improved materially.
- The vague `systemic flaws` phrasing is gone, but the replacement is not clearly better.
- One claim remains clean and causal: speculation in dot-com businesses.
- Two claims drift toward generic regulatory language and one is partially circular (`exposed by the crisis` / `financial crises`) rather than tightly answering the dot-com question.
- Source relevance is still noisy in `002`, with several titles that look only loosely connected to the dot-com crash.
- Net result: metrics improved, but answer quality only improved partially.

## Aggregate Comparison

### Did Evidence Utilization Improve?

Yes.

- 2008 financial crisis: `0.2667` -> `0.3333`
- Great Depression: `0.15` -> `0.3333`
- Dot-com crash: `0.1` -> `0.25`

This is the clearest and most consistent improvement from the hardening change. The reduced executor handoff size produced a meaningfully tighter evidence pool in all three runs.

### Did Claim Specificity Improve?

Partially, but not uniformly.

- 2008 financial crisis: mixed. The broad umbrella claim disappeared, but two replacement claims are not as cleanly causal as desired.
- Great Depression: yes, strongly improved.
- Dot-com crash: mixed. One vague phrase was removed, but two claims still read as generic regulatory commentary.

### Did Question Relevance Remain Strong?

Mostly yes.

- No obvious return of the old response/policy failure mode.
- Great Depression stayed clearly on-question.
- 2008 and dot-com both remained adjacent to the question, but some claims drifted toward timeline/context or generic regulatory framing instead of crisp causes.

### Did Groundedness Stay Acceptable?

Yes.

- 2008 financial crisis improved from `0.6667` to `1.0`
- Great Depression stayed at `0.6667`
- Dot-com crash stayed at `1.0`

Groundedness remained acceptable for v0 across the set.

### Is `002` Better Than `001` Overall?

Yes, but with caveats.

Why `002` is better overall:
- evidence utilization improved on all 3 questions
- evidence count dropped from `15/20/20` to `9/12/12`
- Great Depression improved substantially in claim specificity
- groundedness did not regress overall and improved on the 2008 question

Why the improvement is not cleanly uniform:
- 2008 claim formulation became more grounded but not more elegantly causal
- dot-com claim wording still suffers from generic regulatory drift
- search/provider noise is still clearly visible in the evidence pool

## Overall Assessment

The quality-hardening change materially improved the live baseline in the narrow way it was intended to:

- it tightened the evidence pool
- it improved evidence utilization across the board
- it reduced some vague umbrella claim behavior

But it did not solve single-pass synthesis drift. The remaining issues are now easier to see:

- some claims still turn direct evidence into awkward or weakly causal summaries
- some search steps still admit noisy titles even with the smaller pool
- verification remains too weak to strongly punish generic-but-lexically-supported claims

## Conclusion

`v0_tier1_eval_set_002` is a better reference set than `001` for the current hardened v0 pipeline, but only as an incremental improvement, not as a decisive quality jump.
