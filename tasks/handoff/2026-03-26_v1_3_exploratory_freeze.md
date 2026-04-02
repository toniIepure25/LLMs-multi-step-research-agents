## Handoff: v1.3 Exploratory Freeze

### What v1.3 attempted to add
- A local deterministic `MechanismSketcher` inside `deliberation`.
- Compact evidence-grounded mechanism sketches before final claim wording and selection.
- A narrow sketch-first deliberation step without changing providers, schemas, orchestration, or the broader runtime shape.

### What worked in mocked checkpoints
- Thin-2008 sketch-preservation regressions passed.
- End-to-end mocked sketch-first deliberation coverage passed.
- The exploration produced useful evidence that preserving mechanism structure earlier than final claim wording can help stabilize thin evidence cases.

### What worked in the focused live 2008 probe
- [v1_3_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_3_2008_probe_001.md) completed successfully in live conditions.
- Core metrics were healthy:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
  - materially stronger evidence utilization than the active v1-minimal 2008 baseline
- The result showed that sketch-first deliberation is viable enough to evaluate in real conditions.

### What failed to clear the promotion bar
- `v1.3` did not show clear overall superiority to [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md).
- The mechanism mix was weaker than the strongest v1-minimal 2008 behavior.
- The explicit OTC-derivatives family disappeared.
- The lead deregulation mechanism broadened relative to the better v1-minimal 2008 runs.
- The promotion bar was explicit: `v1.3` needed to be not just viable, but clearly better enough to justify becoming the next default path. It did not clear that bar.

### What remains promising about mechanism sketching
- Sketch-first structure still looks promising as architectural evidence.
- The mocked checkpoints suggest earlier mechanism preservation can help stabilize thin evidence before final wording.
- The live 2008 run showed meaningful evidence-utilization gains, which suggests the idea may still matter as input to a future design step even though this branch should not be promoted as-is.

### Operational issue observed in the live probe
- The focused live `v1.3` 2008 probe completed, but artifacts were written under `v0_live_baseline_001` instead of the requested `v1_3_2008_probe_001` directory.
- Treat this as an artifact-routing / output-dir bug in the live demo path.
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
  - [v1_3_2008_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_3_2008_probe_001.md)

### What should happen next instead of more v1.3 tuning
- Do not continue narrow `v1.3` tuning by default.
- Keep `v1-minimal` as the active runtime comparison point.
- Treat `v1.1`, `v1.2`, and `v1.3` as design evidence, not as the default implementation queue.
- Start the next phase with a new consciously scoped architecture-design step that uses the three exploratory branches as evidence rather than continuing any one of them directly.

### Follow-up status
- Subsequent v1.4 slot-grounded drafting exploration also remained exploratory and was not promoted.
- `v1_tier1_eval_set_004` remains the active experimental baseline after v1.1, v1.2, v1.3, and v1.4.
- See [2026-03-31_v1_4_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md) for the v1.4 freeze rationale and the recurring artifact-routing/output-dir bug note from the focused live 2008 probe.
