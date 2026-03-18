"""
Minimal v0 web/search executor.
"""

from __future__ import annotations

from pydantic import ValidationError

from asar.common import ASARSettings, IDPrefix, generate_id, generate_trace_id, get_logger, setup_logging
from asar.core.errors import ExecutionError, SearchClientError
from asar.core.result import OperationResult
from asar.core.search import SearchClientProtocol, SearchRequest, SearchResponse, SearchResultItem
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.task_packet import TaskPacket


class WebSearchExecutor:
    """Execute one `TaskPacket` through a typed search client."""

    def __init__(
        self,
        search_client: SearchClientProtocol,
        settings: ASARSettings,
        *,
        default_top_k: int = 5,
    ) -> None:
        if default_top_k < 1:
            raise ValueError("default_top_k must be at least 1")
        self._search_client = search_client
        self._settings = settings
        self._default_top_k = default_top_k
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.execution.web_search_executor"

    async def execute(self, task: TaskPacket) -> list[EvidenceItem]:
        """Execute one search task or raise a typed execution error."""

        result = await self.execute_result(task)
        if result.is_error and result.error is not None:
            raise ExecutionError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def execute_result(self, task: TaskPacket) -> OperationResult[list[EvidenceItem]]:
        """Execute one search task and keep provider failures inspectable."""

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)

        try:
            request = self._build_request(task, trace_id=trace_id)
        except ExecutionError as exc:
            return OperationResult.fail(
                "execution_invalid_task",
                exc.message,
                details=exc.details,
            )

        logger.info("Executing web search task")
        try:
            raw_response = await self._search_client.search(request)
        except Exception as exc:
            return OperationResult.fail(
                "execution_provider_failure",
                "Search provider call failed",
                retryable=isinstance(exc, SearchClientError),
                details={
                    "task_id": task.task_id,
                    "trace_id": trace_id,
                    "query": request.query,
                    "error": str(exc),
                },
            )

        try:
            response = SearchResponse.model_validate(raw_response)
            evidence = self._normalize_response(task, request, response)
        except (ExecutionError, ValidationError) as exc:
            message = exc.message if isinstance(exc, ExecutionError) else "Search provider payload was invalid"
            details = exc.details if isinstance(exc, ExecutionError) else {"errors": exc.errors()}
            logger.error("Search response normalization failed")
            return OperationResult.fail(
                "execution_invalid_provider_payload",
                message,
                details={
                    **details,
                    "task_id": task.task_id,
                    "trace_id": trace_id,
                    "query": request.query,
                },
            )

        logger.info("Web search task completed")
        return OperationResult.ok(evidence)

    def _build_request(self, task: TaskPacket, *, trace_id: str) -> SearchRequest:
        query = task.query.strip()
        if not query:
            raise ExecutionError(
                "Task query must not be empty",
                details={"task_id": task.task_id},
            )

        top_k = task.constraints.get("max_results", self._default_top_k)
        if not isinstance(top_k, int) or top_k < 1:
            raise ExecutionError(
                "Task max_results constraint must be a positive integer",
                details={"task_id": task.task_id, "max_results": top_k},
            )

        return SearchRequest(
            query=query,
            top_k=top_k,
            metadata={
                "component": "execution",
                "trace_id": trace_id,
                "task_id": task.task_id,
                "plan_id": task.plan_id,
                "step_id": task.step_id,
                "action": task.action,
                "tool_hint": str(task.constraints.get("tool_hint", task.action)),
            },
        )

    def _normalize_response(
        self,
        task: TaskPacket,
        request: SearchRequest,
        response: SearchResponse,
    ) -> list[EvidenceItem]:
        if not response.results:
            return []

        evidence_items: list[EvidenceItem] = []
        for result in response.results[: request.top_k]:
            evidence_items.append(self._normalize_result(task, request, result))
        return evidence_items

    def _normalize_result(
        self,
        task: TaskPacket,
        request: SearchRequest,
        result: SearchResultItem,
    ) -> EvidenceItem:
        snippet = result.snippet.strip()
        url = result.url.strip()
        if not snippet:
            raise ExecutionError(
                "Search result snippet must not be empty",
                details={"rank": result.rank, "url": url},
            )
        if not url:
            raise ExecutionError(
                "Search result URL must not be empty",
                details={"rank": result.rank},
            )

        normalized_score = result.score if result.score is not None else _rank_based_score(
            result.rank,
            request.top_k,
        )
        additional = {
            "rank": result.rank,
            "query": request.query,
            "source_name": result.source_name,
            "task_action": task.action,
            "raw_payload": result.raw_payload,
        }

        return EvidenceItem(
            evidence_id=generate_id(IDPrefix.EVIDENCE),
            task_id=task.task_id,
            content=snippet,
            source=SourceMetadata(
                source_type=SourceType.WEB_SEARCH,
                url=url,
                title=result.title,
                author=result.author,
                publication_date=result.publication_date,
                raw_snippet=snippet,
                additional=additional,
            ),
            confidence=normalized_score,
            relevance=normalized_score,
            tags=[task.action, task.expected_output_type],
        )


def _rank_based_score(rank: int, top_k: int) -> float:
    if top_k <= 1:
        return 1.0
    return max(0.0, min(1.0, 1.0 - ((rank - 1) / top_k)))
