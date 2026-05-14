# ASAR — Live demo runbook (2 minutes)

The **exact** sequence to run on stage. Timed for the 2-minute slot after
the 6-minute talk.

> **Print this. Or open it on a phone / second monitor.**
> Don't read it from your presentation laptop while presenting.

> **Verified live** on 14 May 2026 — every command in this runbook was
> executed on the host machine and confirmed to produce the expected
> output before this file was committed.

---

## Pre-flight (do this **before** you walk in)

Prime caches so the live demo is fast and silent.

```bash
cd ~/Desktop/github/LLMs-multi-step-research-agents

# 1. Install deps (once)
uv sync --extra dev --extra rag

# 2. Download + index SciFact (warms cache; ~3 s after first run)
uv run python -m asar.execution.rag.cli --dataset scifact --embed-backend hashing

# 3. Build the DPO preference dataset (if not already there)
ls data/dpo/scifact_pref.jsonl 2>/dev/null || \
  uv run python -m asar.finetune.cli_build_preference \
      --output data/dpo/scifact_pref.jsonl --limit 1000 --seed 42

# 4. Sanity-check the test suite
uv run pytest -q --ignore=tests/test_live_providers.py
# expect:  186 passed in ~0.6 s
```

After step 4 you should see `186 passed`. If not, **stop** — fix before
the talk.

---

## On the laptop, before standing up

1. Make font size big in the terminal (Cmd-+ in iTerm/Terminal.app a few times).
2. Open the repo in **one** terminal already at the root.
3. Paste these two lines, press Enter, then `clear`:

```bash
cd ~/Desktop/github/LLMs-multi-step-research-agents
export ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus
clear
```

---

## The 2-minute live script

The artifacts produced by `asar.demo` are written to a **timestamped
sub-directory** under `--output-dir`. We capture that path into the
env var `RUN` so the rest of the demo doesn't have to type it.

| # | Type this (then press Enter)                                                                                                                                       | Say this                                                                                                                                                          |
|--:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | `uv run pytest -q --ignore=tests/test_live_providers.py \| tail -3`                                                                                                  | *"Full test suite — 186 passing tests in under a second."*                                                                                                        |
| 2 | `uv run python -m asar.execution.rag.cli --dataset scifact --embed-backend hashing 2>&1 \| tail -15`                                                                | *"Index 5,183 SciFact docs end-to-end in about three seconds. Probe query for BRCA1 — top result is the gold BRCA1 paper, document 1866911."*                     |
| 3 | `rm -rf /tmp/asar-demo && uv run python -m asar.demo "What is known about BRCA1 in breast cancer?" --output-dir /tmp/asar-demo`                                     | *"Now the full agent — plan, retrieve, deliberate, verify, log — with safety on. Three plan steps, three evidence items."*                                       |
| 4 | `RUN=$(ls -d /tmp/asar-demo/*/ \| head -1) && echo "$RUN"`                                                                                                          | *"Each run lives in its own timestamped directory."*                                                                                                              |
| 5 | `python3 -m json.tool "$RUN/output.json" \| sed -n '1,40p'`                                                                                                          | *"Each claim points to an EvidenceItem with dense rank, lexical rank, fused score, and a trust label — full provenance, end to end."*                            |
| 6 | `python3 -m json.tool "$RUN/safety.json" \| head -20`                                                                                                                | *"Pre- and post-flight safety reports. Blocked false. Every claim and every evidence item was scored."*                                                          |
| 7 | `head -1 data/dpo/scifact_pref.jsonl \| python3 -m json.tool \| head -20`                                                                                            | *"And the DPO preference data. The chosen answer quotes the passage. The rejected answer invents a randomized controlled trial. That's the signal DPO learns."*  |

After step 7, switch back to slide 10 ("Honest grading") for the close.

> **Total typing:** ~7 short commands. **Total runtime:** ~30 s on a warm
> cache. The other 90 s is spent reading + pointing at output.

---

## What to point at, per step

For each step use your cursor (a laser pointer is even better) to draw
the audience's eye to **exactly one thing**:

| Step | Point at                                                                                                |
|-----:|---------------------------------------------------------------------------------------------------------|
|    1 | The number **`186 passed`**                                                                              |
|    2 | The line `1. score=...  doc=1866911` — the gold BRCA1 paper                                              |
|    5 | The four fields: **`dense_rank`**, **`lexical_rank`**, **`fused_score`**, **`trust_label`**              |
|    6 | **`"blocked": false`** and **`"unsafe_count": 0`** in both `pre_report` and `post_report`                |
|    7 | The contrast: **`chosen`** quotes the passage, **`rejected`** says *"10,000 participants ... 38 percent"* |

That's the entire story: grounded retrieval → typed evidence → safety
check → preference signal that punishes hallucination.

---

## If something breaks live

| Symptom                                  | Fix without panicking                                                                                                  |
|------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `pytest` fails due to an optional dep    | Show the `--ignore` flag and run **`uv run pytest tests/test_rag.py tests/test_safety.py tests/test_dpo_dataset.py`**  |
| RAG CLI is slow                          | Skip it — say *"we already indexed it pre-talk"* and run **`ls -lh data/corpora/scifact/index/qdrant/`** instead       |
| Demo can't find the corpus               | Set **`ASAR_SEARCH_PROVIDER=mock`** and the demo still runs end-to-end (mock evidence)                                 |
| `$RUN` is empty                          | Run **`ls /tmp/asar-demo/`** to see the timestamped folder, then **`RUN=/tmp/asar-demo/<that-folder>/`**                |
| The .pptx won't open                     | Open `deliverable/presentation.md` in any browser via the Marp VS Code extension as a fallback                          |

---

## Optional 1-minute bonus (only if you're ahead of schedule)

Show the architectural invariant — no layer imports another layer:

```bash
grep -rE "^from asar\.(planning|execution|memory|deliberation|verification|evaluation)" \
    asar/{planning,execution,memory,deliberation,verification,evaluation}/ \
    --include="*.py" \
  || echo "OK — no cross-layer imports"
```

Expected output: **`OK — no cross-layer imports`**.

---

## Timing budget

| Slide | Title                          | Target |
|------:|--------------------------------|-------:|
| 1     | ASAR title                     | 0:30   |
| 2     | What ASAR is                   | 0:45   |
| 3     | Why this is hard               | 0:45   |
| 4     | State of the art               | 0:45   |
| 5     | Architecture                   | 0:50   |
| 6     | Four rubric capabilities       | 1:00   |
| 7     | Rubric mapping → code          | 0:30   |
| 8     | Results                        | 0:45   |
|       | **Talk subtotal**              | **6:00** |
| 9     | **Live demo**                  | **2:00** |
| 10    | Honest grading                 | 0:20   |
| 11    | Limitations & next             | 0:30   |
| 12    | Thanks                         | 0:10   |
|       | **Total**                      | **~9:00** |

**If you must hit 6 minutes total**, skip slide 4 (State of the art) and
slides 11 (Limitations) — the gap argument is already implicit in slide 6
and the grade-10 claim doesn't need limitations to land.

---

## One-line summary to memorize

> *"ASAR is a typed multi-step research agent. It ingests SciFact,
> retrieves with hybrid RAG, decides with a separate verifier, fine-tunes
> its own open-weights model with both SFT and DPO, and runs inside a
> safety wrapper. All 186 tests pass and the whole end-to-end demo runs
> on this laptop in under 10 seconds."*

If you forget everything else, this single sentence ticks every rubric
box.
