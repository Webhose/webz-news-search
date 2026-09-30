from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from webzio_news_search.consts import (
    API_URL_ENV_NAME,
    DEFAULT_API_URL,
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    LIST_FILTERS,
    MAX_QUERY_CHARS,
    MAX_QUERY_WORDS,
    TOKEN_ENV_NAME,
    TOOL_NAME,
    USER_AGENT,
)
from webzio_news_search.errors import WebzAPIError, WebzConfigError
from webzio_news_search.models import NewsSearchResponse

TOP_LEVEL_KEYS = ("k", "score_gte", "score_lte", "allow_multiple_chunks_per_article")


def resolve_api_token(api_token: str | None = None) -> str:
    token = (api_token or os.getenv(TOKEN_ENV_NAME) or "").strip()
    if not token:
        raise WebzConfigError(
            f"missing Webz API token. set {TOKEN_ENV_NAME} or pass api_token."
        )
    return token


def resolve_api_url(api_url: str | None = None) -> str:
    url = (api_url or os.getenv(API_URL_ENV_NAME) or DEFAULT_API_URL).strip()
    if not url:
        raise WebzConfigError("missing News Search API url.")
    return url


def normalize_query(query: str) -> str:
    text = (query or "").strip()
    if not text:
        raise WebzConfigError("query is required.")
    if len(text) > MAX_QUERY_CHARS:
        raise WebzConfigError(
            f"query is too long: {len(text)} characters (max {MAX_QUERY_CHARS})."
        )
    words = len(text.split())
    if words > MAX_QUERY_WORDS:
        raise WebzConfigError(f"query is too long: {words} words (max {MAX_QUERY_WORDS}).")
    return text


def published_from_for_days(days: int, now: datetime | None = None) -> str:
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise WebzConfigError("days must be a non-negative integer.")
    current = now or datetime.now(timezone.utc)
    return (current - timedelta(days=days)).date().isoformat()


def normalize_filters(filters: dict[str, Any] | None, **extra: Any) -> dict[str, Any]:
    """
    merges explicit filter kwargs with a filters dict and normalizes list fields.

    params:
    - filters: raw filters object as the API expects it.
    - extra: filter names passed as keyword arguments.

    returns:
    - filters dict with empty values dropped and bare strings wrapped for list fields.
    """
    merged: dict[str, Any] = {}
    for source in (filters or {}, extra):
        for key, value in source.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, (list, tuple, set)):
                items = [str(item).strip() for item in value if str(item).strip()]
                if not items:
                    continue
                merged[key] = items
                continue
            if key in LIST_FILTERS:
                merged[key] = [str(value).strip()]
                continue
            merged[key] = value
    if "domain" in merged and "exclude_domain" in merged:
        overlap = set(merged["domain"]) & set(merged["exclude_domain"])
        if overlap:
            raise WebzConfigError(
                f"a domain cannot be in both domain and exclude_domain: {sorted(overlap)}"
            )
    return merged


def build_request_body(
    query: str,
    *,
    k: int | None = None,
    days: int | None = None,
    score_gte: float | None = None,
    score_lte: float | None = None,
    allow_multiple_chunks_per_article: bool | None = None,
    filters: dict[str, Any] | None = None,
    **filter_kwargs: Any,
) -> dict[str, Any]:
    """
    builds the JSON body for POST /api/news/context.

    params:
    - query: natural-language topic or question.
    - k: max articles to return.
    - days: shorthand that sets filters.published_from to today minus days (UTC).
    - score_gte / score_lte: match-score bounds, 0-10.
    - allow_multiple_chunks_per_article: return more than one chunk per article.
    - filters: filters object passed through to the API.
    - filter_kwargs: any filter name as a keyword (language=..., ticker=...).

    returns:
    - request body dict with empty values removed.
    """
    body: dict[str, Any] = {"query": normalize_query(query)}
    if k is not None:
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise WebzConfigError("k must be a positive integer.")
        body["k"] = k
    if score_gte is not None:
        body["score_gte"] = score_gte
    if score_lte is not None:
        body["score_lte"] = score_lte
    if score_gte is not None and score_lte is not None and score_gte > score_lte:
        raise WebzConfigError("score_gte cannot be greater than score_lte.")
    if allow_multiple_chunks_per_article is not None:
        body["allow_multiple_chunks_per_article"] = bool(allow_multiple_chunks_per_article)

    # top-level keys handed in through the filters dict are lifted out of it
    remaining_filters = dict(filters or {})
    for key in TOP_LEVEL_KEYS:
        for source in (remaining_filters, filter_kwargs):
            if key in source:
                value = source.pop(key)
                if key not in body and value is not None:
                    body[key] = value

    merged = normalize_filters(remaining_filters, **filter_kwargs)
    if days is not None:
        if "published_from" in merged:
            raise WebzConfigError("pass either days or published_from, not both.")
        merged["published_from"] = published_from_for_days(days)
    if merged:
        body["filters"] = merged
    return body


