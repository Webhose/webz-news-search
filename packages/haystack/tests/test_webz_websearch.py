# SPDX-FileCopyrightText: 2026-present Webz.io <support@webz.io>
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from haystack import Document
from haystack.core.serialization import component_from_dict, component_to_dict
from haystack.utils import Secret
from webzio_news_search.consts import DEFAULT_API_URL
from webzio_news_search.errors import WebzAPIError

from haystack_integrations.components.websearch.webz import WebzWebSearch
from haystack_integrations.components.websearch.webz.webz_websearch import _require_https

SAMPLE_RESULT = {
    "score": 7.1,
    "article": {
        "article_id": "abc123",
        "url": "https://www.example.com/story",
        "title": "Example headline",
        "published_at": "2026-08-27T07:07:00.000+03:00",
        "summary": "Short summary.",
    },
    "chunk": {
        "chunk_id": "abc123_6",
        "chunk_index": 6,
        "text": "Relevant chunk text.",
    },
    "metadata": {
        "domain": "example.com",
        "language": "english",
        "country": "US",
        "topic": ["regulation"],
        "organization": ["European Union"],
    },
}

SAMPLE_PAYLOAD = {
    "query": "ai regulation",
    "total_results": 1,
    "results": [SAMPLE_RESULT],
}


def _published_from(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def _no_days(value: object) -> None:
    if isinstance(value, dict):
        assert "days" not in value
        for child in value.values():
            _no_days(child)
    elif isinstance(value, list):
        for child in value:
            _no_days(child)


def _capture_client(
    payload: dict,
    status_code: int = 200,
    capture: dict | None = None,
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["url"] = str(request.url)
            capture["body"] = json.loads(request.content or b"{}")
            capture["authorization"] = request.headers.get("authorization")
        return httpx.Response(status_code, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


class TestWebzWebSearch:
    def test_init_default(self) -> None:
        component = WebzWebSearch()
        assert component.top_k == 10
        assert component.api_url is None
        assert component.days is None
        assert component.api_key == Secret.from_env_var("WEBZ_API_TOKEN")

    def test_constant_https_url_passes_the_guard(self) -> None:
        assert _require_https(DEFAULT_API_URL) == DEFAULT_API_URL
        assert DEFAULT_API_URL == "https://api.webz.io/api/news/context"

    def test_guard_rejects_a_non_https_url(self) -> None:
        with pytest.raises(ValueError, match="https"):
            _require_https("http://api.webz.io/api/news/context")
        with pytest.raises(ValueError, match="https"):
            _require_https("https://")

    def test_run_request_body_and_document_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        monkeypatch.delenv("WEBZ_NEWS_SEARCH_URL", raising=False)
        capture: dict = {}
        component = WebzWebSearch(
            top_k=5,
            language="english",
            country=["US", " DE "],
            domain=["reuters.com"],
            days=3,
            score_gte=4,
        )
        component._http_client = _capture_client(SAMPLE_PAYLOAD, capture=capture)
        try:
            result = component.run(query="  ai regulation  ")
        finally:
            component._http_client.close()

        body = capture["body"]
        assert capture["url"] == "https://api.webz.io/api/news/context"
        assert capture["authorization"] == "Bearer test-token"
        assert body["query"] == "ai regulation"
        assert body["k"] == 5
        assert body["score_gte"] == 4
        assert body["filters"]["language"] == ["english"]
        assert body["filters"]["country"] == ["US", "DE"]
        assert body["filters"]["domain"] == ["reuters.com"]
        assert body["filters"]["published_from"] == _published_from(3)
        assert "score_gte" not in body["filters"]
        _no_days(body)

        assert result["links"] == ["https://www.example.com/story"]
        document = result["documents"][0]
        assert isinstance(document, Document)
        assert document.content == "Relevant chunk text."
        assert document.score == 7.1
        assert document.meta["title"] == "Example headline"
        assert document.meta["url"] == "https://www.example.com/story"
        assert document.meta["published_at"] == "2026-08-27T07:07:00.000+03:00"
        assert document.meta["domain"] == "example.com"
        assert document.meta["topic"] == ["regulation"]
        assert document.meta["organization"] == ["European Union"]

    def test_run_overrides_top_k(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        capture: dict = {}
        component = WebzWebSearch(top_k=10)
        component._http_client = _capture_client(SAMPLE_PAYLOAD, capture=capture)
        try:
            component.run(query="ai regulation", top_k=2)
        finally:
            component._http_client.close()
        assert capture["body"]["k"] == 2
        assert "filters" not in capture["body"]
        _no_days(capture["body"])

    def test_token_override_without_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WEBZ_API_TOKEN", raising=False)
        capture: dict = {}
        component = WebzWebSearch(api_key=Secret.from_token("override-token"))
        component._http_client = _capture_client(SAMPLE_PAYLOAD, capture=capture)
        try:
            component.run(query="ai regulation", top_k=1)
        finally:
            component._http_client.close()
        assert capture["authorization"] == "Bearer override-token"

    def test_missing_token_raises_before_the_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WEBZ_API_TOKEN", raising=False)
        called = {"count": 0}

        def handler(_request: httpx.Request) -> httpx.Response:
            called["count"] += 1
            return httpx.Response(200, json=SAMPLE_PAYLOAD)

        component = WebzWebSearch()
        component._http_client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ValueError, match="WEBZ_API_TOKEN"):
                component.run(query="ai regulation")
        finally:
            component._http_client.close()
        assert called["count"] == 0

    def test_cleartext_url_is_rejected_before_the_token_is_sent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        resolved = {"count": 0}
        component = WebzWebSearch(api_url="http://api.webz.io/api/news/context")

        def _resolve(_self: Secret) -> str:
            resolved["count"] += 1
            return "test-token"

        monkeypatch.setattr(type(component.api_key), "resolve_value", _resolve)
        called = {"count": 0}

        def handler(_request: httpx.Request) -> httpx.Response:
            called["count"] += 1
            return httpx.Response(200, json=SAMPLE_PAYLOAD)

        component._http_client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ValueError, match="https"):
                component.run(query="ai regulation")
        finally:
            component._http_client.close()
        assert called["count"] == 0
        assert resolved["count"] == 0

    def test_cleartext_env_url_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        monkeypatch.setenv("WEBZ_NEWS_SEARCH_URL", "http://api.webz.io/api/news/context")
        called = {"count": 0}

        def handler(_request: httpx.Request) -> httpx.Response:
            called["count"] += 1
            return httpx.Response(200, json=SAMPLE_PAYLOAD)

        component = WebzWebSearch()
        component._http_client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ValueError, match="https"):
                component.run(query="ai regulation")
        finally:
            component._http_client.close()
        assert called["count"] == 0

    def test_api_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        component = WebzWebSearch()
        component._http_client = _capture_client({"detail": "unauthorized"}, status_code=401)
        try:
            with pytest.raises(WebzAPIError):
                component.run(query="ai regulation")
        finally:
            component._http_client.close()

    def test_to_dict(self) -> None:
        component = WebzWebSearch(
            top_k=5,
            days=7,
            language=["english"],
            country=["US"],
            domain=["reuters.com"],
        )
        data = component_to_dict(component, "news")
        assert data["type"] == ("haystack_integrations.components.websearch.webz.webz_websearch.WebzWebSearch")
        assert data["init_parameters"]["top_k"] == 5
        assert data["init_parameters"]["days"] == 7
        assert data["init_parameters"]["language"] == ["english"]
        assert data["init_parameters"]["country"] == ["US"]
        assert data["init_parameters"]["domain"] == ["reuters.com"]

    def test_from_dict(self) -> None:
        original = WebzWebSearch(top_k=4, days=3, language=["english"], country=["DE"], domain=["bbc.com"])
        data = component_to_dict(original, "news")
        restored = component_from_dict(WebzWebSearch, data, "news")
        assert restored.top_k == 4
        assert restored.days == 3
        assert restored.language == ["english"]
        assert restored.country == ["DE"]
        assert restored.domain == ["bbc.com"]
        assert restored.api_key == original.api_key

    @pytest.mark.asyncio
    async def test_run_async_maps_results(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
        monkeypatch.delenv("WEBZ_NEWS_SEARCH_URL", raising=False)
        capture: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            capture["url"] = str(request.url)
            capture["body"] = json.loads(request.content or b"{}")
            capture["authorization"] = request.headers.get("authorization")
            return httpx.Response(200, json=SAMPLE_PAYLOAD)

        component = WebzWebSearch(top_k=2, days=1)
        component._async_http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            result = await component.run_async(query="ai regulation")
        finally:
            await component._async_http_client.aclose()

        assert capture["url"] == "https://api.webz.io/api/news/context"
        assert capture["authorization"] == "Bearer test-token"
        assert capture["body"]["k"] == 2
        assert capture["body"]["filters"]["published_from"] == _published_from(1)
        _no_days(capture["body"])
        assert result["documents"][0].content == "Relevant chunk text."
        assert result["links"] == ["https://www.example.com/story"]
