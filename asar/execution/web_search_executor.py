"""
Minimal v0 web/search executor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import ValidationError

from asar.common import (
    ASARSettings,
    IDPrefix,
    generate_id,
    generate_trace_id,
    get_logger,
    setup_logging,
)
from asar.core.errors import ExecutionError, SearchClientError
from asar.core.result import OperationResult
from asar.core.search import (
    SearchClientProtocol,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.task_packet import TaskPacket

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "analyze",
        "as",
        "at",
        "by",
        "define",
        "describe",
        "determine",
        "examine",
        "find",
        "focus",
        "focusing",
        "for",
        "from",
        "gather",
        "how",
        "identify",
        "in",
        "into",
        "investigate",
        "is",
        "it",
        "its",
        "main",
        "of",
        "on",
        "research",
        "role",
        "scope",
        "search",
        "step",
        "steps",
        "synthesize",
        "the",
        "their",
        "these",
        "this",
        "timeline",
        "to",
        "up",
        "were",
        "what",
        "which",
        "with",
    }
)
_GENERIC_TOPIC_TERMS = frozenset(
    {
        "bubble",
        "bubbles",
        "cause",
        "causes",
        "crash",
        "crashes",
        "crisis",
        "crises",
        "depression",
        "driver",
        "drivers",
        "event",
        "events",
        "factor",
        "factors",
        "failure",
        "failures",
        "impact",
        "impacts",
        "lead",
        "leading",
        "major",
        "reason",
        "reasons",
    }
)
_INCIDENT_NOISE_TERMS = frozenset(
    {
        "accident",
        "accidents",
        "autonomous",
        "car",
        "cars",
        "driver",
        "drivers",
        "fatalities",
        "fatality",
        "highway",
        "intersection",
        "intersections",
        "road",
        "roads",
        "safety",
        "traffic",
        "vehicle",
        "vehicles",
    }
)


@dataclass(frozen=True)
class _SelectionProfile:
    query_terms: set[str]
    goal_terms: set[str]
    query_anchor_terms: set[str]
    goal_anchor_terms: set[str]


class WebSearchExecutor:
    """Execute one `TaskPacket` through a typed search client."""

    def __init__(
        self,
        search_client: SearchClientProtocol,
        settings: ASARSettings,
        *,
        default_top_k: int = 3,
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
            details = {
                "task_id": task.task_id,
                "trace_id": trace_id,
                "query": request.query,
                "error": str(exc),
            }
            if isinstance(exc, SearchClientError) and exc.details:
                details["search_error_details"] = exc.details
            return OperationResult.fail(
                "execution_provider_failure",
                "Search provider call failed",
                retryable=isinstance(exc, SearchClientError),
                details=details,
            )

        try:
            response = SearchResponse.model_validate(raw_response)
            evidence = self._normalize_response(task, request, response)
        except (ExecutionError, ValidationError) as exc:
            message = (
                exc.message
                if isinstance(exc, ExecutionError)
                else "Search provider payload was invalid"
            )
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
        for result in _select_results(
            response.results,
            top_k=request.top_k,
            profile=_selection_profile(task, request),
        ):
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


def _select_results(
    results: list[SearchResultItem],
    *,
    top_k: int,
    profile: _SelectionProfile,
) -> list[SearchResultItem]:
    deduped: list[SearchResultItem] = []
    seen_urls: set[str] = set()

    for result in results:
        normalized_url = result.url.strip().lower().rstrip("/")
        if normalized_url and normalized_url in seen_urls:
            continue
        if normalized_url:
            seen_urls.add(normalized_url)

        deduped.append(result)
        if len(deduped) >= top_k * 2:
            break

    if not deduped:
        return []

    scored_results = []
    for result in deduped:
        result_terms = _informative_tokens(f"{result.title} {result.snippet}")
        query_overlap = len(profile.query_terms & result_terms)
        goal_overlap = len(profile.goal_terms & result_terms)
        matched_query_anchor_terms = profile.query_anchor_terms & result_terms
        matched_goal_anchor_terms = profile.goal_anchor_terms & result_terms
        anchor_overlap = len(matched_query_anchor_terms | matched_goal_anchor_terms)
        is_incident_noise = _is_incident_noise_result(
            profile=profile,
            result_terms=result_terms,
            matched_anchor_terms=matched_query_anchor_terms | matched_goal_anchor_terms,
        )
        scored_results.append(
            {
                "result": result,
                "result_terms": result_terms,
                "query_overlap": query_overlap,
                "goal_overlap": goal_overlap,
                "query_anchor_overlap": len(matched_query_anchor_terms),
                "goal_anchor_overlap": len(matched_goal_anchor_terms),
                "anchor_overlap": anchor_overlap,
                "total_overlap": len((profile.query_terms | profile.goal_terms) & result_terms),
                "is_incident_noise": is_incident_noise,
                "is_goal_anchor_misaligned": _is_goal_anchor_misaligned(
                    profile=profile,
                    matched_query_anchor_terms=matched_query_anchor_terms,
                    matched_goal_anchor_terms=matched_goal_anchor_terms,
                ),
            }
        )

    goal_anchor_matches_available = any(
        item["goal_anchor_overlap"] > 0 for item in scored_results if not item["is_incident_noise"]
    )
    scored_results.sort(
        key=lambda item: (
            item["is_incident_noise"],
            item["is_goal_anchor_misaligned"],
            -item["goal_anchor_overlap"],
            -item["anchor_overlap"],
            -item["total_overlap"],
            -(item["result"].score or 0.0),
            item["result"].rank,
        )
    )

    minimum_overlap = _minimum_overlap(profile.query_terms | profile.goal_terms)
    strong_matches = [
        item
        for item in scored_results
        if not item["is_incident_noise"]
        and not item["is_goal_anchor_misaligned"]
        and (
            item["goal_anchor_overlap"] > 0
            if goal_anchor_matches_available
            else item["anchor_overlap"] > 0 or item["total_overlap"] >= minimum_overlap
        )
    ]
    weak_matches = [
        item
        for item in scored_results
        if not item["is_incident_noise"]
        and not item["is_goal_anchor_misaligned"]
        and item["total_overlap"] > 0
        and (
            not goal_anchor_matches_available
            or item["goal_anchor_overlap"] > 0
        )
        and item not in strong_matches
    ]

    selected: list[SearchResultItem] = []
    for item in strong_matches:
        selected.append(item["result"])
        if len(selected) >= top_k:
            return selected

    for item in weak_matches:
        selected.append(item["result"])
        if len(selected) >= top_k:
            return selected

    if selected:
        return selected

    return deduped[:top_k]


def _selection_profile(task: TaskPacket, request: SearchRequest) -> _SelectionProfile:
    query_terms = _informative_tokens(request.query)
    goal_terms = _informative_tokens(_context_goal(task.context))
    query_anchor_terms = {
        token for token in query_terms if token not in _GENERIC_TOPIC_TERMS
    }
    goal_anchor_terms = {
        token for token in goal_terms if token not in _GENERIC_TOPIC_TERMS
    }
    if not query_anchor_terms:
        query_anchor_terms = set(query_terms)
    return _SelectionProfile(
        query_terms=query_terms,
        goal_terms=goal_terms,
        query_anchor_terms=query_anchor_terms,
        goal_anchor_terms=goal_anchor_terms,
    )


def _context_goal(context: str | None) -> str:
    if context is None or not context.strip():
        return ""

    stripped = context.strip()
    if not stripped.startswith("{"):
        return ""

    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        return ""

    if not isinstance(decoded, dict):
        return ""

    goal = decoded.get("goal")
    return goal if isinstance(goal, str) else ""


def _minimum_overlap(query_terms: set[str]) -> int:
    if len(query_terms) <= 3:
        return 1
    return 2


def _is_incident_noise_result(
    *,
    profile: _SelectionProfile,
    result_terms: set[str],
    matched_anchor_terms: set[str],
) -> bool:
    non_numeric_anchor_matches = {term for term in matched_anchor_terms if not term.isdigit()}
    if non_numeric_anchor_matches:
        return False
    if (profile.query_anchor_terms | profile.goal_anchor_terms) & _INCIDENT_NOISE_TERMS:
        return False
    return bool(result_terms & _INCIDENT_NOISE_TERMS)


def _is_goal_anchor_misaligned(
    *,
    profile: _SelectionProfile,
    matched_query_anchor_terms: set[str],
    matched_goal_anchor_terms: set[str],
) -> bool:
    meaningful_goal_anchors = {term for term in profile.goal_anchor_terms if not term.isdigit()}
    if not meaningful_goal_anchors:
        return False

    matched_meaningful_goal_anchors = {
        term for term in matched_goal_anchor_terms if not term.isdigit()
    }
    if matched_meaningful_goal_anchors:
        return False

    return bool(matched_query_anchor_terms)


def _informative_tokens(text: str) -> set[str]:
    normalized = text.lower().replace("dot-com", "dotcom").replace("dot com", "dotcom")
    normalized = normalized.replace("-", " ")
    return {
        token
        for token in _TOKEN_PATTERN.findall(normalized)
        if token not in _STOPWORDS and len(token) > 1
    }