def request_headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def extract_error_detail(response: httpx.Response) -> str:
    text = (response.text or "").strip()
    if not text:
        return ""
    try:
        payload = response.json()
    except ValueError:
        return text[:500]
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or payload.get("error")
        if isinstance(detail, str):
            return detail
        if detail is not None:
            return json.dumps(detail)[:500]
    return text[:500]


def parse_response(response: httpx.Response, query: str) -> NewsSearchResponse:
    if response.status_code >= 400:
        raise WebzAPIError(response.status_code, extract_error_detail(response))
    try:
        payload = response.json()
    except ValueError as exc:
        raise WebzAPIError(response.status_code, "response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise WebzAPIError(response.status_code, "response was not a JSON object")
    return NewsSearchResponse.from_dict(payload, query=query)


def build_timeout(timeout: float | httpx.Timeout | None) -> httpx.Timeout:
    if isinstance(timeout, httpx.Timeout):
        return timeout
    seconds = DEFAULT_TIMEOUT_SECONDS if timeout is None else float(timeout)
    return httpx.Timeout(seconds, connect=min(seconds, DEFAULT_CONNECT_TIMEOUT_SECONDS))


def tool_definition() -> dict[str, Any]:
    """
    returns a JSON-schema function definition for LLM tool calling.

    the shape matches the OpenAI / Anthropic function-calling format:
    {"name", "description", "parameters"}.
    """
    string_list = {"type": "array", "items": {"type": "string"}}
    return {
        "name": TOOL_NAME,
        "description": (
            "Search global news from the last 30 days with Webz.io. Ask in natural "
            "language; results are ranked by meaning and return the title, URL, publish "
            "date, source metadata, and the most relevant excerpt of each article."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language topic or question (max 750 characters).",
                },
                "k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Number of articles to return. Default 10.",
                },
                "days": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Only articles published in the last N days (max coverage is 30).",
                },
                "score_gte": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "description": "Minimum match score 0-10. Default 4. Use 0 to disable.",
                },
                "score_lte": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "description": "Maximum match score 0-10.",
                },
                "language": {**string_list, "description": "Article languages, e.g. [\"english\"]."},
                "country": {**string_list, "description": "Source countries as ISO-2 codes, e.g. [\"US\", \"GB\"]."},
                "category": {**string_list, "description": "One of the 17 article categories, e.g. [\"Politics\"]."},
                "sentiment": {**string_list, "description": "positive, negative, or neutral."},
                "published_from": {"type": "string", "description": "Earliest publish date, YYYY-MM-DD."},
                "published_to": {"type": "string", "description": "Latest publish date, YYYY-MM-DD."},
                "domain": {**string_list, "description": "Only these source domains, e.g. [\"cnn.com\"]."},
                "exclude_domain": {**string_list, "description": "Skip these source domains."},
                "topic": {**string_list, "description": "Topic tags, finer than category."},
                "person": {**string_list, "description": "People mentioned in the article."},
                "organization": {**string_list, "description": "Organizations mentioned in the article."},
                "location": {**string_list, "description": "Locations mentioned in the article."},
                "ticker": {**string_list, "description": "Stock tickers of mentioned organizations, e.g. [\"NVDA\"]."},
                "political_bias": {**string_list, "description": "Source bias: left, center, or right."},
                "trust_category": {"type": "string", "description": "trusted_news, fake_news, or satirical_news."},
                "source_type": {"type": "string", "description": "local_news, newsroom, or gov_news."},
                "domain_rank_gte": {"type": "integer", "description": "Minimum Tranco domain rank (1 = most popular)."},
                "domain_rank_lte": {"type": "integer", "description": "Maximum Tranco domain rank."},
                "allow_multiple_chunks_per_article": {
                    "type": "boolean",
                    "description": "Return more than one matching passage from the same article.",
                },
            },
            "required": ["query"],
        },
    }


def openai_tool_definition() -> dict[str, Any]:
    """wraps tool_definition() in the OpenAI chat-completions tools envelope."""
    return {"type": "function", "function": tool_definition()}


