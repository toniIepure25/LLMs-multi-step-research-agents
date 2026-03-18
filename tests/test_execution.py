"""
Unit tests for the v0 `WebSearchExecutor`.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import ExecutionError, SearchClientError
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem
from asar.execution import WebSearchExecutor
from schemas.task_packet import TaskPacket


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _task(max_results: int | None = None) -> TaskPacket:
    constraints = {}
    if max_results is not None:
        constraints["max_results"] = max_results
    return TaskPacket(
        task_id="task_123",
        plan_id="plan_123",
        step_id="step_123",
        action="search",
        query="battery storage costs 2024",
        context="Focus on recent comparative evidence.",
        constraints=constraints,
    )


class StubSearchClient:
    """Small fake search client that records requests and returns fixed responses."""

    def __init__(self, response: object) -> None:
        self._response = response
        self.requests: list[SearchRequest] = []

    async def search(self, request: SearchRequest) -> SearchResponse:
        self.requests.append(request)
        return self._response  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_web_search_executor_happy_path_returns_evidence() -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(
                    url="https://example.com/report",
                    title="Battery Storage Cost Report",
                    snippet="Battery storage costs fell across multiple markets in 2024.",
                    author="Analyst Team",
                    publication_date="2024-11-01",
                    rank=1,
                    score=0.91,
                    source_name="Example Research",
                    raw_payload={"provider_id": "r1"},
                )
            ]
        )
    )
    executor = WebSearchExecutor(client, settings)

    evidence = await executor.execute(_task())

    assert len(evidence) == 1
    assert evidence[0].evidence_id.startswith("evidence_")
    assert evidence[0].task_id == "task_123"
    assert evidence[0].content == "Battery storage costs fell across multiple markets in 2024."
    assert evidence[0].source.url == "https://example.com/report"
    assert evidence[0].source.raw_snippet == evidence[0].content


@pytest.mark.asyncio
async def test_web_search_executor_provider_failure_returns_typed_failure() -> None:
    settings = load_settings(CONFIG_DIR)

    class BrokenSearchClient:
        async def search(self, request: SearchRequest) -> SearchResponse:
            raise SearchClientError("provider unavailable", retryable=True)

    executor = WebSearchExecutor(BrokenSearchClient(), settings)

    result = await executor.execute_result(_task())

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "execution_provider_failure"
    assert result.error.retryable is True
    assert result.error.details["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_web_search_executor_malformed_provider_payload_returns_typed_failure() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient({"results": [{"url": "https://example.com"}]})
    executor = WebSearchExecutor(client, settings)

    result = await executor.execute_result(_task())

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "execution_invalid_provider_payload"


@pytest.mark.asyncio
async def test_web_search_executor_generates_consistent_evidence_ids() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(url="https://example.com/1", snippet="First", rank=1),
                SearchResultItem(url="https://example.com/2", snippet="Second", rank=2),
            ]
        )
    )
    executor = WebSearchExecutor(client, settings)

    evidence = await executor.execute(_task())

    assert len(evidence) == 2
    assert all(item.evidence_id.startswith("evidence_") for item in evidence)
    assert evidence[0].evidence_id != evidence[1].evidence_id


@pytest.mark.asyncio
async def test_web_search_executor_populates_source_metadata_and_task_linkage() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(
                    url="https://example.com/market",
                    title="Market Update",
                    snippet="Utility-scale batteries became cheaper during 2024.",
                    author="A. Researcher",
                    publication_date="2024-09-15",
                    rank=1,
                    source_name="Market Watch",
                )
            ]
        )
    )
    executor = WebSearchExecutor(client, settings)

    evidence = await executor.execute(_task())
    item = evidence[0]

    assert item.task_id == "task_123"
    assert item.source.title == "Market Update"
    assert item.source.author == "A. Researcher"
    assert item.source.publication_date == "2024-09-15"
    assert item.source.additional["rank"] == 1
    assert item.source.additional["query"] == "battery storage costs 2024"
    assert item.source.additional["task_action"] == "search"


@pytest.mark.asyncio
async def test_web_search_executor_preserves_order_and_rank_metadata() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(url="https://example.com/1", snippet="First result", rank=1),
                SearchResultItem(url="https://example.com/2", snippet="Second result", rank=2),
                SearchResultItem(url="https://example.com/3", snippet="Third result", rank=3),
            ]
        )
    )
    executor = WebSearchExecutor(client, settings)

    evidence = await executor.execute(_task())

    assert [item.content for item in evidence] == ["First result", "Second result", "Third result"]
    assert [item.source.additional["rank"] for item in evidence] == [1, 2, 3]


@pytest.mark.asyncio
async def test_web_search_executor_uses_utc_timestamps_and_schema_valid_items() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[SearchResultItem(url="https://example.com/utc", snippet="Timestamp check", rank=1)]
        )
    )
    executor = WebSearchExecutor(client, settings)

    evidence = await executor.execute(_task())
    item = evidence[0]

    assert item.created_at.utcoffset() is not None
    assert item.source.access_date.utcoffset() is not None
    assert item.source.raw_snippet == "Timestamp check"


@pytest.mark.asyncio
async def test_web_search_executor_applies_top_k_consistently() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(url="https://example.com/1", snippet="First", rank=1),
                SearchResultItem(url="https://example.com/2", snippet="Second", rank=2),
                SearchResultItem(url="https://example.com/3", snippet="Third", rank=3),
            ]
        )
    )
    executor = WebSearchExecutor(client, settings, default_top_k=2)

    evidence = await executor.execute(_task())

    assert len(evidence) == 2
    assert client.requests[0].top_k == 2


@pytest.mark.asyncio
async def test_web_search_executor_task_constraint_overrides_default_top_k() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(
        SearchResponse(
            results=[
                SearchResultItem(url="https://example.com/1", snippet="First", rank=1),
                SearchResultItem(url="https://example.com/2", snippet="Second", rank=2),
                SearchResultItem(url="https://example.com/3", snippet="Third", rank=3),
            ]
        )
    )
    executor = WebSearchExecutor(client, settings, default_top_k=1)

    evidence = await executor.execute(_task(max_results=3))

    assert len(evidence) == 3
    assert client.requests[0].top_k == 3


@pytest.mark.asyncio
async def test_web_search_executor_raises_on_invalid_task_constraint() -> None:
    settings = load_settings(CONFIG_DIR)
    client = StubSearchClient(SearchResponse(results=[]))
    executor = WebSearchExecutor(client, settings)

    with pytest.raises(ExecutionError):
        await executor.execute(_task(max_results=0))
