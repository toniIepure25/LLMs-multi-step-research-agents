# v1.4 Slot-Grounded Drafting Plan

> Architecture proposal: [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](../docs/architecture/v1_4-slot-grounded-drafting-architecture.md)
> Active comparison point: [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md) · [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md) · [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md)

## Goal

Implement the smallest slot-grounded drafting step beyond the active
v1-minimal baseline so the live path is less sensitive to:

- candidate-generation variability
- wording drift between intermediate structure and final claims
- support-attribution brittleness on freeform claim text
- diversity/completeness collapse under thin evidence

without redesigning orchestration, providers, public schemas, or verification.

## Build Order

1. Add an internal `MechanismSlot` helper in `deliberation`
   - keep it local first
   - avoid schema changes unless they become unavoidable

2. Implement deterministic `MechanismSlotBuilder`
   - input: `list[EvidenceItem]`, optional goal / question text
   - output: a small bounded slot set
   - each slot should include:
     - `slot_id`
     - mechanism family / canonical label
     - supporting evidence IDs
     - compact grounded rationale
     - target-event anchor
     - light deterministic diversity or confidence metadata

3. Teach `SimpleSynthesizer` to draft from slots rather than rediscovering mechanisms from the full flat evidence pool
   - keep the external `deliberate(...)` contract stable
   - preserve direct-causal phrasing expectations
   - keep slot count bounded for the current live budget

4. Keep `ClaimSelector` mostly stable in the first pass
   - allow it to consume slot-grounded drafted claims and existing signals
   - avoid a broad selector rewrite unless mocked tests prove it is necessary

5. Add mocked end-to-end coverage before any live rerun
   - 2008 mechanism-retention regression
   - Great Depression diversity/completeness regression
   - dot-com cleanliness preservation

6. Run focused live probes only after mocked coverage passes
   - first 2008
   - then Great Depression
   - then dot-com only if the earlier probes are viable

7. Run a full Tier 1 comparison only if the focused probes are stable and at least one shows a clear structural gain

## Dependencies

- current v1-minimal candidate-generation and selection path
- current `DecisionPacket` and verification contracts
- optional reuse of existing exploratory helpers such as `MechanismBundler` or `MechanismSketcher`, but only as internal implementation support
- no provider changes
- no orchestration changes
- no public schema changes

## Acceptance Criteria

Implementation is acceptable for focused live probing if:

- every slot has explicit supporting evidence IDs
- every slot has an explicit target-event anchor
- slot count is small and bounded
- drafted claims remain short, direct-causal, and evidence-valid
- mocked regressions show healthier mechanism preservation than a flat-evidence or sketch-only path in thin/noisy cases
- existing v1-minimal and exploratory tests still pass

Implementation is promising enough for a first full Tier 1 comparison only if:

- focused 2008 probe shows no regression in claim count or groundedness
- focused 2008 probe preserves an explicit OTC-derivatives or equally strong 2008 mechanism family when supported
- focused Great Depression probe shows equal or better mechanism diversity than the active v1-minimal behavior
- focused dot-com probe preserves clean retrieval behavior and does not regress mechanism organization

## First Mocked Tests To Write

1. Unit test for `MechanismSlotBuilder` output shape and invariants:
   - slot label
   - supporting evidence IDs
   - grounded rationale
   - target-event anchor
   - bounded slot count

2. Mocked 2008 slot-preservation regression:
   - thin/noisy evidence still produces three distinct grounded slots
   - securitization / mortgage-backed / subprime family
   - OTC derivatives / deregulation family
   - one additional supported family

3. End-to-end mocked 2008 drafting regression:
   - slot-grounded drafting preserves three direct-causal final claims
   - drafted claims keep slot evidence IDs and target-event anchor
   - the path does not collapse to two claims

4. Mocked Great Depression diversity regression:
   - slot set preserves stock crash, trade/protectionism, and monetary/banking families as distinct structures

5. Mocked dot-com cleanliness regression:
   - slot set preserves speculation, overvaluation, and regulation when supported
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
- mechanism-family fidelity
- target-event anchoring
- support organization across final claims
- whether wording drift or family-loss regressions appeared

## Explicit Non-Goals

- full grounding layer activation
- `CitationRecord` rollout
- debate or multi-perspective reasoning
- re-planning
- parallel orchestration
- verification redesign
- broad operational hardening beyond narrow bug fixes needed to complete focused probes

## Recommended First Coding Task

Implement a local `MechanismSlot` helper plus a deterministic
`MechanismSlotBuilder` inside `deliberation`, and add one mocked thin-2008
regression proving that three distinct grounded slots are preserved before final
claim wording.