class WebzNewsSearch:
    """
    client for the Webz.io News Search API (POST /api/news/context).

    params:
    - api_token: webz api token. defaults to WEBZ_API_TOKEN.
    - api_url: endpoint override. defaults to production.
    - timeout: seconds or an httpx.Timeout.
    - client: optional httpx.Client to reuse connections.
    - async_client: optional httpx.AsyncClient for asearch().
    """

    def __init__(
        self,
        api_token: str | None = None,
        api_url: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_token = resolve_api_token(api_token)
        self.api_url = resolve_api_url(api_url)
        self.timeout = build_timeout(timeout)
        self._client = client
        self._owns_client = client is None
        self._async_client = async_client
        self._owns_async_client = async_client is None

    # lifecycle

    def __enter__(self) -> WebzNewsSearch:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    async def __aenter__(self) -> WebzNewsSearch:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def close(self) -> None:
        if self._client is not None and self._owns_client:
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        if self._async_client is not None and self._owns_async_client:
            await self._async_client.aclose()
            self._async_client = None

    def _sync_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    # search

    def search(
        self,
        query: str,
        *,
        k: int | None = None,
        days: int | None = None,
        score_gte: float | None = None,
        score_lte: float | None = None,
        allow_multiple_chunks_per_article: bool | None = None,
        filters: dict[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> NewsSearchResponse:
        """
        runs one News Search request.

        params:
        - query: natural-language topic or question.
        - k: max articles (default 10 on the server).
        - days: shorthand for filters.published_from.
        - score_gte / score_lte: match-score bounds.
        - allow_multiple_chunks_per_article: more than one passage per article.
        - filters: filters object as documented by Webz.
        - filter_kwargs: filter names as keywords, e.g. language=["english"].

        returns:
        - NewsSearchResponse with typed results and the raw payload.
        """
        body = build_request_body(
            query,
            k=k,
            days=days,
            score_gte=score_gte,
            score_lte=score_lte,
            allow_multiple_chunks_per_article=allow_multiple_chunks_per_article,
            filters=filters,
            **filter_kwargs,
        )
        try:
            response = self._sync_client().post(
                self.api_url, headers=request_headers(self.api_token), json=body
            )
        except httpx.HTTPError as exc:
            raise WebzAPIError(0, f"could not reach {self.api_url}: {exc}") from exc
        return parse_response(response, body["query"])

    async def asearch(
        self,
        query: str,
        *,
        k: int | None = None,
        days: int | None = None,
        score_gte: float | None = None,
        score_lte: float | None = None,
        allow_multiple_chunks_per_article: bool | None = None,
        filters: dict[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> NewsSearchResponse:
        body = build_request_body(
            query,
            k=k,
            days=days,
            score_gte=score_gte,
            score_lte=score_lte,
            allow_multiple_chunks_per_article=allow_multiple_chunks_per_article,
            filters=filters,
            **filter_kwargs,
        )
        try:
            response = await self._get_async_client().post(
                self.api_url, headers=request_headers(self.api_token), json=body
            )
        except httpx.HTTPError as exc:
            raise WebzAPIError(0, f"could not reach {self.api_url}: {exc}") from exc
        return parse_response(response, body["query"])

    # tool calling

    @staticmethod
    def tool_definition() -> dict[str, Any]:
        return tool_definition()

    @staticmethod
    def openai_tool_definition() -> dict[str, Any]:
        return openai_tool_definition()

    def run_tool(self, arguments: dict[str, Any] | str) -> str:
        """
        executes a tool call from an LLM and returns prompt-ready text.

        params:
        - arguments: the parsed tool arguments, or the JSON string from the model.

        returns:
        - NewsSearchResponse.to_text() output.
        """
        params = _parse_tool_arguments(arguments)
        query = params.pop("query", "")
        return self.search(query, **params).to_text()

    async def arun_tool(self, arguments: dict[str, Any] | str) -> str:
        params = _parse_tool_arguments(arguments)
        query = params.pop("query", "")
        response = await self.asearch(query, **params)
        return response.to_text()


def _parse_tool_arguments(arguments: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments or "{}")
        except json.JSONDecodeError as exc:
            raise WebzConfigError(f"tool arguments must be valid JSON: {exc.msg}") from exc
    else:
        parsed = arguments
    if not isinstance(parsed, dict):
        raise WebzConfigError("tool arguments must be a JSON object.")
    return dict(parsed)


def news_search(query: str, api_token: str | None = None, **kwargs: Any) -> NewsSearchResponse:
    """one-shot helper: builds a client, runs search(), and closes it."""
    with WebzNewsSearch(api_token=api_token) as client:
        return client.search(query, **kwargs)


async def anews_search(
    query: str, api_token: str | None = None, **kwargs: Any
) -> NewsSearchResponse:
    async with WebzNewsSearch(api_token=api_token) as client:
        return await client.asearch(query, **kwargs)
