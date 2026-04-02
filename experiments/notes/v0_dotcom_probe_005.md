# v0 Dotcom Probe 005

## Scope

Focused live rerun of the dot-com crash question after the domain-anchor hardening pass across orchestration + execution.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used as prior v0 live runs
- Goal: determine whether the technology-step wrong-domain `technology + crash` noise from `v0_dotcom_probe_004` is actually removed

## Question

`What were the main causes of the dot-com crash?`

## Command Used

```bash
set -a && source .secrets && \
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the dot-com crash?" \
  --mode live \
  --output-dir experiments/runs/v0_dotcom_probe_005
```

## New Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_005/20260318T222107Z_what-were-the-main-causes-of-the-dot-com_experiment_903255ab1070/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_005/20260318T222107Z_what-were-the-main-causes-of-the-dot-com_experiment_903255ab1070/experiment.json`

## Reference Comparison Target

`v0_dotcom_probe_004`

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_004/20260318T214137Z_what-were-the-main-causes-of-the-dot-com_experiment_d3d65b78487f/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_004/20260318T214137Z_what-were-the-main-causes-of-the-dot-com_experiment_d3d65b78487f/experiment.json`

## Before / After vs `004`

### Technology Step Query

`004`
- `Analyze the role of technological over-saturation in the crash`

`005`
- `Analyze the role of technological over-saturation in the crash about What were the main causes of the dot-com crash?`

Assessment:
- The technology step query in `005` stayed properly anchored to the original dot-com goal.

### Technology Step Survivors

`004`
- `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
- `Characterizing Technology's Influence on Distractive Behavior at ...`

`005`
- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`

Assessment:
- The wrong-domain car-crash / vehicle-safety / distractive-driving / intersection-style noise is gone from the technology step in `005`.
- All surviving technology-step results are at least topically aligned with the dot-com crash.

### Metrics

- evidence count: `11 -> 11`
- evidence utilization: `0.4545 -> 0.2727`
- groundedness: `1.0 -> 1.0`
- plan coverage: `1.0 -> 1.0`
- verification: `supported=3 -> supported=3`

## Focused Assessment Of The Targeted Failure Mode

The targeted failure mode is fixed for this probe.

- In `004`, the technology step still admitted clearly wrong-domain traffic-safety material.
- In `005`, the same step used a goal-anchored query and returned only dot-com-aligned sources.
- This is a real improvement, not just acceptable variance.

## Final Claims

`004`
- `Regulatory shortcomings contributed to the crisis.`
- `Speculation in dot-com businesses caused a stock market bubble.`
- `Artificially low interest rates distorted market signals and led to an unsustainable boom.`

`005`
- `The crash was caused by a number of factors, including overvaluation of tech companies.`
- `A stock market bubble that was caused by speculation in dotcom or internet-based businesses from 1995 to 2000.`
- `The dot-com crash was caused by overvaluation of tech companies and lack of regulation.`

## Claim Quality Assessment

- The final claims stayed on-question.
- Groundedness remained acceptable at `1.0`, and all 3 claims were still verified as `supported`.
- Claim specificity is mixed:
  - better topical alignment than `004`
  - but more copied/generic phrasing than ideal, especially in the first two claims
- This looks like residual synthesis/provider noise rather than a new regression in execution relevance.

## Overall Judgment

### Did the technology step query stay properly anchored to the dot-com goal?

Yes.

### Did the technology step finally drop the wrong-domain noise?

Yes.

### Did evidence quality improve?

Yes for the targeted failure mode.

- The technology step evidence is now domain-correct.
- However, overall evidence utilization got worse because the final claim set still used a relatively small subset of the evidence.

### Did the final claims stay on-question?

Yes.

### Did groundedness remain acceptable?

Yes.

### Is this fix strong enough to justify rerunning the full 3-question set?

Yes.

The targeted dot-com retrieval failure appears fixed in this focused live probe, and no major regression in pipeline health appeared.
