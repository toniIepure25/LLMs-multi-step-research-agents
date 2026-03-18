"""
Brave Search-backed implementation of ASAR's typed search client protocol.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from asar.core.errors import ConfigurationError, SearchClientError
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem


class BraveSearchClient:
    """Minimal Brave Search adapter for the v0 web-search executor."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        country: str | None = None,
        search_lang: str | None = None,
        timeout_seconds: float = 30.0,
        endpoint: str = "https://api.search.brave.com/res/v1/web/search",
    ) -> None:
        resolved_api_key = api_key or os.environ.get("BRAVE_SEARCH_API_KEY")
        if not resolved_api_key:
            raise ConfigurationError(
                "Live Brave Search mode requires BRAVE_SEARCH_API_KEY",
                details={"env_var": "BRAVE_SEARCH_API_KEY"},
            )

        self._api_key = resolved_api_key
        self._country = country or os.environ.get("ASAR_BRAVE_SEARCH_COUNTRY", "US")
        self._search_lang = search_lang or os.environ.get("ASAR_BRAVE_SEARCH_LANG", "en")
        self._timeout_seconds = timeout_seconds
        self._endpoint = endpoint

    async def search(self, request: SearchRequest) -> SearchResponse:
        return await asyncio.to_thread(self._search_sync, request)

    def _search_sync(self, request: SearchRequest) -> SearchResponse:
        params = {
            "q": request.query,
            "count": str(request.top_k),
            "country": self._country,
            "search_lang": self._search_lang,
        }
        url = f"{self._endpoint}?{urlencode(params)}"
        http_request = Request(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self._api_key,
            },
        )

        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise SearchClientError(
                "Brave Search request failed",
                details={"status": exc.code, "query": request.query},
                retryable=False,
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SearchClientError(
                "Brave Search request failed",
                details={"query": request.query, "error": str(exc)},
                retryable=False,
            ) from exc

        return SearchResponse(results=_normalize_brave_results(payload, top_k=request.top_k))


def _normalize_brave_results(payload: dict[str, Any], *, top_k: int) -> list[SearchResultItem]:
    raw_results = payload.get("web", {}).get("results", [])
    if not isinstance(raw_results, list):
        raise SearchClientError(
            "Brave Search returned an unexpected payload shape",
            details={"top_level_keys": sorted(payload.keys())},
        )

    normalized: list[SearchResultItem] = []
    for rank, item in enumerate(raw_results[:top_k], start=1):
        if not isinstance(item, dict):
            continue

        url = _coerce_str(item.get("url"))
        snippet = _coerce_str(item.get("description"))
        title = _coerce_optional_str(item.get("title"))

        if not url or not snippet:
            continue

        normalized.append(
            SearchResultItem(
                url=url,
                snippet=snippet,
                title=title,
                rank=rank,
                source_name=_profile_name(item.get("profile")),
                raw_payload=item,
            )
        )

    return normalized


def _coerce_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _coerce_optional_str(value: Any) -> str | None:
    coerced = _coerce_str(value)
    return coerced or None


def _profile_name(profile: Any) -> str | None:
    if isinstance(profile, dict):
        for key in ("long_name", "name"):
            candidate = _coerce_optional_str(profile.get(key))
            if candidate:
                return candidate
    return None
