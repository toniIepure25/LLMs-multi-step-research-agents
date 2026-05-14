"""
Embedding backends.

Two backends, same protocol:
- `FastEmbedEmbedder` (production): BAAI/bge-small-en-v1.5 via FastEmbed.
  Pure CPU, fast on Apple Silicon, no external service.
- `HashingEmbedder` (deterministic fallback): bag-of-hashed-tokens projection
  into a fixed-dim float vector. Works without any heavy ML dependency, used
  for smoke tests, CI, and constrained environments.

Both produce L2-normalized float vectors of a known dimension.
"""

from __future__ import annotations

import hashlib
import math
import os
from typing import Iterable, Protocol


class EmbedderProtocol(Protocol):
    """Minimal protocol for an embedding backend."""

    @property
    def dim(self) -> int: ...

    @property
    def name(self) -> str: ...

    def encode(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic bag-of-hashed-tokens embedder.

    Not a real semantic embedder — but it is deterministic, fast, dependency-free,
    and good enough for unit tests, smoke runs, and pipeline plumbing.
    """

    def __init__(self, dim: int = 384) -> None:
        if dim < 32:
            raise ValueError("dim must be at least 32")
        self._dim = dim
        self._name = f"hashing-{dim}"

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return self._name

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._encode_one(t) for t in texts]

    def _encode_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in _tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
        return _l2_normalize(vec)


class FastEmbedEmbedder:
    """Real production embedder backed by FastEmbed (CPU)."""

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str | None = None) -> None:
        try:
            from fastembed import TextEmbedding  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "FastEmbed is not installed. Run `uv sync --extra rag`."
            ) from exc

        self._model_name = model_name or self.DEFAULT_MODEL
        self._model = TextEmbedding(model_name=self._model_name)
        # FastEmbed lazy-loads on first encode; we probe dim with a tiny call.
        probe = list(self._model.embed(["dim probe"]))
        if not probe:
            raise RuntimeError("FastEmbed returned no embeddings on probe")
        self._dim = len(probe[0])

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"fastembed:{self._model_name}"

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for vec in self._model.embed(texts):
            vectors.append(_l2_normalize([float(x) for x in vec]))
        return vectors


def build_embedder(backend: str | None = None) -> EmbedderProtocol:
    """Build the configured embedder backend.

    Resolution order:
    1. Explicit ``backend`` argument.
    2. ``ASAR_RAG_EMBED_BACKEND`` environment variable.
    3. Default: ``hashing`` (deterministic, dependency-free).
    """
    resolved = (backend or os.environ.get("ASAR_RAG_EMBED_BACKEND") or "hashing").strip().lower()
    if resolved in {"hashing", "hash", "fallback"}:
        return HashingEmbedder()
    if resolved in {"fastembed", "bge", "bge-small"}:
        return FastEmbedEmbedder()
    raise ValueError(f"Unknown embedder backend: {resolved!r}")


def _tokenize(text: str) -> Iterable[str]:
    import re
    return (m.group(0).lower() for m in re.finditer(r"[A-Za-z0-9]+", text))


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0.0:
        return vec
    return [x / norm for x in vec]
