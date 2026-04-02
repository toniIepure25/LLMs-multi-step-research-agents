# v1 Minimal Plan

> Baseline to beat: [experiments/notes/v0_tier1_eval_set_004.md](../experiments/notes/v0_tier1_eval_set_004.md)
> Architecture reference: [docs/architecture/v1-minimal-architecture.md](../docs/architecture/v1-minimal-architecture.md)

This plan covers the smallest implementation step beyond frozen v0. It does not
include grounding, re-planning, debate, parallelism, or benchmark expansion.

## Goal

Add a support-aware claim selection stage after candidate claim generation so
claim generation and claim selection are no longer the same step.

## Build Order

| # | What | Depends on | Acceptance checkpoint |
|---|------|------------|-----------------------|
| 1 | Define the internal candidate-claim shape and generation output contract | frozen v0 docs | candidate set can represent more than 3 draft claims with evidence links |
| 2 | Adapt current deliberation generation path to emit candidate claims instead of final pruning | step 1 | generation tests pass without selector logic |
| 3 | Implement `ClaimSelector` with deterministic support/relevance/diversity scoring | step 2 | selector chooses stable claims in mocked 2008-style cases |
| 4 | Wire generation -> selection -> `DecisionPacket` inside deliberation/orchestration | steps 2–3 | end-to-end mocked pipeline passes |
| 5 | Run focused live 2008 probe against `v0_tier1_eval_set_004` | step 4 | direct causal phrasing improves without groundedness regression |
| 6 | If stable, rerun the 3-question Tier 1 live set and compare against `004` | step 5 | determine whether v1 minimal beats the frozen v0 baseline |

## Dependencies

- Keep the existing planning, execution, memory, verification, and evaluation layers intact
- Preserve current schemas unless a tiny new typed structure is strictly needed
- Reuse existing v0 live eval artifacts as comparison targets

## Acceptance Criteria

v1 minimal is acceptable only if all of the following hold:

- claim generation and claim selection are separate steps
- the selector prefers stronger support over elegant but weakly supported specificity
- distinct supported mechanisms are not collapsed unnecessarily
- direct causal phrasing remains strong
- groundedness does not regress versus `v0_tier1_eval_set_004`
- dot-com cleanliness from the frozen v0 baseline does not regress

## What To Test First

Test these before any live run:

1. Candidate generation returns multiple plausible claims for a single evidence set
2. Selector prefers stronger supported claims over weaker over-specific claims
3. Selector keeps distinct supported mechanisms when both are relevant
4. Selector removes duplicates without collapsing meaningfully different claims
5. Existing off-question protections still pass

## First Live Comparison Target

The first live validation should be only:

- `What were the main causes of the 2008 financial crisis?`

Why first:

- it is the narrowest known structural failure case
- it exposes the tension between support quality, claim count, and direct causal phrasing
- it is a better early signal than rerunning the whole Tier 1 set immediately

## What To Compare Against `v0_tier1_eval_set_004`

For the focused 2008 probe:

- final claim wording
- groundedness
- claim count
- evidence utilization
- whether securitization / derivatives / Glass-Steagall / monetary-policy claims remain distinct when supported
- whether copied/snippet-like wording remains reduced

For the full 3-question rerun, if reached:

- 2008 claim stability
- Great Depression claim usefulness
- dot-com retrieval cleanliness
- overall groundedness
- evidence utilization

## Explicitly Out Of Scope

- grounding or citation architecture
- re-planning loops
- parallel execution
- debate or multi-agent deliberation
- advanced memory
- broad verification redesign
- benchmark expansion
