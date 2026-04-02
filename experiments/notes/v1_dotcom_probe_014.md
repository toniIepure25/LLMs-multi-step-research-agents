# v1 Dot-Com Probe 014

## Scope

Focused live rerun of the dot-com crash question after the narrow
candidate-generation hardening pass for live-budget stability.

This step tests whether the leaner candidate-generation path plus the new
dot-com mechanism-family backfill improve final claim completeness under:

- `ASAR_MODEL_MODEL=llama3.1:8b`
- `ASAR_MODEL_MAX_TOKENS=512`

No full Tier 1 rerun was performed in this step.

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
  --output-dir experiments/runs/v1_dotcom_probe_014
```

## New Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_dotcom_probe_014/20260319T213937Z_what-were-the-main-causes-of-the-dot-com_experiment_dac755a333cd/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_dotcom_probe_014/20260319T213937Z_what-were-the-main-causes-of-the-dot-com_experiment_dac755a333cd/experiment.json`

## Comparison Targets

- previous v1 dot-com run: the dot-com run inside `v1_tier1_eval_set_002`
- strongest prior clean dot-com run: the dot-com run inside `v0_tier1_eval_set_004`

`v0_dotcom_probe_005` remains relevant as the focused retrieval-clean checkpoint,
but `v0_tier1_eval_set_004` is the stronger overall comparison because it kept
3 supported claims in the full live set.

## Metrics

### `v1_tier1_eval_set_002` dot-com run

- evidence count: `12`
- evidence utilization: `0.25`
- groundedness: `1.0`
- claim count: `2`
- verification: `supported=2`

### `v0_tier1_eval_set_004` dot-com run

- evidence count: `12`
- evidence utilization: `0.25`
- groundedness: `1.0`
- claim count: `3`
- verification: `supported=3`

### `v1_dotcom_probe_014`

- evidence count: `12`
- evidence utilization: `0.3333`
- groundedness: `1.0`
- claim count: `3`
- verification: `supported=3`
- plan coverage: `1.0`

## Claims

### `v1_tier1_eval_set_002`

- `Speculation in dotcom or internet-based businesses from 1995 to 2000 caused the dotcom bubble.`
- `Overvaluation of tech companies contributed to the dot-com crash.`

### `v0_tier1_eval_set_004`

- `Overvaluation of tech companies was a cause of the dot-com crash.`
- `Lack of regulation in the tech industry contributed to the dot-com crash.`
- `Speculation in dotcom or internet-based businesses caused the dot-com bubble.`

### `v1_dotcom_probe_014`

- `Overvaluation of tech companies contributed to the crash.`
- `Lack of regulation in the tech industry contributed to the crash.`
- `Speculation in dotcom businesses caused the crash.`

## Evidence Snapshot

`014` used this 4-step plan:

- `Define the scope and timeline of the dot-com crash`
- `Research the economic factors leading to the crash`
- `Analyze the role of technological over-saturation in the crash`
- `Examine the impact of regulatory failures on the crash`

Important note:

- the planner/step wording regressed to `technological over-saturation`
- but the surviving evidence stayed dot-com aligned
- the old wrong-domain crash/vehicle noise did not return

Technology-step survivors:

- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Dotcom Bubble - Overview, Characteristics, Causes`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`

Regulation-step survivors included:

- `The Dot Com Crash: Causes and Consequences - Eccuity`
- `Understanding the Dotcom Bubble: Causes, Impact, and Lessons`
- `Impact of the Dot-Com Bubble Burst - LinkedIn`

## Focused Assessment

### Did the missing third mechanism recover?

Yes.

This is the clearest improvement over `v1_tier1_eval_set_002`:

- `claim count: 2 -> 3`
- the missing regulation-style mechanism returned

The final claim set now covers:

- overvaluation
- lack of regulation
- speculation

### Did wrong-domain crash/vehicle noise stay gone?

Yes.

Even though the plan text drifted back toward `technological over-saturation`,
the actual surviving evidence remained dot-com aligned. The old car-crash /
vehicle-safety / distractive-driving style failure mode did not reappear.

### Did groundedness remain acceptable?

Yes.

`014` kept:

- `groundedness=1.0`
- `supported=3`

### Did claim wording remain direct-causal?

Mostly yes.

All 3 claims are direct causal answers. The one quality caveat is specificity:

- the claims say `the crash` instead of explicitly `the dot-com crash`
- `Speculation in dotcom businesses caused the crash.` is shorter but less precise
  than the better `v1_002` speculation wording

## Comparison Summary

### Versus the dot-com run inside `v1_tier1_eval_set_002`

`014` is clearly better:

- `claim count: 2 -> 3`
- `evidence utilization: 0.25 -> 0.3333`
- groundedness stayed `1.0`
- the missing regulation mechanism returned
- retrieval stayed clean

This is a real completeness improvement, not just acceptable variance.

### Versus the strongest prior clean run inside `v0_tier1_eval_set_004`

`014` is competitive:

- both kept `groundedness=1.0`
- both kept `claim count=3`
- both kept `supported=3`
- `014` improved evidence utilization: `0.25 -> 0.3333`

But the tradeoff is claim specificity:

- `v0_004` used more explicit target wording like `the dot-com crash`
- `014` is cleaner than the weak `v1_002` run on completeness, but slightly less
  specific in phrasing than `v0_004`

## Overall Judgment

### Did the remaining dot-com completeness issue improve?

Yes.

The missing third mechanism recovered, groundedness stayed strong, and the old
wrong-domain retrieval failure remained fixed.

### Were there regressions?

No major regression in retrieval quality or grounding.

The remaining caveat is plan/claim phrasing drift:

- the plan reverted to `technological over-saturation`
- the final claims say `the crash` instead of `the dot-com crash`

So mechanism coverage improved clearly, but phrasing still varies.

### Is v1-minimal now strong enough on both 2008 and dot-com to justify another full 3-question rerun?

Yes.

The two narrow blockers that remained after `v1_tier1_eval_set_002` now look
meaningfully improved in focused probes:

- `v1_2008_probe_014` improved 2008 stability
- `v1_dotcom_probe_014` improved dot-com completeness

That is strong enough to justify another full 3-question v1-minimal rerun.
