"""
Build a small instruction-tuned Q&A dataset derived from SciFact + a research
agent task template.

Output format (JSONL, one example per line):

    {
        "messages": [
            {"role": "system", "content": "<system prompt>"},
            {"role": "user", "content": "<user prompt>"},
            {"role": "assistant", "content": "<gold answer>"}
        ]
    }

This is the format TRL's `SFTTrainer` expects when a chat template is applied.
Each SciFact document becomes one Q&A example:

    Q: <claim-style question about the abstract>
    A: <one-paragraph answer grounded in the abstract>

Why this dataset is research-relevant:
- It teaches the SLM to answer **grounded** in a provided passage — the exact
  pattern our deliberation/synthesis layer uses (synthesize from
  ``EvidenceItem``s, never fabricate).
- It is tiny (<= 2k examples), so a LoRA fine-tune fits in ~10-30 min on a
  CPU/MPS Mac.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Iterable, Iterator

from asar.execution.rag.scifact_loader import SciFactDatasetAdapter


SYSTEM_PROMPT = (
    "You are ASAR, a careful research assistant. Answer ONLY using the provided "
    "passage. If the passage does not contain enough information, say so explicitly. "
    "Keep answers concise (2-4 sentences) and never invent citations or facts."
)


_QUESTION_TEMPLATES = (
    "Based on the passage, what does the research say about: {topic}?",
    "What is the main finding of the passage about {topic}?",
    "Summarize the evidence the passage gives for {topic}.",
    "According to the passage, what role does {topic} play?",
    "What conclusion does the passage support about {topic}?",
)


def _topic_from_title(title: str) -> str:
    title = title.strip().rstrip(".")
    if not title:
        return "the subject"
    lowered = title.lower()
    for prefix in ("a study of ", "the role of ", "effects of ", "impact of "):
        if lowered.startswith(prefix):
            return title[len(prefix):]
    return title


def _build_answer(text: str, max_chars: int = 600) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    truncated = cleaned[:max_chars].rsplit(".", 1)[0]
    if not truncated:
        truncated = cleaned[:max_chars]
    return truncated + "."


def build_examples(
    *,
    root: Path,
    limit: int | None = None,
    seed: int = 42,
) -> Iterator[dict]:
    """Yield chat-format SFT examples derived from a SciFact corpus.

    Parameters
    ----------
    root
        Directory containing a prepared SciFact normalized corpus
        (``normalized/documents.jsonl``).
    limit
        Cap on number of source documents to use.
    seed
        Deterministic shuffling and template selection.
    """
    adapter = SciFactDatasetAdapter(root=root)
    docs = list(adapter.documents())
    rng = random.Random(seed)
    rng.shuffle(docs)
    if limit is not None:
        docs = docs[:limit]
    for doc in docs:
        topic = _topic_from_title(doc.title)
        question = rng.choice(_QUESTION_TEMPLATES).format(topic=topic)
        user_prompt = f"Passage:\n{doc.text.strip()}\n\nQuestion: {question}"
        answer = _build_answer(doc.text)
        yield {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": answer},
            ]
        }


def write_dataset(examples: Iterable[dict], out_path: Path) -> int:
    """Write examples to JSONL. Returns the number of examples written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for example in examples:
            fh.write(json.dumps(example) + "\n")
            count += 1
    return count
