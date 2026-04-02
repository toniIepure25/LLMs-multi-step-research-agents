# v1.3 Mechanism Sketching Plan

## Goal

Implement the smallest evidence-grounded mechanism sketching step beyond the
active v1-minimal baseline without changing orchestration, providers, or public
schemas.

Reference architecture:

- [docs/architecture/v1_3-mechanism-sketching-architecture.md](../docs/architecture/v1_3-mechanism-sketching-architecture.md)

Active comparison point:

- [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)

Exploratory evidence:

- [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md)
- [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md)

## Build Order

1. Add a local internal `MechanismSketch` helper in `deliberation`.
2. Implement a narrow `MechanismSketcher` that emits a small sketch set from evidence, with explicit supporting evidence IDs.
3. Integrate sketch-first prompting into `SimpleSynthesizer` while keeping the external `DecisionPacket` path unchanged.
4. Keep `ClaimSelector` stable in the first pass unless a tiny compatibility adjustment is clearly necessary.
5. Add mocked end-to-end regressions for 2008, Great Depression, and dot-com.
6. Run focused live probes only after mocked coverage passes.
7. Run a full Tier 1 comparison only if the focused probes are stable and at least one shows a clear structural gain.

## Dependencies

- existing `SimpleSynthesizer`
- existing `ClaimSelector`
- existing exploratory evidence from `SupportAttributor` and `MechanismBundler`
- no schema changes
- no provider changes
- no orchestration changes

## Acceptance Criteria

Implementation is ready for focused live probing if:

- every sketch has explicit supporting evidence IDs
- the sketch count is small and bounded
- the final `DecisionPacket` path remains schema-valid
- mocked regressions show healthier mechanism coverage than a flat evidence path in thin/noisy cases
- existing v1-minimal and exploratory tests still pass

Implementation is promising enough for a first full Tier 1 comparison only if:

- focused 2008 probe shows no regression in claim count or groundedness
- focused Great Depression probe shows equal or better mechanism diversity than the active v1-minimal behavior
- focused dot-com probe preserves clean retrieval behavior and does not regress mechanism organization

## First Mocked Tests To Write

1. Unit test for `MechanismSketcher` output shape and invariants:
   - sketch label
   - causal angle
   - supporting evidence IDs
   - bounded sketch count

2. Mocked 2008 regression:
   - thin/noisy evidence still produces three distinct mechanism sketches
   - securitization / mortgage-backed family
   - OTC derivatives / deregulation family
   - one additional supported family

3. Mocked Great Depression regression:
   - sketch set preserves stock crash, trade/protectionism, and monetary/banking families as distinct structures

4. Mocked dot-com regression:
   - sketch set preserves speculation, overvaluation, and regulation when supported
   - wrong-domain crash/vehicle noise does not appear

## First Focused Live Probes To Run

1. 2008 financial crisis
2. Great Depression
3. dot-com crash

Run them in that order. Only move to the next if the previous result is at
least viable and does not clearly regress against the active baseline.

## How To Compare Against v1-Minimal

Use [v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
as the active runtime comparison point.

For each focused live probe, compare:

- claim count
- groundedness
- evidence utilization
- direct-causal wording quality
- mechanism-family coverage
- support organization across final claims
- whether new phrasing or structure regressions appeared

## First Coding Task

Implement a local `MechanismSketch` helper plus a narrow `MechanismSketcher`
inside `deliberation`, and add one mocked thin-2008 regression proving that the
full sketch-first path preserves three distinct mechanism structures before
final claim wording.
