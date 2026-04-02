## Handoff: v1 Diversity Hardening

### What was done
- Diagnosed the latest Great Depression failure as a selector-side diversity gap: the final set could keep three supported claims that all reused the same single broad evidence source.
- Added a narrow support-diversity deferral rule in `asar/deliberation/claim_selector.py`.
- The selector now defers a single-source claim that adds no new supporting evidence when a comparably strong, distinct-family candidate with new support evidence is still available.
- Added a second-pass fallback so deferred claims can still fill the set if diversity alternatives run out.
- Added regression tests for Great Depression diversity at both selector and end-to-end deliberation levels.

### What was NOT done
- No live reruns were performed.
- No provider, schema, verification, or orchestration changes were made.
- No broad selector rewrite was made.

### Decisions made
- Kept the fix in the selector because the latest failure was not missing retrieval or missing claim count; it was poor final-set composition.
- Targeted repeated reuse of one already-used single support source, since that was the actual brittle pattern in `v1_great_depression_probe_015`.
- Kept the rule conservative by only deferring when a distinct-family candidate with new support evidence is still competitive.

### Open questions
- Whether this selector diversity pressure is enough to keep stronger Great Depression families alive in live runs.
- Whether the same rule also helps future 2008 runs avoid broad-source concentration without hurting support quality.

### Suggested next steps
1. Rerun only the focused Great Depression live probe and compare it directly against `v1_great_depression_probe_015`.
2. If Great Depression now keeps 3 supported and more diverse families, rerun the focused 2008 probe again because that remains unstable.
3. Only if both focused probes look healthier, rerun the full 3-question v1 Tier 1 set.
