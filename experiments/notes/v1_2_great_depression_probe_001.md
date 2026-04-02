# v1_2_great_depression_probe_001

## Question

`What were the main causes of the Great Depression?`

## Exact command used

```bash
set -a && source .secrets && \
OPENAI_API_KEY=dummy \
ASAR_MODEL_PROVIDER=openai \
ASAR_MODEL_MODEL='llama3.1:8b' \
ASAR_OPENAI_BASE_URL='https://inference.ccrolabs.com/v1' \
ASAR_MODEL_MAX_TOKENS=512 \
ASAR_SEARCH_PROVIDER=tavily \
uv run python -m asar.demo \
  "What were the main causes of the Great Depression?" \
  --mode live \
  --output-dir experiments/runs/v1_2_great_depression_probe_001
```

## Artifact paths

- Note: [v1_2_great_depression_probe_001.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_2_great_depression_probe_001.md)
- Output: [output.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_2_great_depression_probe_001/20260325T230848Z_what-were-the-main-causes-of-the-great-d_experiment_d4e592cb2ed2/output.json)
- Experiment: [experiment.json](/home/tonystark/Desktop/multi-step-agent-research/experiments/runs/v1_2_great_depression_probe_001/20260325T230848Z_what-were-the-main-causes-of-the-great-d_experiment_d4e592cb2ed2/experiment.json)

## Comparison baselines

- strongest prior acceptable Great Depression run:
  - [v1_tier1_eval_set_002.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_002.md)
- active v1-minimal full-set baseline:
  - [v1_tier1_eval_set_004.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_tier1_eval_set_004.md)
- strongest focused v1-minimal Great Depression probe:
  - [v1_great_depression_probe_016.md](/home/tonystark/Desktop/multi-step-agent-research/experiments/notes/v1_great_depression_probe_016.md)

## Result

### Final claims

1. `The stock market crash of 1929 contributed to the Great Depression.`
2. `Protectionism and the collapse of world trade contributed to the Great Depression.`
3. `The Wall Street Crash of 1929 led to bank losses, failures, and a collapse in the money supply.`

### Metrics

- Evidence items: `12`
- Claim count: `3`
- Evidence utilization: `0.1667`
- Groundedness: `1.0`
- Verification summary: `supported=3, unsupported=0, insufficient=0, contradicted=0`

## Comparison

### Versus the strongest prior acceptable run: `v1_tier1_eval_set_002`

`v1_002` claims:
- `The stock market crash of 1929 contributed to the Great Depression.`
- `The collapse of world trade due to the Smoot-Hawley Tariff contributed to the Great Depression.`
- `The worldwide collapse in national money supplies contributed to the Great Depression.`

Assessment:
- `v1_2_001` matches `v1_002` on the core metrics:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- `v1_2_001` successfully brings back a monetary/banking-style family, which is the main qualitative win.
- But it is still weaker than `v1_002` overall because:
  - evidence utilization is much lower: `0.1667` vs `0.4`
  - the monetary/banking mechanism is fused into a Wall Street Crash sentence rather than surviving as a cleaner standalone money-supply claim
  - support still concentrates two claims on one source

### Versus `v1_tier1_eval_set_004` Great Depression

`v1_004` claims:
- `War reparations post-World War I contributed to the Great Depression.`
- `The stock market crash of 1929 contributed to the Great Depression.`
- `The Smoot-Hawley Tariff contributed to the Great Depression.`

Assessment:
- `v1_2_001` keeps the same healthy core metrics:
  - `3` claims
  - `groundedness=1.0`
  - `supported=3`
- It is more promising on mechanism diversity than the active v1-minimal baseline because the monetary/banking family appears again.
- But support concentration does not clearly improve:
  - `v1_004` used two supporting sources
  - `v1_2_001` also uses two supporting sources, with the stock-crash and money-supply/bank-loss claim both leaning on the same source
- Evidence utilization is slightly worse: `0.1667` vs `0.1818`

### Versus `v1_great_depression_probe_016`

`016` claims:
- `The stock market crash of 1929 contributed to the Great Depression.`
- `The collapse of world trade due to the Smoot-Hawley Tariff contributed to the Great Depression.`
- `War reparations post-World War I contributed to the Great Depression.`

Assessment:
- `v1_2_001` is more promising on the specific diversity problem because it reintroduces a monetary/banking / money-supply-style mechanism that `016` lacked.
- `016` still has slightly cleaner final phrasing and slightly better utilization: `0.1818` vs `0.1667`
- `v1_2_001` is a better architectural signal than `016` for the `v1.2` hypothesis, even though it is not cleanly stronger on every metric.

## Answers

- Did claim count remain healthy?
  - Yes, `3`.
- Did groundedness remain acceptable?
  - Yes, `1.0`.
- Did the stock crash family stay present?
  - Yes.
- Did the trade/protectionism family stay present?
  - Yes.
- Did the monetary/banking family appear when supported?
  - Yes, partially. It appeared, but in a fused claim tied to the Wall Street Crash rather than as a clean standalone money-supply claim.
- Did support concentration improve?
  - Not clearly. Two claims still rely on the same source.
- Did `v1.2` improve the targeted Great Depression mechanism-diversity problem?
  - Partially yes. It restored the missing monetary/banking family, which is the main qualitative improvement over the active v1-minimal baseline. But the support pattern is still concentrated and the final phrasing is not fully clean.

## Bottom line

`v1_2_great_depression_probe_001` is a meaningful positive signal for `v1.2`.

It does not clearly beat the strongest prior Great Depression run on efficiency or cleanliness, but it does recover the monetary/banking family that the active v1-minimal Great Depression baseline was missing. That makes `v1.2` more promising on Great Depression mechanism diversity than on 2008, even though support spread is still only partial.

## Recommended next step

Run the focused dot-com `v1.2` probe next.

At this point:
- `v1.2` has completed live focused probes on 2008 and Great Depression
- 2008 is mixed
- Great Depression shows a real mechanism-diversity gain

So dot-com is the right next focused live check before deciding whether `v1.2` is promising enough for a broader comparison set.
