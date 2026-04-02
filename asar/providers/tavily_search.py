"""
Tavily-backed implementation of ASAR's typed search client protocol.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from asar.core.errors import ConfigurationError, SearchClientError
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem


class TavilySearchClient:
    """Minimal Tavily adapter for the v0 web-search executor."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        topic: str = "general",
        timeout_seconds: float = 30.0,
        endpoint: str = "https://api.tavily.com/search",
    ) -> None:
        resolved_api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not resolved_api_key:
            raise ConfigurationError(
                "Live Tavily mode requires TAVILY_API_KEY",
                details={"env_var": "TAVILY_API_KEY"},
            )

        self._api_key = resolved_api_key
        self._topic = topic
        self._timeout_seconds = timeout_seconds
        self._endpoint = endpoint

    async def search(self, request: SearchRequest) -> SearchResponse:
        return await asyncio.to_thread(self._search_sync, request)

    def _search_sync(self, request: SearchRequest) -> SearchResponse:
        body = json.dumps(
            {
                "query": request.query,
                "topic": self._topic,
                "max_results": request.top_k,
                "include_answer": False,
                "include_raw_content": False,
            }
        ).encode("utf-8")
        http_request = Request(
            self._endpoint,
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = {
                "status": exc.code,
                "query": request.query,
            }
            error_body = _read_error_body(exc)
            if error_body is not None:
                details["provider_error"] = error_body
                hint = _tavily_hint(exc.code, error_body)
                if hint is not None:
                    details["hint"] = hint
            raise SearchClientError(
                "Tavily search request failed",
                details=details,
                retryable=False,
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SearchClientError(
                "Tavily search request failed",
                details={"query": request.query, "error": str(exc)},
                retryable=False,
            ) from exc

        return SearchResponse(results=_normalize_tavily_results(payload, top_k=request.top_k))


def _normalize_tavily_results(payload: dict[str, Any], *, top_k: int) -> list[SearchResultItem]:
    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        raise SearchClientError(
            "Tavily returned an unexpected payload shape",
            details={"top_level_keys": sorted(payload.keys())},
        )

    normalized: list[SearchResultItem] = []
    for rank, item in enumerate(raw_results[:top_k], start=1):
        if not isinstance(item, dict):
            continue

        url = _coerce_str(item.get("url"))
        snippet = _coerce_str(item.get("content"))
        title = _coerce_optional_str(item.get("title"))
        publication_date = _coerce_optional_str(item.get("published_date"))
        score = _coerce_optional_score(item.get("score"))

        if not url or not snippet:
            continue

        normalized.append(
            SearchResultItem(
                url=url,
                snippet=snippet,
                title=title,
                publication_date=publication_date,
                rank=rank,
                score=score,
                source_name=_source_name(url),
                raw_payload=item,
            )
        )

    return normalized


def _coerce_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _coerce_optional_str(value: Any) -> str | None:
    coerced = _coerce_str(value)
    return coerced or None


def _coerce_optional_score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _source_name(url: str) -> str | None:
    hostname = urlparse(url).hostname
    if not hostname:
        return None
    return hostname.removeprefix("www.")


def _read_error_body(exc: HTTPError) -> dict[str, Any] | str | None:
    try:
        raw_body = exc.read().decode("utf-8").strip()
    except Exception:
        return None
    if not raw_body:
        return None
    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body
    return decoded if isinstance(decoded, dict | str) else raw_body


def _tavily_hint(status: int, provider_error: dict[str, Any] | str) -> str | None:
    lowered = json.dumps(provider_error).lower() if isinstance(provider_error, dict) else provider_error.lower()
    if status in {401, 403}:
        return "Tavily rejected the request. Check that TAVILY_API_KEY is real and active."
    if status == 429:
        return "Tavily rate limited the request. Retry later or reduce request frequency."
    if "unauthorized" in lowered or "invalid api key" in lowered:
        return "Tavily rejected the API key. Check that TAVILY_API_KEY is real and active."
    return None
