# v0 Live Baseline 001

## Status

Executed successfully on 2026-03-18.

This note records the first successful provider-backed v0 baseline for the canonical question.

Provider configuration used:

- `ASAR_MODEL_PROVIDER=openai`
- `ASAR_MODEL_MODEL=llama3.1:8b`
- `ASAR_OPENAI_BASE_URL=https://inference.ccrolabs.com/v1`
- `ASAR_SEARCH_PROVIDER=tavily`

Secrets were supplied via environment variables at runtime and are intentionally omitted here.

## Canonical Question

`What were the main causes of the 2008 financial crisis?`

## Provider Mode

`live`

### Command Used

```bash
export OPENAI_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL="llama3.1:8b"
export ASAR_OPENAI_BASE_URL="https://inference.ccrolabs.com/v1"
export ASAR_MODEL_MAX_TOKENS=512

export TAVILY_API_KEY=...
export ASAR_SEARCH_PROVIDER=tavily

uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live \
  --output-dir experiments/runs/v0_live_baseline_001
```

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_001/20260318T183357Z_what-were-the-main-causes-of-the-2008-fi_experiment_4b883e4fdf84/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_001/20260318T183357Z_what-were-the-main-causes-of-the-2008-fi_experiment_4b883e4fdf84/experiment.json`

### High-Level Summary

- Plan: 3 sequential steps covering timeline/events, deregulation, and securitization.
- Evidence: 15 `EvidenceItem`s, evenly distributed across the 3 steps (5 each), with inspectable provenance. Notable sources included Investopedia, Economics Observatory, Federal Reserve-adjacent material, IMF, NY Fed, Harvard LPR, and Mercatus.
- Claims: 3 claims. Two answer the question directly (`deregulation`, `subprime mortgage issuance`). One high-confidence claim drifted into crisis response (`Emergency Economic Stabilization Act of 2008`) rather than a cause.
- Verdicts: 3 `supported`, 0 `insufficient`, 0 `contradicted`.
- Metrics: `groundedness=1.0`, `evidence_utilization=0.2667`, `plan_coverage=1.0`, `number_of_claims=3`, `number_of_evidence_items=15`, `number_of_supported_claims=3`.

### Weak Or Suspicious Aspects

- The deliberation output partially drifted off-question: one final claim is about a policy response to the crisis, not a cause of the crisis.
- The plan explicitly investigated securitization, but the final claims omitted it and instead surfaced the bailout act; this suggests synthesis relevance drift rather than retrieval failure.
- The deterministic v0 verifier marked all claims `supported`, which is acceptable for v0 but did not catch the off-question claim because it checks evidence linkage and lexical overlap rather than question relevance.
- Source quality is mixed, with some strong institutional sources and some weaker or more opinionated sources in the evidence pool.

### Baseline Assessment

- Acceptable as first real baseline: `yes`
- Why: the full v0 live stack completed end-to-end, produced schema-valid artifacts, maintained provenance across all 15 evidence items, and generated fully supported claims under the current v0 verifier. The remaining issue is answer quality, not pipeline viability.

### Recommended Next Improvement

- Add a stronger question-relevance constraint in deliberation and/or verification so final claims must answer the original user question, not merely be supported by nearby crisis-related evidence.

## Post-Fix Rerun: v0 Live Baseline 002

The same canonical live path was rerun after relevance hardening using the same question and provider path, but with a separate output directory:

`experiments/runs/v0_live_baseline_002/`

### Command Used

```bash
export OPENAI_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL="llama3.1:8b"
export ASAR_OPENAI_BASE_URL="https://inference.ccrolabs.com/v1"
export ASAR_MODEL_MAX_TOKENS=512

export TAVILY_API_KEY=...
export ASAR_SEARCH_PROVIDER=tavily

uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live \
  --output-dir experiments/runs/v0_live_baseline_002
```

### Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_002/20260318T185739Z_what-were-the-main-causes-of-the-2008-fi_experiment_f7891b45eea0/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_002/20260318T185739Z_what-were-the-main-causes-of-the-2008-fi_experiment_f7891b45eea0/experiment.json`

### Before / After Assessment

- Plan quality: unchanged and still sensible. Both runs produced the same 3 sequential steps covering timeline/events, deregulation, and securitization.
- Groundedness: unchanged at `1.0`.
- Plan coverage: unchanged at `1.0`.
- Evidence count: unchanged at `15`.
- Supported claims: unchanged at `3`.
- Evidence utilization: improved from `0.2667` to `0.4`.

Claim comparison:

- `baseline_001` claims:
  - `Deregulation contributed to the 2008 financial crisis.`
  - `Subprime mortgage issuance was a major factor in the 2008 financial crisis.`
  - `The Emergency Economic Stabilization Act of 2008 was passed in response to the financial crisis.`
- `baseline_002` claims:
  - `Deregulation led to the 2008 financial crisis.`
  - `Securitization played a significant role in the 2008 financial crisis.`
  - `The failure of regulatory oversight led to the 2008 financial crisis.`

### Result

- The previous off-question response/policy claim is gone.
- It was replaced by on-question causal claims about securitization and regulatory failure.
- The pipeline remained healthy end-to-end and the artifacts remained schema-valid and grounded.
- The relevance hardening improved answer quality without damaging the frozen v0 path.

### Updated Baseline Assessment

- `baseline_002` is acceptable as the canonical v0 live baseline.
- It preserves the working live stack while producing claims that better answer the actual user question.

## Repeat Check: baseline_002 second live run

The same `baseline_002` command was run again on 2026-03-18 to check whether the relevance hardening held up across repeated live runs.

Artifact paths:

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_002/20260318T191035Z_what-were-the-main-causes-of-the-2008-fi_experiment_3388cf069025/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_live_baseline_002/20260318T191035Z_what-were-the-main-causes-of-the-2008-fi_experiment_3388cf069025/experiment.json`

Observed result:

- The off-question policy/response claim did not return.
- The final claims stayed on-question and causal:
  - `Securitization played a significant role in the 2008 financial crisis.`
  - `Deregulation of the financial services sector led to the 2008 financial crisis.`
  - `The failure of securitization and deregulation was a primary cause of the 2008 financial crisis.`
- Plan shape stayed stable at 3 sequential steps.
- `plan_coverage` stayed at `1.0`.

However, this repeat run was slightly weaker than the first `baseline_002` run:

- `groundedness` dropped from `1.0` to `0.6667`
- `number_of_supported_claims` dropped from `3` to `2`
- one securitization claim was marked `insufficient`
- `evidence_utilization` returned to `0.2667`

Interpretation:

- The relevance hardening appears stable for the original failure mode: the off-question bailout/policy claim has remained gone across repeated runs.
- Live output quality is still somewhat variable, which is consistent with v0's single-pass LLM synthesis and weak deterministic verification.
- The first `baseline_002` run remains the strongest canonical live v0 reference, while this second repeat run is useful evidence that relevance improved but run-to-run quality variance still exists.

## Notes From This Session

- Earlier in the session, `llama3.3:70b` on the same OpenAI-compatible endpoint failed provider-side; `llama3.1:8b` was the stable working model for this baseline.
- Tavily authentication and the OpenAI-compatible base URL path were verified before the final successful run.
- No Phase 2 grounding work was introduced; this remained a pure v0 sequential baseline.
