# v0 Tier 1 Eval Set 001

## Scope

Small live evaluation set for the frozen v0 pipeline.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used across all runs
- Goal: check whether the current v0 pipeline generalizes reasonably across a tiny set of broad Tier 1 questions

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

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/financial_crisis_2008/20260318T192759Z_what-were-the-main-causes-of-the-2008-fi_experiment_f611b8f921ee/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/financial_crisis_2008/20260318T192759Z_what-were-the-main-causes-of-the-2008-fi_experiment_f611b8f921ee/experiment.json`

### Summary

- Plan quality: sensible 3-step sequential plan focused on timeline/events, deregulation, and securitization.
- Evidence relevance/provenance: good provenance structure and even distribution across steps; evidence set leaned heavily toward securitization sources in this run.
- Claims:
  - `Securitization played a significant role in the 2008 financial crisis.`
  - `Deregulation of the financial services sector contributed to the 2008 financial crisis.`
  - `The failure of securitization and deregulation to regulate the financial system led to the 2008 financial crisis.`
- Verification: `supported=2, unsupported=0, insufficient=1, contradicted=0`
- Metrics:
  - `groundedness=0.6667`
  - `evidence_utilization=0.2667`
  - `plan_coverage=1.0`

### On-Question Assessment

- Yes, the answer stayed on-question.
- The original off-question policy/response failure mode did not reappear.

### Suspicious Output

- One claim was marked `insufficient`, so the run was less strong than the best `baseline_002` reference.
- The third claim is awkwardly worded (`failure of securitization and deregulation to regulate the financial system`) and reads like synthesis drift rather than a clean causal statement.

## Run B: Great Depression

### Question

`What were the main causes of the Great Depression?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/great_depression/20260318T192859Z_what-were-the-main-causes-of-the-great-d_experiment_c1622f377bc9/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/great_depression/20260318T192859Z_what-were-the-main-causes-of-the-great-d_experiment_c1622f377bc9/experiment.json`

### Summary

- Plan quality: coherent but more ambitious than the 2008 run, with 4 steps spanning historical accounts, categorization, scholarly sources, and consensus synthesis.
- Evidence relevance/provenance: provenance remained intact and evidence was evenly distributed across all 4 steps.
- Claims:
  - `A perfect storm of unlucky factors led to the start of the worst economic downturn in U.S. history.`
  - `A fall in total demand may have originated the Great Depression, but its length and severity resulted primarily from other causes.`
  - `Monetary and fiscal policies were ineffective in addressing the economic downturn.`
- Verification: `supported=2, unsupported=0, insufficient=1, contradicted=0`
- Metrics:
  - `groundedness=0.6667`
  - `evidence_utilization=0.15`
  - `plan_coverage=1.0`

### On-Question Assessment

- Mostly yes, but the answer quality is weak.
- The claims stayed broadly related to causes, but they became too generic and under-specified for a good factual summary.

### Suspicious Output

- `A perfect storm of unlucky factors...` is too vague to be a strong research claim.
- `Monetary and fiscal policies were ineffective...` sounds more like a response/outcome framing than a direct answer to the causes question, though it stayed adjacent to the topic.
- This was the weakest run in the set.

## Run C: Dot-Com Crash

### Question

`What were the main causes of the dot-com crash?`

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/dot_com_crash/20260318T192851Z_what-were-the-main-causes-of-the-dot-com_experiment_830b1feee34d/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_001/dot_com_crash/20260318T192851Z_what-were-the-main-causes-of-the-dot-com_experiment_830b1feee34d/experiment.json`

### Summary

- Plan quality: straightforward 4-step plan covering scope/timeline, economic factors, technological over-saturation, and regulation.
- Evidence relevance/provenance: provenance remained inspectable and step coverage was even, though some top search results looked noisier than ideal.
- Claims:
  - `Regulatory failures and systemic flaws contributed to the dot-com crash.`
  - `Speculation and unsustainable increases in stock market valuations caused the dot-com bubble.`
  - `Failure to monitor market imbalances contributed to the dot-com crash.`
- Verification: `supported=3, unsupported=0, insufficient=0, contradicted=0`
- Metrics:
  - `groundedness=1.0`
  - `evidence_utilization=0.1`
  - `plan_coverage=1.0`

### On-Question Assessment

- Yes, the answer stayed on-question.
- The claims are concise and causal.

### Suspicious Output

- Source quality looked more mixed than the metrics suggest; some evidence titles appeared only loosely aligned with the dot-com crash.
- `evidence_utilization=0.1` indicates that most evidence gathered did not make it into the final claims.
- The verifier may be somewhat permissive here relative to the noisiness of the evidence pool.

## Aggregate Summary

### Best Performer

`What were the main causes of the dot-com crash?`

Why:

- Best verification result (`supported=3`)
- Best groundedness (`1.0`)
- Answer stayed clearly on-question
- No obvious off-question claim drift

### Worst Performer

`What were the main causes of the Great Depression?`

Why:

- Generic and partially vague claims
- One `insufficient` verdict
- Lowest-quality synthesis in the set despite complete pipeline execution

### Recurring Failure Modes

1. **Low evidence utilization**
   - All three runs collected much more evidence than the final claims used.
   - This looks like a v0 synthesis-selection limitation rather than a routing bug.

2. **Run-to-run and question-to-question synthesis variability**
   - The pipeline stays operational, but claim quality varies.
   - This is most visible on the 2008 and Great Depression runs.

3. **Verification is useful but weak**
   - It catches some insufficiency, but it does not strongly police vague or weakly framed causal claims.
   - This remains acceptable for v0 but is still an important limitation.

### Stability Assessment

- v0 is stable enough to keep as a real baseline.
- The pipeline completed all 3 live runs successfully.
- Provenance and step linkage remained intact across the set.
- The relevance hardening appears to have fixed the original off-question response/policy failure mode.
- However, answer quality is still modest and variable, which should be treated as an acceptable v0 limitation rather than proof that the problem is solved.

## Overall Conclusion

The current live v0 pipeline is good enough to preserve as the project baseline:

- it runs end-to-end reliably
- it stays broadly grounded
- it is capable of producing on-question causal answers
- it still shows normal single-pass LLM variance and weak evidence selection discipline

That is sufficient for a frozen v0 baseline, but not yet strong enough to claim robust research quality.
