## Handoff: v1 Selector Support Sufficiency

### What was done
- Tightened `ClaimSelector` so clean direct-causal claims are penalized when
  their support is too thin for the event-level wording.
- Added explicit support-sufficiency tracking:
  - claim/support lexical overlap
  - goal-event/support overlap
  - support-sufficiency penalty for thin single-source event-linkage
- Added same-family suppression so a weakly supported mechanism claim loses to a
  better-supported same-family alternative when available.
- Added focused selector and deliberation tests for:
  - better-supported same-family securitization variants
  - preservation of exact-target fidelity
  - preservation of sharper OTC-derivatives-style claims
  - preservation of distinct supported mechanisms
- Validated with `uv run ruff check ...` and `uv run pytest`.

### What was NOT done
- No live reruns.
- No provider changes.
- No schema or orchestration changes.

### Decisions made
- Kept the fix inside the deterministic selector.
- Treated support sufficiency as a stronger gating signal, but only when the
  claim’s event-level linkage is thin enough to be suspicious.
- Narrowed the new event-linkage penalty so it does not punish strong
  mechanism-specific claims like OTC derivatives that have rich support but do
  not restate the full event phrase.

### Open questions
- Whether the live 2008 probe now preserves the OTC-derivatives gain from `010`
  while restoring a better-supported securitization claim.
- Whether the selector should ever return fewer than 3 claims when the third
  claim is too thin, or whether the better fix is stronger same-family fallback
  from candidate generation.

### Suggested next steps
1. Rerun only the focused live 2008 probe.
2. Compare directly against `v1_2008_probe_010`.
3. If groundedness recovers without losing the target-event and OTC gains,
   consider the full 3-question v1-minimal rerun.
