# v0 Dotcom Probe 004

## Scope

Focused live rerun of the dot-com crash question after the narrow step-aware execution hardening pass.

- Architecture unchanged
- No Phase 2 features introduced
- Same live provider path used as prior v0 live runs
- Goal: determine whether the technology-step car-crash / vehicle-safety noise from `v0_tier1_eval_set_003` is actually removed

## Question

`What were the main causes of the dot-com crash?`

## Command Used

```bash
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
TAVILY_API_KEY='[redacted]' \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the dot-com crash?" \
  --mode live \
  --output-dir experiments/runs/v0_dotcom_probe_004
```

## New Artifact Paths

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_004/20260318T214137Z_what-were-the-main-causes-of-the-dot-com_experiment_d3d65b78487f/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_dotcom_probe_004/20260318T214137Z_what-were-the-main-causes-of-the-dot-com_experiment_d3d65b78487f/experiment.json`

## Reference Comparison Target

`v0_tier1_eval_set_003` dot-com run:

- `output.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/dot_com_crash/20260318T211815Z_what-were-the-main-causes-of-the-dot-com_experiment_af7cba51c1b5/output.json`
- `experiment.json`: `/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v0_tier1_eval_set_003/dot_com_crash/20260318T211815Z_what-were-the-main-causes-of-the-dot-com_experiment_af7cba51c1b5/experiment.json`

## Before / After vs `003`

### Plan Quality

- Unchanged. The same 4-step plan was generated.

### Metrics

- evidence count: `12 -> 11`
- evidence utilization: `0.3333 -> 0.4545`
- groundedness: `1.0 -> 1.0`
- plan coverage: `1.0 -> 1.0`
- verification: `supported=3 -> supported=3`

### Technology Step Survivors

`003`
- `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
- `Characterizing Technology's Influence on Distractive Behavior at ...`
- `Exploring the mechanism of crashes with automated vehicles using ...`

`004`
- `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
- `Characterizing Technology's Influence on Distractive Behavior at ...`

### Focused Assessment Of The Targeted Failure Mode

- The fix removed one obviously wrong technology-step result:
  - `Exploring the mechanism of crashes with automated vehicles using ...`
- However, the technology step still retained two clearly wrong results:
  - `Emerging Technologies Pose Solutions as Car Crash Fatalities Rise`
  - `Characterizing Technology's Influence on Distractive Behavior at ...`
- Therefore the targeted failure mode is reduced, but not fully fixed.

## Final Claims

`003`
- `Speculation in dotcom or internet-based businesses from 1995 to 2000 caused the dotcom bubble.`
- `Regulatory failures contributed to the 2007-2008 global financial crisis, which was related to the dot-com crash.`
- `Artificially low interest rates distorted market signals and led to an unsustainable boom.`

`004`
- `Regulatory shortcomings contributed to the crisis.`
- `Speculation in dot-com businesses caused a stock market bubble.`
- `Artificially low interest rates distorted market signals and led to an unsustainable boom.`

## Claim Quality Assessment

- The speculation claim stayed on-question and remained the strongest claim.
- The low-interest-rate claim stayed acceptable and grounded.
- The regulatory claim became more generic in `004`; it is less obviously off-question than the `003` reference to the 2007-2008 crisis, but it is also less specific.
- Overall claim quality stayed acceptable for v0, but it did not clearly improve.

## Overall Judgment

### Did the technology step finally drop the car-crash / vehicle-safety evidence?

No.

- It dropped one bad result.
- It did not remove the two most obvious wrong-domain survivors.

### Did evidence quality improve?

Slightly.

- The evidence pool got a little smaller.
- One bad automated-vehicle crash result disappeared.
- But the technology step still contains clearly wrong-domain evidence, so the improvement is only partial.

### Did the final claims stay on-question?

Mostly yes.

- The answer stayed broadly about causes of the dot-com crash.
- No obvious response/policy bug appeared.
- One claim remained too generic.

### Did groundedness remain acceptable?

Yes.

- `groundedness=1.0`
- all 3 claims were still marked `supported`

## Conclusion

`v0_dotcom_probe_004` shows that the narrow step-aware execution fix helped, but not enough to call the dot-com technology-step problem solved. The fix reduced the bad-result set, but it did not actually clear the technology step of car-crash / vehicle-safety noise.

This is a partial improvement, not a decisive one.
