"""
Build a preference dataset for DPO (Direct Preference Optimization).

DPO is the modern, reward-model-free flavor of RLHF: instead of training a
reward model and running PPO, we directly optimize the policy on
``(prompt, chosen, rejected)`` triples. This makes it CPU/MPS-friendly
and well-suited to the laptop training budget of this project.

Strategy for synthesizing preference pairs from SciFact
-------------------------------------------------------

For each passage in the SciFact corpus we emit one triple:

- **prompt**: ``"Passage:\\n<text>\\n\\nQuestion: <q>"`` — the same shape as
  the SFT prompt.
- **chosen**: a *grounded* answer extracted from the passage itself.
- **rejected**: an *ungrounded* answer that exhibits one of the failure
  modes we want the model to learn to avoid:
    - fabricates statistics or citations that are not in the passage
    - asserts confident claims while ignoring the passage entirely
    - copies the wrong passage (taken from a different SciFact document)

This is sufficient for a proof-of-shape DPO pass that the model **prefers
grounded answers to fabricated ones** — directly aligned with the
project's grounded-output invariant.

Output format
-------------

JSONL, one preference pair per line:

    {
        "prompt": "...",
        "chosen": "...",
        "rejected": "..."
    }

TRL's ``DPOTrainer`` consumes this format directly.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Iterable, Iterator

from asar.execution.rag.scifact_loader import SciFactDatasetAdapter
from asar.finetune.dataset import SYSTEM_PROMPT, _QUESTION_TEMPLATES, _build_answer, _topic_from_title


# ---------------------------------------------------------------------------
# Rejected-answer templates — each one models a real failure mode we want
# the SLM to learn to avoid.
# ---------------------------------------------------------------------------

_FABRICATED_STATISTICS = (
    "{topic} has been shown in approximately 87% of cases studied across "
    "more than 4,200 patients, with a hazard ratio of 2.3 (p < 0.001).",
    "Multiple randomized controlled trials with over 10,000 participants "
    "confirm that {topic} reduces mortality by 38 percent.",
    "A 2019 meta-analysis of 27 studies found that {topic} accounts for "
    "between 60 and 75 percent of observed variance.",
)

_OFF_TOPIC_CONFIDENT = (
    "The most important thing to know about {topic} is that it is widely "
    "regarded as a settled question, and further research is not required.",
    "There is broad expert consensus that {topic} can be safely ignored in "
    "most clinical and research settings.",
    "{topic} has no measurable effect; published claims to the contrary "
    "reflect publication bias rather than real findings.",
)


def _fabricated_answer(topic: str, rng: random.Random) -> str:
    """Generate a confident answer that invents data not in the passage."""
    if rng.random() < 0.5:
        return rng.choice(_FABRICATED_STATISTICS).format(topic=topic)
    return rng.choice(_OFF_TOPIC_CONFIDENT).format(topic=topic)


def _wrong_passage_answer(other_text: str) -> str:
    """Use a different passage's content as the answer — a silent miss."""
    return _build_answer(other_text)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------


def build_preference_pairs(
    *,
    root: Path,
    limit: int | None = None,
    seed: int = 42,
) -> Iterator[dict]:
    """Yield DPO preference triples derived from a SciFact corpus.

    Each yielded record is a ``{"prompt", "chosen", "rejected"}`` dict.
    """
    adapter = SciFactDatasetAdapter(root=root)
    docs = list(adapter.documents())
    if not docs:
        return
    rng = random.Random(seed)
    rng.shuffle(docs)
    if limit is not None:
        docs = docs[:limit]
    n = len(docs)
    for idx, doc in enumerate(docs):
        topic = _topic_from_title(doc.title)
        question = rng.choice(_QUESTION_TEMPLATES).format(topic=topic)
        prompt = (
            f"<|system|>\n{SYSTEM_PROMPT}\n"
            f"<|user|>\nPassage:\n{doc.text.strip()}\n\nQuestion: {question}\n"
            f"<|assistant|>\n"
        )
        chosen = _build_answer(doc.text)
        # Choose a rejected-answer failure mode at random.
        mode = rng.choice(("fabricate", "off_topic", "wrong_passage"))
        if mode == "fabricate":
            rejected = _fabricated_answer(topic, rng)
        elif mode == "off_topic":
            rejected = _fabricated_answer(topic, rng)
        else:
            # Pick a different passage's text as a wrong-passage answer.
            other_idx = (idx + 1 + rng.randrange(max(1, n - 1))) % n
            if other_idx == idx and n > 1:
                other_idx = (idx + 1) % n
            rejected = _wrong_passage_answer(docs[other_idx].text)
        # Guard against degenerate ties.
        if rejected.strip() == chosen.strip():
            rejected = _fabricated_answer(topic, rng)
        yield {"prompt": prompt, "chosen": chosen, "rejected": rejected}


def write_preference_dataset(pairs: Iterable[dict], out_path: Path) -> int:
    """Write preference pairs to JSONL. Returns the number of pairs written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for pair in pairs:
            fh.write(json.dumps(pair) + "\n")
            count += 1
    return count
