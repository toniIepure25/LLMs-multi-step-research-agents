"""
Corpus types and document-aware chunker.

Chunking strategy:
1. If the document has section headings, split on headings first.
2. Within each section, group paragraphs greedily until target token size.
3. If a single paragraph is too large, fall back to sentence splitting.
4. Preserve overlap (in tokens) between adjacent chunks of the same section.

Tokens are approximated with a simple whitespace tokenizer — exact counts are
not the goal; bounded, deterministic chunk sizes are.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Iterable


_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$", re.MULTILINE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WHITESPACE_TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class CorpusDocument:
    """A normalized document ready for chunking and indexing."""

    doc_id: str
    title: str
    text: str
    dataset_name: str
    source_url: str | None = None
    tags: tuple[str, ...] = ()
    trust_label: str = "unknown"


@dataclass(frozen=True)
class CorpusChunk:
    """One chunk of a document, ready for embedding and indexing."""

    chunk_id: str
    doc_id: str
    title: str
    section: str
    text: str
    dataset_name: str
    source_url: str | None
    tags: tuple[str, ...]
    trust_label: str
    token_count: int
    char_count: int

    def to_metadata(self) -> dict[str, object]:
        """Return a flat metadata dict for storage alongside the embedding."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "section": self.section,
            "text": self.text,
            "dataset_name": self.dataset_name,
            "source_url": self.source_url or "",
            "tags": list(self.tags),
            "trust_label": self.trust_label,
            "token_count": self.token_count,
            "char_count": self.char_count,
        }


@dataclass(frozen=True)
class ChunkingConfig:
    """Tunable chunking parameters."""

    target_tokens: int = 450
    max_tokens: int = 650
    overlap_tokens: int = 80
    min_tokens: int = 120


@dataclass
class DocumentChunker:
    """Section -> paragraph -> sentence-aware chunker with overlap."""

    config: ChunkingConfig = field(default_factory=ChunkingConfig)

    def chunk(self, doc: CorpusDocument) -> list[CorpusChunk]:
        sections = self._split_sections(doc.text)
        chunks: list[CorpusChunk] = []
        for section_title, section_body in sections:
            for chunk_text in self._chunk_section(section_body):
                token_count = _token_count(chunk_text)
                if token_count == 0:
                    continue
                chunks.append(
                    CorpusChunk(
                        chunk_id=f"{doc.doc_id}::{uuid.uuid4().hex[:12]}",
                        doc_id=doc.doc_id,
                        title=doc.title,
                        section=section_title,
                        text=chunk_text.strip(),
                        dataset_name=doc.dataset_name,
                        source_url=doc.source_url,
                        tags=doc.tags,
                        trust_label=doc.trust_label,
                        token_count=token_count,
                        char_count=len(chunk_text),
                    )
                )
        if not chunks and doc.text.strip():
            # Single-chunk fallback for very short docs
            chunks.append(
                CorpusChunk(
                    chunk_id=f"{doc.doc_id}::{uuid.uuid4().hex[:12]}",
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=doc.title or "body",
                    text=doc.text.strip(),
                    dataset_name=doc.dataset_name,
                    source_url=doc.source_url,
                    tags=doc.tags,
                    trust_label=doc.trust_label,
                    token_count=_token_count(doc.text),
                    char_count=len(doc.text),
                )
            )
        return chunks

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        if not text:
            return []
        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            return [("body", text)]

        sections: list[tuple[str, str]] = []
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                sections.append(("body", preamble))
        for i, match in enumerate(matches):
            title = match.group(2).strip() or "body"
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_body = text[start:end].strip()
            if section_body:
                sections.append((title, section_body))
        return sections

    def _chunk_section(self, section_body: str) -> list[str]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_body) if p.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = _token_count(paragraph)

            if paragraph_tokens > self.config.max_tokens:
                # flush current
                if current:
                    chunks.append("\n\n".join(current))
                    current, current_tokens = self._carry_overlap(current)
                # split paragraph into sentence-sized chunks
                chunks.extend(self._chunk_sentences(paragraph))
                continue

            if current_tokens + paragraph_tokens > self.config.target_tokens and current:
                chunks.append("\n\n".join(current))
                current, current_tokens = self._carry_overlap(current)

            current.append(paragraph)
            current_tokens += paragraph_tokens

            if current_tokens >= self.config.max_tokens:
                chunks.append("\n\n".join(current))
                current, current_tokens = self._carry_overlap(current)

        if current:
            tail = "\n\n".join(current)
            tail_tokens = _token_count(tail)
            if tail_tokens >= self.config.min_tokens or not chunks:
                chunks.append(tail)
            else:
                # Merge tail into previous chunk to avoid tiny fragments.
                chunks[-1] = chunks[-1] + "\n\n" + tail
        return chunks

    def _chunk_sentences(self, paragraph: str) -> list[str]:
        sentences = [s.strip() for s in _SENTENCE_RE.split(paragraph) if s.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0
        for sentence in sentences:
            sentence_tokens = _token_count(sentence)
            if current_tokens + sentence_tokens > self.config.target_tokens and current:
                chunks.append(" ".join(current))
                current, current_tokens = self._carry_overlap(current)
            current.append(sentence)
            current_tokens += sentence_tokens
            if current_tokens >= self.config.max_tokens:
                chunks.append(" ".join(current))
                current, current_tokens = self._carry_overlap(current)
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _carry_overlap(self, current: list[str]) -> tuple[list[str], int]:
        if self.config.overlap_tokens <= 0 or not current:
            return [], 0
        # Take the last paragraph(s) up to overlap_tokens worth of tokens
        tail_tokens: list[str] = []
        for piece in reversed(current):
            piece_tokens = _WHITESPACE_TOKEN_RE.findall(piece)
            for tok in reversed(piece_tokens):
                tail_tokens.append(tok)
                if len(tail_tokens) >= self.config.overlap_tokens:
                    break
            if len(tail_tokens) >= self.config.overlap_tokens:
                break
        if not tail_tokens:
            return [], 0
        overlap = " ".join(reversed(tail_tokens))
        return [overlap], _token_count(overlap)


def _token_count(text: str) -> int:
    return len(_WHITESPACE_TOKEN_RE.findall(text))


def chunk_documents(
    documents: Iterable[CorpusDocument],
    config: ChunkingConfig | None = None,
) -> list[CorpusChunk]:
    """Convenience helper to chunk an iterable of documents."""
    chunker = DocumentChunker(config=config or ChunkingConfig())
    chunks: list[CorpusChunk] = []
    for doc in documents:
        chunks.extend(chunker.chunk(doc))
    return chunks
