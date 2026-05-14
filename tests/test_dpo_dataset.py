"""
Tests for the DPO preference dataset builder.

These tests do NOT run training. They validate:
- preference triples have the expected shape (prompt/chosen/rejected)
- chosen != rejected
- the prompt is a valid chat-template-like string
- the builder is deterministic for a given seed
- the CLI writes the configured number of pairs
"""

from __future__ import annotations

import json
from pathlib import Path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _stage_tiny_scifact(tmp_path: Path):
    from asar.execution.rag.scifact_loader import SciFactDatasetAdapter

    root = tmp_path / "scifact"
    adapter = SciFactDatasetAdapter(root=root)
    adapter.paths.ensure()
    _write_jsonl(
        adapter.paths.normalized / "documents.jsonl",
        [
            {
                "doc_id": "1",
                "title": "BRCA1 and cancer risk",
                "text": "BRCA1 mutations are strongly associated with increased breast and ovarian cancer risk in carriers.",
                "source_url": "corpus://scifact/1",
                "tags": ["scifact"],
                "trust_label": "peer_reviewed",
            },
            {
                "doc_id": "2",
                "title": "Photosynthesis basics",
                "text": "Photosynthesis converts light into chemical energy via light-dependent and light-independent reactions in chloroplasts.",
                "source_url": "corpus://scifact/2",
                "tags": ["scifact"],
                "trust_label": "peer_reviewed",
            },
            {
                "doc_id": "3",
                "title": "Mitochondrial DNA inheritance",
                "text": "Mitochondrial DNA in humans is inherited predominantly from the mother and accumulates mutations at a higher rate than nuclear DNA.",
                "source_url": "corpus://scifact/3",
                "tags": ["scifact"],
                "trust_label": "peer_reviewed",
            },
        ],
    )
    return root


def test_preference_pairs_have_expected_shape(tmp_path: Path) -> None:
    from asar.finetune.preference_dataset import build_preference_pairs

    root = _stage_tiny_scifact(tmp_path)
    pairs = list(build_preference_pairs(root=root, limit=None, seed=7))
    assert len(pairs) == 3
    for pair in pairs:
        assert set(pair.keys()) == {"prompt", "chosen", "rejected"}
        assert pair["prompt"].startswith("<|system|>")
        assert "Passage:" in pair["prompt"]
        assert "Question:" in pair["prompt"]
        assert pair["chosen"].strip()
        assert pair["rejected"].strip()
        # Chosen and rejected must differ — otherwise DPO sees no signal.
        assert pair["chosen"].strip() != pair["rejected"].strip()


def test_preference_dataset_is_deterministic(tmp_path: Path) -> None:
    from asar.finetune.preference_dataset import build_preference_pairs

    root = _stage_tiny_scifact(tmp_path)
    pairs_a = list(build_preference_pairs(root=root, limit=None, seed=42))
    pairs_b = list(build_preference_pairs(root=root, limit=None, seed=42))
    assert pairs_a == pairs_b


def test_preference_dataset_writer(tmp_path: Path) -> None:
    from asar.finetune.preference_dataset import build_preference_pairs, write_preference_dataset

    root = _stage_tiny_scifact(tmp_path)
    out = tmp_path / "pref.jsonl"
    count = write_preference_dataset(
        build_preference_pairs(root=root, limit=2, seed=1),
        out,
    )
    assert count == 2
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    for p in parsed:
        assert set(p.keys()) == {"prompt", "chosen", "rejected"}


def test_preference_dataset_cli(tmp_path: Path) -> None:
    """The CLI should accept --scifact-root + --output and write a JSONL."""
    from asar.finetune.cli_build_preference import main

    root = _stage_tiny_scifact(tmp_path)
    out = tmp_path / "out" / "pref.jsonl"
    code = main(
        [
            "--scifact-root", str(root),
            "--output", str(out),
            "--limit", "2",
            "--seed", "9",
        ]
    )
    assert code == 0
    assert out.exists()
    rows = [json.loads(line) for line in out.read_text().strip().splitlines()]
    assert len(rows) == 2
    for r in rows:
        assert {"prompt", "chosen", "rejected"} <= set(r.keys())
