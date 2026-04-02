# v1.5 Mechanism Slate Selection Plan

> Architecture proposal: [docs/architecture/v1_5-mechanism-slate-selection-architecture.md](../docs/architecture/v1_5-mechanism-slate-selection-architecture.md)
> Active comparison point: [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md) · [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md) · [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md) · [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md)

## Goal

Implement the smallest set-composition step beyond the active v1-minimal
baseline so the live path is less sensitive to:

- same-family duplication in the final set
- third-mechanism loss under thin or noisy evidence
- brittle per-claim scoring after the candidate surface has already drifted
- wording drift between structured intermediate representations and the final answer

without redesigning orchestration, providers, public schemas, or verification.

## Build Order

1. Add an internal `MechanismSlateEntry` helper and a bounded `MechanismSlate`
   - keep both local first
   - avoid schema changes unless they become unavoidable

2. Implement deterministic mechanism-family candidate extraction
   - input: `list[EvidenceItem]`, optional goal / question text
   - output: a small pool of candidate mechanism entries
   - candidate metadata should include:
     - canonical family label
     - target-event anchor
     - supporting evidence IDs
     - compact grounded rationale
     - support sufficiency indicators
     - duplication / diversity metadata

3. Implement deterministic `MechanismSlateSelector`
   - choose a small bounded slate at the set level, not independently per entry
   - prefer:
     - support sufficiency
     - target-event fidelity
     - family distinctness
     - healthy three-mechanism composition when evidence supports it
   - explicitly penalize same-family duplication

4. Teach `SimpleSynthesizer` to draft from a selected slate rather than rediscovering the final set from flat evidence or loosely structured intermediate objects
   - keep the external `deliberate(...)` contract stable
   - keep prompt size bounded for the current live budget
   - preserve short direct-causal wording expectations

5. Keep `ClaimSelector` mostly stable in the first pass
   - allow it to consume slate-grounded drafted claims and existing signals
   - avoid a broad selector rewrite unless mocked tests prove it is necessary

6. Add mocked end-to-end coverage before any live rerun
   - 2008 anti-duplication regression
   - Great Depression diversity-preservation regression
   - dot-com cleanliness and coherence regression

7. Run focused live probes only after mocked coverage passes
   - first 2008
   - then Great Depression
   - then dot-com only if the earlier probes are viable

8. Run a full Tier 1 comparison only if the focused probes are stable and at least one shows a clear structural gain

## Dependencies

- current v1-minimal candidate-generation and selection path
- current `DecisionPacket` and verification contracts
- optional reuse of existing exploratory helpers such as bundlers, sketchers, or slot builders, but only as internal implementation support
- no provider changes
- no orchestration changes
- no public schema changes

## Acceptance Criteria

Implementation is acceptable for focused live probing if:

- every slate entry has explicit supporting evidence IDs
- every slate entry has an explicit target-event anchor
- slate size is small and bounded
- slate selection is explicitly diversity-aware at the set level
- drafted claims remain short, direct-causal, and evidence-valid
- mocked regressions show healthier set composition than per-claim or slot-only drafting in thin/noisy cases
- existing v1-minimal and exploratory tests still pass

Implementation is promising enough for a first full Tier 1 comparison only if:

- focused 2008 probe shows no regression in claim count or groundedness
- focused 2008 probe avoids same-family duplication and preserves a clearer third supported mechanism
- focused Great Depression probe shows equal or better mechanism diversity than the active v1-minimal behavior
- focused dot-com probe preserves clean retrieval behavior and does not regress mechanism organization

## First Mocked Tests To Write

1. Unit test for `MechanismSlateSelector` output shape and invariants:
   - bounded slate size
   - explicit family labels
   - supporting evidence IDs
   - target-event anchors
   - diversity metadata

2. Mocked 2008 anti-duplication regression:
   - evidence supports securitization, OTC derivatives, and a third distinct family
   - two nearby housing-finance entries compete
   - the final slate keeps only one housing-finance family entry and preserves the third mechanism

3. End-to-end mocked 2008 slate-grounded drafting regression:
   - selected slate drafts three direct-causal final claims
   - drafted claims keep slate evidence IDs and target-event anchors
   - the path does not collapse to two claims and does not duplicate the same family

4. Mocked Great Depression composition regression:
   - slate preserves stock crash, trade/protectionism, and monetary/banking families as distinct structures when supported

5. Mocked dot-com cleanliness regression:
   - slate preserves speculation, overvaluation, and regulation when supported
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
- same-family duplication rate in the final set
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

Implement a local `MechanismSlateEntry` / `MechanismSlate` helper plus a
deterministic `MechanismSlateSelector` inside `deliberation`, and add one
mocked thin-2008 regression proving that a selected slate preserves three
distinct supported mechanisms without same-family duplication before final
claim wording.
