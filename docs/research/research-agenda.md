# Research Agenda

> See also: [hypotheses.md](hypotheses.md) · [open-questions.md](open-questions.md) · [PROJECT_DOSSIER.md § Research Hypotheses](../../PROJECT_DOSSIER.md#8-research-hypotheses)

## Central Research Question

**How can we build a multi-step research agent that produces reliably grounded, verifiable outputs by combining LLM reasoning with structured memory and symbolic verification?**

## Research Threads

Each thread maps to one or more layers in the architecture ([system-overview.md](../architecture/system-overview.md)).

### RT-1: Plan Decomposition Quality → `planning`
How should a research goal be decomposed into sub-tasks? What granularity yields the best results? How do we measure plan quality independently of execution quality?

Related: H-001 in [hypotheses.md](hypotheses.md), OQ-A1 in [open-questions.md](open-questions.md)

### RT-2: Memory Architecture → `memory`
What memory compression strategies preserve the most useful signal? How should working memory capacity be bounded? What retrieval strategies work best for research contexts?

Related: H-002 in [hypotheses.md](hypotheses.md), OQ-M1/M2/M3 in [open-questions.md](open-questions.md)

### RT-3: Evidence Grounding → `grounding`
How should evidence be normalized and structured for downstream verification? What knowledge representation (triples, property graphs, flat records) best supports claim checking?

Related: H-004 in [hypotheses.md](hypotheses.md), OQ-A2 in [open-questions.md](open-questions.md)

### RT-4: Verification Effectiveness → `verification`
Which verification strategies catch the most errors? How do we balance thoroughness against cost? Can verification be made reliable enough to trust?

Related: H-003 in [hypotheses.md](hypotheses.md), OQ-V1/V2/V3 in [open-questions.md](open-questions.md)

### RT-5: Deliberation Strategies → `deliberation`
Does multi-perspective reasoning improve output quality? How should conflicts be surfaced and resolved?

Related: H-005 in [hypotheses.md](hypotheses.md)

### RT-6: Parallel Execution → `execution`, `orchestration`
How much speedup does parallel execution provide? What scheduling strategies minimize wasted work?

Related: OQ-A3 in [open-questions.md](open-questions.md)

### RT-7: Failure Modes → all layers
What are the systematic failure modes of multi-step research agents? How do errors propagate through the pipeline? Which failures are recoverable?

Related: [evaluation-plan.md](../evaluation/evaluation-plan.md), [error_analysis_template.md](../../experiments/templates/error_analysis_template.md)

## Priority Order

| Phase | Research threads | Why |
|-------|-----------------|-----|
| Phase 1 | RT-1 (planning), RT-2 (memory) | Foundational — everything else depends on these |
| Phase 2 | RT-3 (grounding), RT-4 (verification) | Core differentiators — grounding and verification |
| Phase 3 | RT-5 (deliberation), RT-6 (parallelism) | Advanced capabilities |
| Ongoing | RT-7 (failure modes) | Informs all other threads |
