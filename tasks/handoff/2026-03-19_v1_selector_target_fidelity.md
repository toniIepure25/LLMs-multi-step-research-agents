## Handoff: v1 Selector Target Fidelity And Mechanism Diversity

### What was done
- Tightened `ClaimSelector` to score exact goal-event fidelity explicitly.
- Added a penalty path for broader same-family mechanism claims when a sharper
  supported variant exists for the same target event.
- Added a guard that suppresses lower-fidelity alternate-target claims when a
  better same-family claim is available.
- Added focused selector and deliberation tests covering:
  - exact target-event preference over related alternate targets
  - sharper OTC-derivatives-style mechanism preference over broad deregulation
  - preservation of distinct supported mechanisms
- Validated with `uv run ruff check ...` and `uv run pytest`.

### What was NOT done
- No live reruns.
- No provider changes.
- No schema or orchestration redesign.

### Decisions made
- Kept the fix entirely inside the deterministic selector.
- Treated target-event fidelity as a first-class criterion, but only suppressed
  alternate-target claims when a better same-family candidate exists so valid
  causal precursor claims can still survive.

### Open questions
- Whether the live 2008 probe now replaces the `housing crisis` drift with a
  better exact-target claim.
- Whether the selector now preserves a sharper OTC-derivatives claim in live
  conditions when the candidate generator emits both broad and sharp variants.

### Suggested next steps
1. Rerun only the focused live 2008 probe.
2. Compare directly against `v1_2008_probe_009`.
3. Only if target fidelity and mechanism diversity improve in that probe,
   consider the full 3-question v1-minimal rerun.
