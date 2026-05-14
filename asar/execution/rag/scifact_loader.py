"""
SciFact dataset adapter.

Downloads the BeIR/scifact mirror from Hugging Face via the `datasets`
library, normalizes records into `CorpusDocument`s, and persists
`documents.jsonl`, `queries.jsonl`, and `qrels.jsonl` under a stable layout:

    data/corpora/scifact/
        normalized/  — cleaned, deterministic line-delimited JSON
        index/       — vector index store

Why SciFact:
- ~5 MB total corpus on disk — well under the 2 GB course constraint
- Already document-like (title + abstract) and easy to chunk
- Includes gold qrels so we can evaluate retrieval recall@k

The first run will download the dataset via Hugging Face caching; subsequent
runs read directly from `normalized/documents.jsonl` and stay fully offline.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from asar.execution.rag.chunker import CorpusDocument


_HF_CORPUS_REPO = "BeIR/scifact"
_HF_QRELS_REPO = "BeIR/scifact-qrels"


@dataclass
class SciFactPaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def normalized(self) -> Path:
        return self.root / "normalized"

    @property
    def index(self) -> Path:
        return self.root / "index"

    def ensure(self) -> None:
        for d in (self.raw, self.normalized, self.index):
            d.mkdir(parents=True, exist_ok=True)


class SciFactDatasetAdapter:
    """Reproducible local mirror + normalization for BeIR/scifact."""

    DATASET_NAME = "scifact"

    def __init__(self, root: str | Path = "data/corpora/scifact") -> None:
        self.paths = SciFactPaths(root=Path(root))

    # -- public API ------------------------------------------------------

    def prepare(self, *, download: bool = True) -> Path:
        """Download (if requested) and normalize the dataset.

        Returns the path to ``normalized/documents.jsonl``.
        """
        self.paths.ensure()
        documents_path = self.paths.normalized / "documents.jsonl"
        if documents_path.exists() and documents_path.stat().st_size > 0:
            return documents_path
        if not download:
            return documents_path

        self._download_and_normalize_corpus(documents_path)
        self._download_and_normalize_queries(self.paths.normalized / "queries.jsonl")
        self._download_and_normalize_qrels(self.paths.normalized / "qrels.jsonl")
        return documents_path

    def documents(self) -> Iterable[CorpusDocument]:
        """Yield normalized CorpusDocument records."""
        documents_path = self.paths.normalized / "documents.jsonl"
        if not documents_path.exists():
            self.prepare()
        with documents_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                yield CorpusDocument(
                    doc_id=str(record["doc_id"]),
                    title=record.get("title") or "",
                    text=record.get("text") or "",
                    dataset_name=self.DATASET_NAME,
                    source_url=record.get("source_url"),
                    tags=tuple(record.get("tags") or []),
                    trust_label=record.get("trust_label") or "peer_reviewed",
                )

    def queries(self) -> list[dict[str, str]]:
        path = self.paths.normalized / "queries.jsonl"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def qrels(self) -> list[dict[str, object]]:
        path = self.paths.normalized / "qrels.jsonl"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    # -- internals -------------------------------------------------------

    def _load_hf_dataset(self, repo: str, name: str):
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "Loading SciFact requires the `datasets` library. "
                "Run `uv sync --extra rag`."
            ) from exc
        return load_dataset(repo, name=name, split="corpus" if name == "corpus" else "queries")

    def _download_and_normalize_corpus(self, dest: Path) -> None:
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Loading SciFact requires the `datasets` library. "
                "Run `uv sync --extra rag`."
            ) from exc
        ds = load_dataset(_HF_CORPUS_REPO, "corpus")
        # ``BeIR/scifact`` exposes a single 'corpus' split.
        split = ds[next(iter(ds.keys()))]
        count = 0
        with dest.open("w", encoding="utf-8") as out:
            for row in split:
                doc_id = str(row.get("_id") or row.get("doc_id") or "").strip()
                title = (row.get("title") or "").strip()
                text = (row.get("text") or "").strip()
                if not doc_id or not text:
                    continue
                normalized = {
                    "doc_id": doc_id,
                    "title": title or f"SciFact-{doc_id}",
                    "text": text,
                    "source_url": f"https://huggingface.co/datasets/{_HF_CORPUS_REPO}",
                    "tags": ["scifact", "scientific_claim"],
                    "trust_label": "peer_reviewed",
                }
                out.write(json.dumps(normalized) + "\n")
                count += 1
        if count == 0:
            dest.unlink(missing_ok=True)

    def _download_and_normalize_queries(self, dest: Path) -> None:
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError:
            dest.write_text("", encoding="utf-8")
            return
        try:
            ds = load_dataset(_HF_CORPUS_REPO, "queries")
        except Exception:
            dest.write_text("", encoding="utf-8")
            return
        split = ds[next(iter(ds.keys()))]
        with dest.open("w", encoding="utf-8") as out:
            for row in split:
                qid = str(row.get("_id") or row.get("qid") or "").strip()
                text = (row.get("text") or row.get("query") or "").strip()
                if not qid or not text:
                    continue
                out.write(json.dumps({"qid": qid, "text": text}) + "\n")

    def _download_and_normalize_qrels(self, dest: Path) -> None:
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError:
            dest.write_text("", encoding="utf-8")
            return
        try:
            ds = load_dataset(_HF_QRELS_REPO)
        except Exception:
            dest.write_text("", encoding="utf-8")
            return
        # qrels are split into 'train' / 'test' typically.
        with dest.open("w", encoding="utf-8") as out:
            for split_name, split in ds.items():
                for row in split:
                    qid = str(row.get("query-id") or row.get("qid") or "").strip()
                    doc_id = str(row.get("corpus-id") or row.get("doc_id") or "").strip()
                    score = row.get("score")
                    try:
                        rel = int(score) if score is not None else 0
                    except (TypeError, ValueError):
                        continue
                    if not qid or not doc_id:
                        continue
                    out.write(json.dumps({"qid": qid, "doc_id": doc_id, "relevance": rel, "split": split_name}) + "\n")


def default_root() -> Path:
    """Resolve the default SciFact storage root (overridable via env)."""
    override = os.environ.get("ASAR_CORPUS_ROOT")
    if override:
        return Path(override).expanduser().resolve() / "scifact"
    return Path("data/corpora/scifact").resolve()
