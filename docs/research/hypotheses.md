# Research Hypotheses

> See also: [research-agenda.md](research-agenda.md) · [open-questions.md](open-questions.md) · [experiment templates](../../experiments/templates/)

Testable hypotheses. Each should be falsifiable and connected to an experiment.

## Format

```
### H-NNN: <Title>
**Claim:** <Falsifiable statement>
**Rationale:** <Why we believe this might be true>
**Test:** <How to test — reference experiment template>
**Layer(s):** <Which layer(s) this tests>
**Status:** untested | supported | refuted | inconclusive
**Evidence:** <Link to experiment results or failed direction note>
```

---

### H-001: Structured Plans Outperform Linear Execution
**Claim:** A planner that decomposes research goals into structured sub-tasks produces higher-quality outputs than a single-pass LLM prompt, as measured by factual accuracy and completeness.
**Rationale:** Decomposition reduces the cognitive load per step and allows targeted tool use.
**Test:** Compare single-pass vs. planned execution on benchmark. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `planning`, `orchestration`
**Status:** untested
**Evidence:** —

### H-002: Memory Compression Preserves Research Utility
**Claim:** Compressed memory summaries retain sufficient information to support multi-step research without significant quality degradation (< 10% drop on downstream metrics).
**Rationale:** LLM-generated summaries can capture key facts while reducing token count by 5–10x.
**Test:** Ablation: full-context vs. compressed-context. Use [ablation_template.md](../../experiments/templates/ablation_template.md).
**Layer(s):** `memory`
**Status:** untested
**Evidence:** —

### H-003: Verification Catches Meaningful Errors
**Claim:** A separate verification layer catches at least 30% of factual errors that pass through generation unchecked.
**Rationale:** Separation of generation and verification introduces an independent check.
**Test:** Inject known errors, measure verification recall. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `verification`
**Status:** untested
**Evidence:** —

### H-004: Evidence Grounding Reduces Hallucination
**Claim:** Requiring all claims to link to `EvidenceItem`s reduces hallucination rate by at least 50% compared to ungrounded generation.
**Rationale:** Grounding forces citation, making unsupported claims structurally impossible.
**Test:** Compare grounded vs. ungrounded on hallucination benchmark. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `grounding`
**Status:** untested
**Evidence:** —

### H-005: Multi-Perspective Deliberation Improves Synthesis
**Claim:** Deliberation using multiple perspectives (advocate/critic) produces more balanced and accurate syntheses than single-perspective generation.
**Rationale:** Adversarial perspectives surface blind spots and conflicts.
**Test:** Compare single vs. multi-perspective on nuanced topics. Use [ablation_template.md](../../experiments/templates/ablation_template.md).
**Layer(s):** `deliberation`
**Status:** untested
**Evidence:** —
