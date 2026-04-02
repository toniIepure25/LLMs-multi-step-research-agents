## Handoff: v1.4 Exploratory Freeze

### What v1.4 attempted to add
- A local deterministic `MechanismSlotBuilder` inside `deliberation`.
- Compact grounded `MechanismSlot` objects before final claim wording and selection.
- A narrow slot-grounded drafting step without changing providers, schemas, orchestration, or the broader runtime shape.

### What worked in mocked checkpoints
- Thin-2008 grounded-slot preservation regressions passed.
- End-to-end mocked slot-grounded deliberation coverage passed.
- The exploration produced useful evidence that preserving explicit grounded slots can stabilize mechanism structure before final wording.

### What worked in the focused live 2008 probe
- [v1_4_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_4_2008_probe_001.md) completed successfully in live conditions.
- Core viability was acceptable:
  - `3` claims
  - OTC derivatives stayed preserved
  - evidence utilization improved materially
- The result showed that slot-grounded drafting is viable enough to evaluate in real conditions.

### What failed to clear the promotion bar
- `v1.4` did not show clear overall superiority to [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md).
- Groundedness regressed from the active v1-minimal 2008 baseline to `0.6667`.
- One claim verified as `insufficient`.
- The final set duplicated the housing-finance family instead of clearly improving distinct third-family coverage.
- The promotion bar was explicit: `v1.4` needed to be not just viable, but clearly better enough to justify becoming the next default path. It did not clear that bar.

### What remains promising about slot-grounded drafting
- Slot-grounded structure still looks promising as architectural evidence.
- The mocked checkpoints suggest explicit grounded slots can preserve mechanism structure earlier than free drafting alone.
- The live 2008 probe showed meaningful evidence-utilization gains and preserved OTC derivatives, which suggests the idea may still matter as input to a future design step even though this branch should not be promoted as-is.

### Recurring operational issue observed in the live probe
- The focused live `v1.4` 2008 probe completed, but artifacts were written under `v0_live_baseline_001d` instead of the requested `v1_4_2008_probe_001` directory.
- Treat this as a recurring artifact-routing / output-dir bug in the live demo path.
- It is recorded here as an operational issue only. It is not being fixed in this freeze step.

### Explicit status
- Frozen historical baseline:
  - [v0_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- Exploratory only, not promoted:
  - [v1_1-grounded-selection-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_1-grounded-selection-architecture.md)
  - [v1_2-mechanism-bundling-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_2-mechanism-bundling-architecture.md)
  - [v1_3-mechanism-sketching-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_3-mechanism-sketching-architecture.md)
  - [v1_4-slot-grounded-drafting-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_4-slot-grounded-drafting-architecture.md)
  - [v1_4_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_4_2008_probe_001.md)

### What should happen next instead of more v1.4 tuning
- Do not continue narrow `v1.4` tuning by default.
- Keep `v1-minimal` as the active runtime comparison point.
- Treat `v1.1`, `v1.2`, `v1.3`, and `v1.4` as design evidence, not as the default implementation queue.
- Start the next phase with a new consciously scoped architecture-design step that uses all four exploratory branches as evidence rather than continuing any one of them directly.
