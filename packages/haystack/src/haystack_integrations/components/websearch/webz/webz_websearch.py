# SPDX-FileCopyrightText: 2026-present Webz.io <support@webz.io>
#
# SPDX-License-Identifier: MIT

import os
from typing import Any
from urllib.parse import urlsplit

import httpx
from haystack import Document, component
from haystack.utils import Secret
from webzio_news_search import NewsSearchResponse, WebzNewsSearch
from webzio_news_search.consts import (
    API_URL_ENV_NAME,
    DEFAULT_API_URL,
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    TOKEN_ENV_NAME,
)

_META_KEYS = (
    "language",
    "country",
    "category",
    "sentiment",
    "topic",
    "person",
    "organization",
    "location",
    "ticker",
)


def _require_https(url: str) -> str:
    """
    Reject any News Search URL that is not absolute HTTPS.

    :param url: Endpoint candidate from the constructor or the environment.
    :returns: The stripped URL when its scheme is ``https``.
    """
    cleaned = url.strip()
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        msg = f"The Webz.io News Search API endpoint must be an absolute https:// URL, got {url!r}."
        raise ValueError(msg)
    return cleaned


@component
class WebzWebSearch:
    """
    Search recent news with Webz.io and return Haystack documents.

    The component calls ``POST https://api.webz.io/api/news/context``. Coverage is the
    last 30 days. ``days`` is not an API field; it is sent as ``filters.published_from``.

    ### Usage example

    ```python
    from haystack import Pipeline
    from haystack_integrations.components.websearch.webz import WebzWebSearch

    pipeline = Pipeline()
    pipeline.add_component("news", WebzWebSearch(top_k=5, days=7))
    result = pipeline.run({"news": {"query": "recent developments on EU AI regulation"}})
    documents = result["news"]["documents"]
    ```
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var(TOKEN_ENV_NAME),  # noqa: B008
        top_k: int = 10,
        *,
        api_url: str | None = None,
        language: list[str] | str | None = None,
        country: list[str] | str | None = None,
        domain: list[str] | str | None = None,
        days: int | None = None,
        score_gte: float | None = None,
        score_lte: float | None = None,
    ) -> None:
        """
        Create a Webz news search component.

        :param api_key:
            Webz API token. Defaults to the ``WEBZ_API_TOKEN`` environment variable.
        :param top_k: Maximum number of articles. Sent as ``k``.
        :param api_url:
            News Search endpoint. Defaults to ``WEBZ_NEWS_SEARCH_URL`` or the production
            HTTPS URL. Any other scheme is rejected before the token is sent.
        :param language: Article languages, for example ``["english"]``.
        :param country: Source countries as ISO-2 codes, for example ``["US"]``.
        :param domain: Only these source domains, for example ``["reuters.com"]``.
        :param days:
            Keep articles published in the last N days. Mapped to ``filters.published_from``.
        :param score_gte: Minimum match score, 0-10.
        :param score_lte: Maximum match score, 0-10.
        """
        self.api_key = api_key
        self.top_k = top_k
        self.api_url = api_url
        self.language = language
        self.country = country
        self.domain = domain
        self.days = days
        self.score_gte = score_gte
        self.score_lte = score_lte
        self._http_client: httpx.Client | None = None
        self._async_http_client: httpx.AsyncClient | None = None

    @component.output_types(documents=list[Document], links=list[str])
    def run(
        self,
        query: str,
        *,
        top_k: int | None = None,
        language: list[str] | str | None = None,
        country: list[str] | str | None = None,
        domain: list[str] | str | None = None,
        days: int | None = None,
        score_gte: float | None = None,
        score_lte: float | None = None,
    ) -> dict[str, Any]:
        """
        Search news and return documents plus links.

        :param query: Natural-language topic or question.
        :param top_k: Overrides the init-time ``top_k`` for this call.
        :param language: Overrides the init-time language filter.
        :param country: Overrides the init-time country filter.
        :param domain: Overrides the init-time domain filter.
        :param days: Overrides the init-time day window.
        :param score_gte: Overrides the init-time minimum score.
        :param score_lte: Overrides the init-time maximum score.
        :returns: A dictionary with:
            - ``documents``: one Document per article. ``content`` is the matching excerpt.
            - ``links``: URLs from those documents.
        """
        response = self._search_sync(
            query,
            top_k=top_k,
            language=language,
            country=country,
            domain=domain,
            days=days,
            score_gte=score_gte,
            score_lte=score_lte,
        )
        return _documents_from_response(response)

    @component.output_types(documents=list[Document], links=list[str])
    async def run_async(
        self,
        query: str,
        *,
        top_k: int | None = None,
        language: list[str] | str | None = None,
        country: list[str] | str | None = None,
        domain: list[str] | str | None = None,
        days: int | None = None,
        score_gte: float | None = None,
        score_lte: float | None = None,
    ) -> dict[str, Any]:
        """
        Search news asynchronously and return documents plus links.

        :param query: Natural-language topic or question.
        :param top_k: Overrides the init-time ``top_k`` for this call.
        :param language: Overrides the init-time language filter.
        :param country: Overrides the init-time country filter.
        :param domain: Overrides the init-time domain filter.
        :param days: Overrides the init-time day window.
        :param score_gte: Overrides the init-time minimum score.
        :param score_lte: Overrides the init-time maximum score.
        :returns: A dictionary with:
            - ``documents``: one Document per article. ``content`` is the matching excerpt.
            - ``links``: URLs from those documents.
        """
        response = await self._search_async(
            query,
            top_k=top_k,
            language=language,
            country=country,
            domain=domain,
            days=days,
            score_gte=score_gte,
            score_lte=score_lte,
        )
        return _documents_from_response(response)

    def _resolve_api_url(self) -> str:
        if self.api_url is not None:
            raw = self.api_url
        else:
            raw = os.getenv(API_URL_ENV_NAME) or DEFAULT_API_URL
        return _require_https(raw)

    def _resolve_token(self) -> str:
        value = self.api_key.resolve_value()
        token = (value or "").strip()
        if not token:
            msg = f"missing Webz API token. set {TOKEN_ENV_NAME} or pass api_key."
            raise ValueError(msg)
        return token

    def _endpoint_and_token(self) -> tuple[str, str]:
        # Validate the URL before the token is read, so a cleartext endpoint never
        # proceeds to a request that would send the bearer token.
        url = self._resolve_api_url()
        token = self._resolve_token()
        return url, token

    def _search_kwargs(
        self,
        *,
        top_k: int | None,
        language: list[str] | str | None,
        country: list[str] | str | None,
        domain: list[str] | str | None,
        days: int | None,
        score_gte: float | None,
        score_lte: float | None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"k": self.top_k if top_k is None else top_k}
        resolved_language = self.language if language is None else language
        resolved_country = self.country if country is None else country
        resolved_domain = self.domain if domain is None else domain
        resolved_days = self.days if days is None else days
        resolved_score_gte = self.score_gte if score_gte is None else score_gte
        resolved_score_lte = self.score_lte if score_lte is None else score_lte
        if resolved_language is not None:
            kwargs["language"] = resolved_language
        if resolved_country is not None:
            kwargs["country"] = resolved_country
        if resolved_domain is not None:
            kwargs["domain"] = resolved_domain
        if resolved_days is not None:
            kwargs["days"] = resolved_days
        if resolved_score_gte is not None:
            kwargs["score_gte"] = resolved_score_gte
        if resolved_score_lte is not None:
            kwargs["score_lte"] = resolved_score_lte
        return kwargs

    def _search_sync(self, query: str, **overrides: Any) -> NewsSearchResponse:  # noqa: ANN401
        url, token = self._endpoint_and_token()
        owns_client = self._http_client is None
        http_client = self._http_client or httpx.Client(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS, connect=DEFAULT_CONNECT_TIMEOUT_SECONDS),
            follow_redirects=False,
        )
        try:
            searcher = WebzNewsSearch(api_token=token, api_url=url, client=http_client)
            try:
                return searcher.search(query, **self._search_kwargs(**overrides))
            finally:
                searcher.close()
        finally:
            if owns_client:
                http_client.close()

    async def _search_async(self, query: str, **overrides: Any) -> NewsSearchResponse:  # noqa: ANN401
        url, token = self._endpoint_and_token()
        owns_client = self._async_http_client is None
        http_client = self._async_http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS, connect=DEFAULT_CONNECT_TIMEOUT_SECONDS),
            follow_redirects=False,
        )
        try:
            searcher = WebzNewsSearch(api_token=token, api_url=url, async_client=http_client)
            try:
                return await searcher.asearch(query, **self._search_kwargs(**overrides))
            finally:
                await searcher.aclose()
        finally:
            if owns_client:
                await http_client.aclose()


def _documents_from_response(response: NewsSearchResponse) -> dict[str, Any]:
    documents: list[Document] = []
    links: list[str] = []
    for result in response.results:
        meta: dict[str, Any] = {"title": result.title, "url": result.url}
        if result.article.published_at:
            meta["published_at"] = result.article.published_at
        if result.domain:
            meta["domain"] = result.domain
        for key in _META_KEYS:
            value = result.metadata.get(key)
            if value:
                meta[key] = value
        documents.append(
            Document(
                content=result.text or result.article.summary,
                meta=meta,
                score=result.score,
            )
        )
        url = (result.url or "").strip()
        if url:
            links.append(url)
    return {"documents": documents, "links": links}
