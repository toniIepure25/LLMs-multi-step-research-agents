## Handoff: v1.1 Exploratory Freeze

### What v1.1 attempted to add
- A local deterministic `SupportAttributor` inside `deliberation`.
- Support-attribution-aware `ClaimSelector` behavior before final `DecisionPacket` packaging.
- A minimal grounding-aware selection step without changing providers, orchestration, or the broader pipeline shape.

### What worked in mocked tests
- Weak-support-vs-strong-support regressions passed.
- Diversity-aware selector behavior passed.
- End-to-end mocked `SimpleSynthesizer.deliberate(...)` diversity composition also passed.
- The exploration produced meaningful evidence that grounding-aware selection can help when support signals are reliable enough.

### What failed in live 2008 probing
- [v1_1_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_1_2008_probe_001.md) regressed materially versus the active v1-minimal baseline:
  - claim count dropped from `3` to `2`
  - groundedness dropped from `1.0` to `0.5`
  - verification quality regressed
  - the third mechanism disappeared
- [v1_1_2008_probe_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_1_2008_probe_002.md) improved over the first v1.1 probe, but still did not beat the active v1-minimal baseline:
  - claim count recovered to `3`
  - groundedness recovered only partway to `0.6667`
  - the clean securitization claim still verified as `insufficient`
  - stable support for the securitization family was still not robust enough

### Why v1.1 was not promoted
- It did not beat [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md) on the key 2008 criteria.
- The support-attribution layer remained too brittle in live conditions around the subprime / borrower / lending / securitization family.
- The promotion bar was explicit: v1.1 needed to improve support-quality choice without regressing groundedness, claim count, or mechanism stability. It did not clear that bar.

### What remains promising about the idea
- Grounding-aware selection still looks promising in principle.
- The mocked checkpoints suggest support attribution can improve weak-support filtering and diversity-aware composition.
- The idea remains a useful input to a future design step, even though this specific v1.1 branch should not be promoted as-is.

### Explicit status
- Frozen historical baseline:
  - [v0_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- Exploratory only, not promoted:
  - [v1_1-grounded-selection-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_1-grounded-selection-architecture.md)
  - [v1_1_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_1_2008_probe_001.md)
  - [v1_1_2008_probe_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_1_2008_probe_002.md)

### What should happen next instead of more tuning
- Do not continue narrow v1.1 tuning by default.
- Keep v1-minimal as the active runtime comparison point.
- Start the next phase with a new consciously scoped architecture-design step that uses the v1.1 exploration as evidence, not as the default implementation queue.

### Follow-up status
- Subsequent v1.2 mechanism-bundling exploration also remained exploratory and was not promoted.
- Subsequent v1.3 mechanism-sketching exploration also remained exploratory and was not promoted.
- Subsequent v1.4 slot-grounded drafting exploration also remained exploratory and was not promoted.
- `v1_tier1_eval_set_004` still remains the active experimental baseline after the later exploratory branches.
- See [2026-03-25_v1_2_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) for the v1.2 freeze rationale.
- See [2026-03-26_v1_3_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) for the v1.3 freeze rationale.
- See [2026-03-31_v1_4_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md) for the v1.4 freeze rationale.
