## Handoff: Domain Anchor Hardening

### What was done
- Preserved goal-side domain anchors in task query construction when a plan step became too broad.
- Updated execution relevance scoring to prioritize original goal anchors over step-only anchor terms.
- Added tests for broad-step query anchoring and wrong-domain technology-step filtering.

### What was NOT done
- No live evaluation reruns were performed in this step.
- No planner prompt changes or Phase 2 features were added.

### Decisions made
- Kept the fix inside frozen v0 behavior by changing only task query construction and deterministic execution scoring.
- Allowed execution to return fewer than `top_k` results when goal-anchored matches exist and anchorless step-only matches look misaligned.

### Open questions
- Whether goal-anchor preservation is sufficient for near-synonym cases like `internet` vs `dot-com`.
- Whether the next live dot-com probe drops the remaining wrong-domain technology results in practice.

### Suggested next steps
- Rerun the focused dot-com live probe and inspect the technology-step evidence titles/snippets.
- If the probe is clean, rerun the 3-question Tier 1 set and compare against `v0_tier1_eval_set_002`.
