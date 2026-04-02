## Handoff: v1 Selector Same-Family Umbrella Suppression

### What was done
- Tightened `ClaimSelector` so broad same-family umbrella claims are skipped
  during final greedy selection when a sharper supported same-family mechanism
  claim has already been selected for the same event.
- Added lightweight family-token normalization so wording drift like
  `deregulated` vs `deregulation` still compares as the same mechanism family.
- Added focused tests covering:
  - broad deregulation umbrella claim vs sharper OTC-derivatives claim
  - inflected same-family wording (`deregulated` vs `deregulation`)
  - preservation of distinct mechanisms
  - continued target-event fidelity and support-sufficiency behavior
- Validated with `uv run ruff check ...` and `uv run pytest`.

### What was NOT done
- No live reruns.
- No provider changes.
- No schema or orchestration changes.

### Decisions made
- Kept the fix entirely inside the deterministic selector.
- Solved the final same-family issue at the greedy selection stage instead of
  by only increasing score penalties, because the broader claim could still be
  added later simply because there was room left in the top 3.

### Open questions
- Whether the live 2008 probe now drops the broad deregulation umbrella claim
  while preserving groundedness and the sharpened OTC claim.
- Whether evidence utilization improves once that redundant broad claim no
  longer consumes a final slot.

### Suggested next steps
1. Rerun only the focused live 2008 probe.
2. Compare directly against `v1_2008_probe_011`.
3. If the broad umbrella claim stays gone and groundedness remains healthy,
   consider the full 3-question v1-minimal rerun.
