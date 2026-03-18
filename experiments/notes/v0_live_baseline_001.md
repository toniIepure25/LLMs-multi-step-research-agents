# v0 Live Baseline 001

## Status

Not executed in this environment.

The canonical live v0 path is already implemented, but this machine does not currently have the required live credentials or provider overrides set:

- `OPENAI_API_KEY`
- `BRAVE_SEARCH_API_KEY`
- `ASAR_MODEL_PROVIDER=openai`
- `ASAR_MODEL_MODEL=<live-model>`

Because of that, no real provider-backed baseline artifact was produced in this session.

## Canonical Question

`What were the main causes of the 2008 financial crisis?`

## Provider Mode

`live`

## Exact Manual Run Command

```bash
export OPENAI_API_KEY=...
export BRAVE_SEARCH_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL=gpt-5.2

uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live \
  --output-dir experiments/runs/v0_live_baseline_001
```

## Expected Artifact Paths

The run should write a timestamped directory under:

`experiments/runs/v0_live_baseline_001/`

Expected files inside the generated run directory:

- `output.json`
- `experiment.json`

The concrete path shape will be:

`experiments/runs/v0_live_baseline_001/<YYYYMMDD>T<HHMMSS>Z_what-were-the-main-causes-of-the-2008-financial-crisis_<experiment_id>/`

## Inspection Checklist

After the live run completes, inspect the generated `output.json` and `experiment.json` using the checklist below.

### 1. Plan quality

- `ResearchPlan` exists and is schema-valid
- step count is between 3 and 5
- steps are sequential and sensible for the question
- no parallel branches or speculative planning behavior appear

### 2. Evidence quality

- each `EvidenceItem` is schema-valid
- each item has populated `SourceMetadata`
- provenance fields are inspectable and non-empty
- evidence covers multiple plan steps rather than collapsing onto one search result

### 3. Deliberation quality

- `DecisionPacket` is present and schema-valid
- claims reference only real `evidence_` IDs from the run
- claims are concise and grounded rather than generic summaries
- any conflict markers are minimal and inspectable

### 4. Verification quality

- `VerificationResult` is present and schema-valid
- verdicts look reasonable under the weak deterministic v0 heuristic
- no claim is marked `SUPPORTED` without plausible lexical overlap to cited evidence
- any `INSUFFICIENT` or `CONTRADICTED` verdicts are understandable from the artifacts

### 5. Evaluation quality

- `groundedness` is sensible for the produced claims
- `evidence_utilization` is neither trivially `0.0` nor suspiciously perfect without justification
- `plan_coverage` reflects actual step linkage from execution
- `number_of_claims`, `number_of_evidence_items`, and `number_of_supported_claims` align with the artifacts

### 6. Overall acceptability

- output artifacts are easy to inspect manually
- the run is coherent enough to serve as the first real provider-backed v0 baseline
- any suspicious behavior is recorded before comparing later runs

## Run Record Template

Fill this section in immediately after the first real live run.

### Command Used

`<paste exact command>`

### Artifact Paths

- `output.json`: `<paste path>`
- `experiment.json`: `<paste path>`

### High-Level Summary

- Plan: `<3-5 step summary>`
- Evidence: `<count + notable sources>`
- Claims: `<count + short summary>`
- Verdicts: `<supported / insufficient / contradicted summary>`
- Metrics: `<groundedness, evidence_utilization, plan_coverage>`

### Weak Or Suspicious Aspects

- `<note any brittle planning, poor evidence, odd claims, or surprising verdicts>`

### Baseline Assessment

- Acceptable as first real baseline: `<yes/no>`
- Why: `<brief rationale>`

### Recommended Next Improvement

- `<single next improvement after baseline review>`

## Notes From This Session

- The live demo path and provider factory were inspected before recording this note.
- The current environment was missing both provider credentials and the required live model overrides.
- Per project instructions, no live run was faked and no Phase 2 work was started.
