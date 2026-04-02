## Handoff: v1 Candidate Budget Stability

### What was done
- Diagnosed the remaining v1-minimal instability as primarily candidate-generation instability under the live `llama3.1:8b` / `512` token budget.
- Hardened `SimpleSynthesizer` so candidate generation is slightly leaner:
  - reduced serialized evidence content/title lengths
  - removed URL fields from the candidate-generation evidence payload
- Replaced the old single 2008-only mechanism family table with goal-aware family rules.
- Extended deterministic family coverage so thin live candidate sets can be backfilled for:
  - 2008: broader subprime / mortgage-backed-securities wording
  - dot-com: speculation, overvaluation, and regulation families
- Added regression tests for:
  - thin 2008 candidate sets with MBS/subprime evidence
  - thin dot-com candidate sets missing the third mechanism

### What was NOT done
- No live reruns were performed in this step.
- No selector rewrite was made.
- No provider, verification, or orchestration changes were made.

### Decisions made
- Treated the root cause as generation starvation rather than selector scoring, because the selector already behaved reasonably when healthier candidate sets were available.
- Kept the fix inside `SimpleSynthesizer` to preserve the current v1-minimal architecture.
- Used deterministic family backfill rather than more prompt tuning so the recovery path stays inspectable and testable.

### Open questions
- Whether the leaner payload plus broader family backfill is enough to hold 2008 support quality in a live rerun.
- Whether the dot-com third mechanism now returns consistently without hurting claim phrasing quality.

### Suggested next steps
1. Run one focused live 2008 v1-minimal probe and compare it against `v1_2008_probe_013`.
2. Run one focused live dot-com v1-minimal probe and check whether the third mechanism claim returns.
3. Only if both focused probes hold should the next full 3-question v1 Tier 1 rerun be attempted.
