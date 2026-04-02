## Handoff: v0 Freeze And v1 Minimal

### What was done
- Marked v0 as frozen in the repo docs.
- Declared `v0_tier1_eval_set_004` as the official live reference baseline.
- Added a minimal v1 architecture proposal centered on support-aware claim selection after claim generation.
- Added a focused implementation plan for v1 minimal.

### What was NOT done
- No v1 code was implemented.
- No schemas or protocols were changed.
- No live reruns were performed.

### Decisions made
- v0 tuning is complete for now and later probes remain comparison records only.
- The smallest sensible v1 step is to separate candidate claim generation from claim selection.
- `ClaimSelector` is the only new architectural capability planned for the first v1 step.

### Open questions
- Whether `ClaimSelector` should remain fully deterministic in the first cut or use a very small LLM-assisted ranking prompt later.
- Whether a new internal candidate-claim type is needed or whether existing `Claim`-adjacent structures are enough.

### Suggested next steps
1. Start with `tasks/v1_minimal_plan.md`.
2. Build the candidate claim generation output contract.
3. Implement the selector and validate it on mocked 2008-style tests before any live run.
