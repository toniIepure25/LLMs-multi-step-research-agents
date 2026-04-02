## Handoff: 2008 Causal Claim Hardening

### What was done
- Tightened `SimpleSynthesizer` causal-answer prompting to explicitly prefer direct mechanism-to-event phrasing.
- Added a small deterministic rewrite for grounded descriptive mechanism claims like securitization and deregulated-derivatives descriptions so they normalize to direct causal claims when a causal goal subject is available.
- Added exact-target normalization for generic phrases like `the financial crisis` -> the concrete goal subject when possible.
- Tightened post-parse filtering so non-direct causal claims do not survive when cleaner direct causal claims are available.
- Added deliberation tests covering 2008-style mechanism phrasing and updated the mocked v0 integration fixture to emit direct causal claims consistent with the hardened contract.

### What was NOT done
- No live reruns were performed in this step.
- No retrieval, planning, verification, or schema changes were made.
- No Phase 2 features were introduced.

### Decisions made
- Kept the fix inside `asar/deliberation/simple_synthesizer.py` to preserve the frozen v0 architecture.
- Used a narrow hybrid approach: prompt tightening plus transparent deterministic normalization/filtering.
- Updated the integration test fixture rather than weakening the new filter, so the canonical mocked v0 test still reflects the current causal-answer contract.

### Open questions
- Whether the new normalization/filtering makes the 2008 live rerun consistently stay closer to the stronger `v0_2008_probe_006` shape.
- Whether any remaining weak 2008 claims are now mostly provider/evidence noise rather than synthesizer formatting drift.

### Suggested next steps
1. Rerun only the 2008 financial crisis live probe and compare it against `v0_2008_probe_006` and the 2008 run from `v0_tier1_eval_set_004`.
2. If the 2008 probe is stable, rerun the full 3-question Tier 1 live set before changing anything else in v0.
