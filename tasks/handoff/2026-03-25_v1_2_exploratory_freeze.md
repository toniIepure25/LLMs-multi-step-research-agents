## Handoff: v1.2 Exploratory Freeze

### What v1.2 attempted to add
- A local deterministic `MechanismBundler` inside `deliberation`.
- Bundled mechanism-family evidence slices before final claim generation and selection.
- A minimal upstream stabilization step without changing providers, orchestration, schemas, or the broader pipeline shape.

### What worked in mocked checkpoints
- Bundle-shape and thin-evidence mechanism-bundling regressions passed.
- End-to-end mocked thin-2008 coverage showed that bundled slices could preserve healthier mechanism-family coverage before final packaging.
- The exploration produced meaningful evidence that explicit mechanism bundling can help stabilize candidate generation under thin or noisy evidence.

### What worked in focused live probing
- [v1_2_2008_probe_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_2008_probe_002.md) completed successfully after narrow provider-timeout hardening and showed that `v1.2` was viable in live conditions:
  - `3` claims
  - `groundedness=1.0`
  - healthy completion and preserved OTC derivatives
- [v1_2_great_depression_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_great_depression_probe_001.md) showed the strongest positive signal for the idea:
  - `3` claims
  - `groundedness=1.0`
  - a meaningful mechanism-diversity gain through the return of a monetary / banking family
- [v1_2_dotcom_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_dotcom_probe_001.md) stayed complete and grounded:
  - `3` claims
  - `groundedness=1.0`
  - wrong-domain crash / vehicle noise stayed gone

### What failed to clear the promotion bar
- `v1.2` did not show clear overall superiority to the active v1-minimal baseline.
- The focused live 2008 result was viable but mixed, not clearly better than the active v1-minimal 2008 behavior.
- The focused live Great Depression result was promising on diversity, but still not a clean overall win on utilization or wording.
- The focused live dot-com result did not clearly improve mechanism organization and lost the cleaner regulation-family behavior seen in stronger prior runs.
- The promotion bar was explicit: `v1.2` needed to show a clearer overall advantage than [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md). It did not clear that bar.

### What remains promising about mechanism bundling
- Mechanism bundling still looks promising as an upstream stabilization idea.
- The mocked checkpoints suggest it can improve thin-evidence mechanism coverage before final phrasing.
- The live Great Depression result is meaningful evidence that explicit bundle structure may help recover missing mechanism families in cases where v1-minimal undercovers them.
- The idea remains useful as input to a future design step, even though this specific `v1.2` branch should not be promoted as-is.

### Explicit status
- Frozen historical baseline:
  - [v0_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- Exploratory only, not promoted:
  - [v1_1-grounded-selection-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_1-grounded-selection-architecture.md)
  - [v1_2-mechanism-bundling-architecture.md](/home/tonystark/Desktop/multi-step-agent-research/docs/architecture/v1_2-mechanism-bundling-architecture.md)
  - [v1_2_2008_probe_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_2008_probe_002.md)
  - [v1_2_great_depression_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_great_depression_probe_001.md)
  - [v1_2_dotcom_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_dotcom_probe_001.md)

### What should happen next instead of more v1.2 tuning
- Do not continue narrow `v1.2` tuning by default.
- Keep `v1-minimal` as the active runtime comparison point.
- Treat `v1.1` and `v1.2` as design evidence, not as the default implementation queue.
- Start the next phase with a new consciously scoped architecture-design step that uses the exploratory results as inputs rather than continuing either exploratory branch directly.

### Follow-up status
- Subsequent v1.3 mechanism-sketching exploration also remained exploratory and was not promoted.
- Subsequent v1.4 slot-grounded drafting exploration also remained exploratory and was not promoted.
- `v1_tier1_eval_set_004` remains the active experimental baseline after v1.1, v1.2, v1.3, and v1.4.
- See [2026-03-26_v1_3_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) for the v1.3 freeze rationale and the artifact-routing/output-dir bug note from the focused live 2008 probe.
- See [2026-03-31_v1_4_exploratory_freeze.md](/home/tonystark/Desktop/multi-step-agent-research/tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md) for the v1.4 freeze rationale and the recurring artifact-routing/output-dir bug note from the focused live 2008 probe.
