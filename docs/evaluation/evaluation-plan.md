# Evaluation Plan

> See also: [benchmarks.md](benchmarks.md) · [PROJECT_DOSSIER.md § Experimental Methodology](../../PROJECT_DOSSIER.md#12-experimental-methodology) · [experiment templates](../../experiments/templates/)

## Principles

1. Define metrics before implementing features
2. Evaluate components individually AND end-to-end
3. Track failure modes, not just aggregate scores
4. Human evaluation is the gold standard; automate where possible
5. Negative results are results — log them

## Evaluation Dimensions

### Factual Accuracy
- Are claims in the output factually correct?
- **Metric:** precision and recall against ground-truth fact sets
- **Method:** human annotation on sample, automated spot-checks via `verification`

### Completeness
- Does the output cover the key aspects of the research question?
- **Metric:** coverage of ground-truth topic facets
- **Method:** human evaluation with topic rubric

### Groundedness
- Is every claim backed by collected evidence?
- **Metric:** v0: % of claims with `VerificationResult` verdict `supported`; Phase 2+: % of claims with valid `CitationRecord` links
- **Method:** v0: automated check via `verification`; Phase 2+: automated check via `grounding`

### Citation Quality
- Are citations accurate — does the evidence actually support the claim?
- **Metric:** citation precision (% of `CitationRecord`s where `strength` ≠ `contradicts`)
- **Method:** human evaluation + automated retrieval check
- **Phase:** Phase 2+

### Plan Quality (component-level)
- Is the `ResearchPlan` well-structured and comprehensive?
- **Metric:** task coverage, logical ordering, absence of redundant `PlanStep`s
- **Method:** human evaluation of plans on sample tasks

### Memory Fidelity (component-level)
- Does compressed memory retain information needed for downstream tasks?
- **Metric:** downstream task performance with compressed vs. full context
- **Method:** ablation study — see [ablation_template.md](../../experiments/templates/ablation_template.md)

## Evaluation Cadence

| Phase | What to evaluate | Related hypothesis |
|-------|------------------|--------------------|
| Phase 1 | Plan quality, basic end-to-end output, groundedness via `VerificationResult` | H-001 |
| Phase 2 | Groundedness, citation quality, verification effectiveness | H-003, H-004 |
| Phase 3 | Deliberation quality, parallel execution efficiency | H-005 |
| Phase 4 | Full benchmark suite, ablations, error analysis | H-002, all |

## Open Questions

- What benchmark tasks to start with: see [benchmarks.md](benchmarks.md) and [OQ-E1](../research/open-questions.md).
- How to evaluate intermediate steps vs. end-to-end: see [OQ-E2](../research/open-questions.md).
