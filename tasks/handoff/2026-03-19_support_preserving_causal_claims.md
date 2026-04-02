## Handoff: Support-Preserving Causal Claims

### What was done
- Diagnosed the `v0_2008_probe_007` regression as a support-quality tradeoff rather than a pure phrasing failure.
- Added support-aware claim normalization in `SimpleSynthesizer` so over-specific causal claims can be generalized back to a stronger supported mechanism claim.
- Strengthened the prompt to prefer the most directly supported mechanism formulation and to keep distinct supported mechanisms as separate claims.
- Added tests covering weakly supported over-specific claims, distinct mechanism preservation, and prompt contract updates.

### What was NOT done
- No live reruns were performed in this step.
- No execution, planning, verification, or schema changes were made.
- No Phase 2 features were introduced.

### Decisions made
- Kept the fix inside `asar/deliberation/simple_synthesizer.py`.
- Used a narrow hybrid approach: prompt guidance plus evidence-aware deterministic normalization.
- Prioritized support preservation over cleaner-but-brittle specificity.

### Open questions
- Whether the next 2008 live probe keeps the cleaner direct-causal phrasing while avoiding the groundedness drop seen in `v0_2008_probe_007`.
- Whether the OTC-derivatives claim shape becomes stable again in live output.

### Suggested next steps
1. Rerun only the 2008 financial crisis live probe and compare it directly with `v0_2008_probe_006` and `v0_2008_probe_007`.
2. If groundedness/support recover while direct causal phrasing remains clean, then consider rerunning the full 3-question Tier 1 set.
