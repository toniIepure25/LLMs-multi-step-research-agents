## Handoff: v1 2008 Candidate Stability Hardening

### What was done
- Diagnosed the `v1_tier1_eval_set_001` 2008 regression as primarily a
  candidate-generation problem, not just selector scoring.
- Hardened `SimpleSynthesizer` so over-specific 2008-style causal claims are
  generalized more reliably when support text does not justify the extra
  qualifier.
- Added a small deterministic candidate-coverage backstop that recovers
  missing supported mechanism families from evidence anchors when a causal
  candidate set is thin but non-trivial.
- Updated mocked v1 integration expectations to the hardened candidate
  contract.
- Ran `uv run ruff check ...` and `uv run pytest`.

### What was NOT done
- No live reruns were performed in this step.
- No provider changes were made.
- No selector redesign or Phase 2 work was introduced.

### Decisions made
- Chose to harden candidate generation rather than the selector because the
  full-set 2008 failure omitted the sharper OTC claim entirely and collapsed to
  two final claims, which the selector could not recover from.
- Kept the backstop small by reusing explicit 2008 mechanism-family anchors
  already implicit in the synthesizer normalization logic.

### Open questions
- Whether the new candidate backfill is enough to stabilize the 2008 live run
  under the full evaluation setting.
- Whether the backfill should remain narrowly 2008-oriented or later be
  generalized after more v1 evidence is collected.

### Suggested next steps
- Rerun only the focused live 2008 v1-minimal probe again.
- Compare it directly against `v1_2008_probe_012` and the 2008 run inside
  `v1_tier1_eval_set_001`.
- Only if that probe is stable, retry the full 3-question v1 Tier 1 set.
