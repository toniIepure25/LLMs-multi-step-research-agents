## Handoff: v1 Full-Set Completeness Hardening

### What was done
- Diagnosed the latest v1-minimal full-set failures as generation-side mechanism-family undercoverage under the live budget, not a fresh selector failure.
- Expanded the synthesizer's deterministic family backfill for causal goals in `asar/deliberation/simple_synthesizer.py`.
- Added a safer 2008 mortgage-backed-securities family so thin live evidence can recover a third supported mechanism without forcing an unsupported subprime claim.
- Added Great Depression family backfill for:
  - stock market crash of 1929
  - monetary contraction and banking panics
  - protectionism and collapse of world trade
- Added a narrow redundancy guard so explicit subprime-family coverage suppresses the generic mortgage-backed backfill.
- Added focused regression tests for 2008 and Great Depression thin-candidate collapse cases.

### What was NOT done
- No live reruns were performed.
- No selector rewrite was made.
- No schema, provider, or verification changes were made.

### Decisions made
- Kept the fix inside `SimpleSynthesizer` because the selector was being starved by thin candidate sets rather than ranking obviously good candidates incorrectly.
- Preferred deterministic family backfill over prompt growth because the remaining failures were budget-sensitive and topic-family specific.
- Used a generic mortgage-backed claim for non-subprime MBS evidence so support quality stays safer than forcing `Subprime lending` from weaker aliases.

### Open questions
- Whether the broader Great Depression family backfill consistently preserves 3 claims in live full-set conditions.
- Whether 2008 full-set runs now keep 3 supported mechanisms without drifting toward broader regulation-only mixes.

### Suggested next steps
1. Rerun only the focused 2008 v1-minimal live probe and compare it against `v1_2008_probe_014`.
2. Rerun only the focused Great Depression v1-minimal live probe and check whether the missing third mechanism now recovers cleanly.
3. Only if both focused probes hold, rerun the full 3-question v1 Tier 1 set.
