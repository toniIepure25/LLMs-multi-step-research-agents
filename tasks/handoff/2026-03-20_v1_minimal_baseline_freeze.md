## Handoff: v1 Minimal Baseline Freeze

### What v0 proved
- The frozen v0 sequential slice could run end-to-end in live conditions with typed artifacts and deterministic verification.
- `v0_tier1_eval_set_004` is a credible historical reference point for future comparisons.
- v0 also exposed the main structural bottleneck: single-pass synthesis was trying to generate, select, and phrase claims at the same time.

### What v1-minimal added
- An explicit candidate-claim generation boundary in `deliberation`.
- A deterministic `ClaimSelector` after generation.
- Support-aware, question-aware, non-duplication-aware final claim selection.
- Narrow generation and selection hardening to stabilize 2008, preserve dot-com cleanliness, and recover acceptable Great Depression completeness.

### What improved
- 2008 direct-causal answers improved materially relative to frozen v0.
- Dot-com retrieval stayed clean and did not regress back to wrong-domain crash/vehicle noise.
- Great Depression recovered enough to be acceptable as part of the active v1-minimal baseline.
- `v1_tier1_eval_set_004` is the first full v1-minimal live set strong enough to serve as the active experimental baseline.

### What still remains imperfect
- Some phrasing is still broader or more evidence-shaped than ideal.
- Evidence utilization is not uniformly optimal across questions.
- Great Depression is acceptable, but not yet the strongest mechanism mix seen in earlier focused or comparison runs.
- v1-minimal is better overall, but it is not a final architecture.

### What is intentionally postponed
- Grounding and `CitationRecord`-heavy evidence normalization.
- Replanning loops.
- Parallel execution.
- Debate or multi-perspective deliberation.
- Advanced memory compression.
- Broad verification redesign.
- Benchmark expansion beyond the current focused Tier 1 workflow.

### Formal baseline status
- Frozen historical v0 baseline:
  - [v0_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental v1-minimal baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)

### Recommended next architectural step
- Stop narrow v1-minimal tuning for now.
- Begin the next phase from the v1-minimal baseline intentionally.
- The next phase should be a consciously scoped architectural step beyond v1-minimal, not another round of micro-tuning inside the same loop.


### Follow-up status
- Subsequent v1.1 grounded-selection exploration did not change the baseline decision.
- Subsequent v1.2 mechanism-bundling exploration also did not change the baseline decision.
- Subsequent v1.3 mechanism-sketching exploration also did not change the baseline decision.
- Subsequent v1.4 slot-grounded drafting exploration also did not change the baseline decision.
- `v1_tier1_eval_set_004` remains the active experimental baseline.
- See [2026-03-21_v1_1_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) for the exploratory v1.1 outcome and freeze rationale.
- See [2026-03-25_v1_2_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) for the exploratory v1.2 outcome and freeze rationale.
- See [2026-03-26_v1_3_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) for the exploratory v1.3 outcome and freeze rationale.
- See [2026-03-31_v1_4_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md) for the exploratory v1.4 outcome and freeze rationale.
