# Dataflow

> Parent: [system-overview.md](system-overview.md)
> See also: [component-map.md](component-map.md) · [`schemas/`](../../schemas/)

## Primary Research Pipeline

```
                        ┌──────────┐
                        │ Research  │
                        │   Goal   │
                        └────┬─────┘
                             │
                             ▼
                     ┌───────────────┐
                     │   PLANNING    │
                     │               │
                     │ Goal → Plan   │
                     └───────┬───────┘
                             │ ResearchPlan
                             ▼
                     ┌───────────────┐
                     │ ORCHESTRATION │◄─── re-plan loop
                     │               │
                     │ Dispatch &    │
                     │ Coordinate    │
                     └───┬───┬───┬───┘
                         │   │   │
            ┌────────────┘   │   └────────────┐
            ▼                ▼                ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ EXECUTION  │  │ EXECUTION  │  │ EXECUTION  │
     │ (search)   │  │ (retrieve) │  │ (parse)    │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │ EvidenceItem   │ EvidenceItem   │ EvidenceItem
           └────────┬───────┴────────┬───────┘
                    ▼                │
            ┌───────────────┐       │
            │   GROUNDING   │◄──────┘
            │               │
            │ Normalize,    │
            │ build         │
            │ CitationRecords│
            └───────┬───────┘
                    │ EvidenceItem (normalized) + CitationRecord
                    ▼
            ┌───────────────┐
            │    MEMORY     │
            │               │
            │ Store, index, │
            │ compress      │
            └───────┬───────┘
                    │ list[EvidenceItem] (retrieved)
                    ▼
            ┌───────────────┐
            │ DELIBERATION  │
            │               │
            │ Synthesize,   │
            │ critique,     │
            │ detect        │
            │ conflicts     │
            └───────┬───────┘
                    │ DecisionPacket
                    ▼
            ┌───────────────┐
            │ VERIFICATION  │
            │               │
            │ Check claims, │
            │ validate      │
            │ citations     │
            └───────┬───────┘
                    │ DecisionPacket (with verification labels)
                    ▼
            ┌───────────────┐
            │  EVALUATION   │
            │               │
            │ Score, log,   │
            │ analyze       │
            └───────┬───────┘
                    │
                    ▼
             ┌────────────┐
             │   OUTPUT    │
             │  (grounded, │
             │   cited,    │
             │   verified) │
             └─────────────┘
```

## Schema Types at Each Boundary

| Boundary | Schema(s) flowing | Defined in |
|----------|--------------------|-----------|
| Goal → planning | `str` + optional constraints | — |
| planning → orchestration | `ResearchPlan` | `schemas/research_plan.py` |
| orchestration → execution | `TaskPacket` | `schemas/task_packet.py` |
| execution → grounding | `EvidenceItem` | `schemas/evidence_item.py` |
| grounding → memory | `EvidenceItem` (normalized) + `CitationRecord` | `schemas/evidence_item.py`, `schemas/citation_record.py` |
| memory → deliberation | `list[EvidenceItem]` | `schemas/evidence_item.py` |
| deliberation → verification | `DecisionPacket` | `schemas/decision_packet.py` |
| verification → output | `DecisionPacket` (with labels) | `schemas/decision_packet.py` |

## Re-Planning Loop

Orchestration may trigger re-planning when:
1. An executor fails to produce usable evidence
2. Verification rejects a critical claim
3. Deliberation identifies an information gap
4. A task's success criteria are unmet after execution

Re-planning feeds gap analysis back to planning, which produces an amended `ResearchPlan` (with incremented `revision` field).

## Open Design Questions

- Parallel execution scheduling strategy (fan-out, priority queue, dependency-aware) — Phase 3. See [OQ-A3](../research/open-questions.md).
