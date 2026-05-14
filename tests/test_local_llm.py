"""
Tests for the fine-tuning path: dataset builder + LocalSLMClient construction.

These tests deliberately do NOT load model weights or run training. They
validate:
- the SFT dataset builder produces the expected chat-format shape
- LocalSLMClient honors env vars and exposes the correct attributes before
  lazy-loading the model
- LocalSLMClient satisfies LLMClientProtocol structurally
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from asar.core.llm import LLMClientProtocol
from asar.providers.local_llm import LocalSLMClient, build_local_llm_client


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_local_slm_client_construction_is_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASAR_LOCAL_BASE_MODEL", raising=False)
    monkeypatch.delenv("ASAR_LOCAL_ADAPTER_PATH", raising=False)
    client = LocalSLMClient()
    assert client.base_model.startswith("Qwen/")
    assert client.adapter_path is None
    # Lazy attributes should not be loaded yet
    assert client._model is None  # type: ignore[attr-defined]
    assert client._tokenizer is None  # type: ignore[attr-defined]


def test_local_slm_client_respects_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASAR_LOCAL_BASE_MODEL", "some/base")
    monkeypatch.setenv("ASAR_LOCAL_ADAPTER_PATH", "/tmp/adapter")
    client = build_local_llm_client()
    assert client.base_model == "some/base"
    assert client.adapter_path == "/tmp/adapter"


def test_local_slm_client_satisfies_llm_protocol() -> None:
    client = LocalSLMClient()
    assert isinstance(client, LLMClientProtocol)


def test_sft_dataset_builder_produces_chat_messages(tmp_path: Path) -> None:
    # Pre-stage a tiny normalized SciFact corpus so the builder doesn't try to download.
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
        ],
    )

    from asar.finetune.dataset import build_examples

    examples = list(build_examples(root=root, limit=None, seed=42))
    assert len(examples) == 2
    for example in examples:
        assert "messages" in example
        roles = [m["role"] for m in example["messages"]]
        assert roles == ["system", "user", "assistant"]
        assert "Passage:" in example["messages"][1]["content"]
        assert example["messages"][2]["content"]
