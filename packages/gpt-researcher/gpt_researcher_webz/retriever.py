"""GPT Researcher retriever for the Webz.io News Search API."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlsplit

import httpx
from webzio_news_search import WebzAPIError, WebzConfigError, WebzNewsSearch
from webzio_news_search.consts import DEFAULT_API_URL, TOKEN_ENV_NAME
from webzio_news_search.models import NewsResult, NewsSearchResponse

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "gpt_researcher.retrievers"
ENTRY_POINT_NAME = "webz"
API_URL_ENV_NAME = "WEBZ_NEWS_SEARCH_URL"
HEADER_TOKEN_KEY = "webz_api_key"


class WebzRetrieverError(ValueError):
    """Raised when the retriever is missing a token or given an unsafe endpoint."""


class WebzSearch:
    """News search retriever registered as ``RETRIEVER=webz``.

    GPT Researcher constructs this with the sub-query and an optional domain
    list, then calls ``search(max_results=...)``. Each hit has ``href`` and
    ``body``. ``requires_scraping`` stays true because ``body`` is an excerpt,
    and the page is fetched later for the citation.

    The token is read from ``headers['webz_api_key']`` when that dict is
    passed in, otherwise from ``WEBZ_API_TOKEN``. The live GPT Researcher
    search path passes ``query`` and ``query_domains`` only, so the
    environment variable is the setting ``RETRIEVER=webz`` uses.
    """

    requires_scraping = True

    def __init__(
        self,
        query: str,
        query_domains: list[str] | str | None = None,
        headers: dict[str, Any] | None = None,
        *,
        client: httpx.Client | None = None,
        **_ignored: Any,
    ) -> None:
        self.query = query
        self.query_domains = _domain_list(query_domains)
        self.headers = headers if isinstance(headers, dict) else {}
        self.api_token = _resolve_token(self.headers)
        self.api_url = _resolve_https_url()
        self._client = client

    def search(self, max_results: int = 7) -> list[dict[str, str]]:
        """Return up to ``max_results`` articles as ``{"href", "body"}`` dicts.

        Network and response-parse failures return an empty list so one
        provider does not abort a research run. A missing token or a
        non-HTTPS endpoint raises ``WebzRetrieverError`` before the token
        is sent.
        """
        owns_client = self._client is None
        http_client = self._client or httpx.Client(
            timeout=httpx.Timeout(60.0, connect=15.0),
            follow_redirects=False,
        )
        try:
            searcher = WebzNewsSearch(
                api_token=self.api_token,
                api_url=self.api_url,
                client=http_client,
            )
            try:
                response = searcher.search(
                    self.query,
                    k=max_results,
                    **self._filter_kwargs(),
                )
            except WebzConfigError:
                raise
            except (WebzAPIError, httpx.HTTPError, ValueError) as exc:
                logger.warning("Webz retriever search failed: %s", exc)
                return []
            return _map_results(response)
        finally:
            if owns_client:
                http_client.close()

    def _filter_kwargs(self) -> dict[str, list[str]]:
        if not self.query_domains:
            return {}
        return {"domain": self.query_domains}


def _resolve_token(headers: dict[str, Any]) -> str:
    from_header = headers.get(HEADER_TOKEN_KEY)
    header_token = str(from_header).strip() if from_header else ""
    token = header_token or (os.getenv(TOKEN_ENV_NAME) or "").strip()
    if not token:
        raise WebzRetrieverError(
            "Webz API token not found. Set the WEBZ_API_TOKEN environment "
            "variable, or pass webz_api_key in headers. Get a token from "
            "https://webz.io/."
        )
    return token


def _resolve_https_url() -> str:
    url = (os.getenv(API_URL_ENV_NAME) or DEFAULT_API_URL).strip()
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise WebzRetrieverError(
            "The Webz.io News Search API endpoint must be an absolute "
            f"https:// URL, got {url!r}."
        )
    return url


def _domain_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    items = [value] if isinstance(value, str) else list(value)
    return [str(item).strip() for item in items if str(item).strip()]


def _preview(result: NewsResult) -> str:
    """Lead the snippet with title, source, and publish time.

    GPT Researcher stringifies the first search response into the planning
    prompt. Tavily and Exa put only the snippet in ``body``; news hits carry
    a title, domain, and publish time that the planner otherwise never sees,
    so those three lines sit in front of the excerpt.
    """
    excerpt = (result.text or result.article.summary or "").strip()
    lines: list[str] = []
    title = (result.title or "").strip()
    if title:
        lines.append(title)
    source = (result.domain or "").strip()
    if source:
        lines.append(f"Source: {source}")
    published = (result.article.published_at or "").strip()
    if published:
        lines.append(f"Published: {published}")
    if lines and excerpt:
        return "\n".join(lines) + "\n\n" + excerpt
    if lines:
        return "\n".join(lines)
    return excerpt


def _map_results(response: NewsSearchResponse) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for result in response.results:
        href = (result.url or "").strip()
        if not href:
            continue
        hits.append({"href": href, "body": _preview(result)})
    return hits
