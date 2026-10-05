"""Offline tests for the GPT Researcher Webz retriever. No token required."""

from __future__ import annotations

import json
from importlib.metadata import entry_points

import httpx
import pytest

from gpt_researcher_webz import ENTRY_POINT_GROUP, ENTRY_POINT_NAME, WebzSearch
from gpt_researcher_webz.retriever import HEADER_TOKEN_KEY, WebzRetrieverError

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
    "metadata": {"domain": "example.com", "language": "english"},
}

SAMPLE_PAYLOAD = {
    "query": "ai regulation",
    "total_results": 1,
    "results": [SAMPLE_RESULT],
}


def _no_days(value: object) -> None:
    if isinstance(value, dict):
        assert "days" not in value
        for child in value.values():
            _no_days(child)
    elif isinstance(value, list):
        for child in value:
            _no_days(child)


def _install_transport(payload: dict, status_code: int = 200, capture: dict | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["url"] = str(request.url)
            capture["body"] = json.loads(request.content or b"{}")
            capture["authorization"] = request.headers.get("authorization")
        return httpx.Response(status_code, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_entry_point_resolves_to_webz_search() -> None:
    matches = [
        ep
        for ep in entry_points(group=ENTRY_POINT_GROUP)
        if ep.name == ENTRY_POINT_NAME
    ]
    assert len(matches) == 1
    assert matches[0].load() is WebzSearch
    assert ENTRY_POINT_GROUP == "gpt_researcher.retrievers"
    assert ENTRY_POINT_NAME == "webz"


def test_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBZ_API_TOKEN", raising=False)
    with pytest.raises(WebzRetrieverError, match="WEBZ_API_TOKEN"):
        WebzSearch("ai regulation")


def test_search_maps_results_and_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    monkeypatch.delenv("WEBZ_NEWS_SEARCH_URL", raising=False)
    capture: dict = {}
    retriever = WebzSearch(
        "  ai regulation  ",
        query_domains=["cnn.com", " bbc.com ", ""],
        client=_install_transport(SAMPLE_PAYLOAD, capture=capture),
    )
    results = retriever.search(max_results=3)

    assert capture["url"] == "https://api.webz.io/api/news/context"
    assert capture["authorization"] == "Bearer test-token"
    assert capture["body"]["query"] == "ai regulation"
    assert capture["body"]["k"] == 3
    assert capture["body"]["filters"]["domain"] == ["cnn.com", "bbc.com"]
    _no_days(capture["body"])
    assert results == [
        {
            "href": "https://www.example.com/story",
            "body": (
                "Example headline\n"
                "Source: example.com\n"
                "Published: 2026-08-27T07:07:00.000+03:00\n"
                "\n"
                "Relevant chunk text."
            ),
        }
    ]
    assert retriever.requires_scraping is True


def test_default_max_results_is_sent_as_k(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    capture: dict = {}
    retriever = WebzSearch(
        "ai regulation",
        client=_install_transport(SAMPLE_PAYLOAD, capture=capture),
    )
    retriever.search()
    assert capture["body"]["k"] == 7
    assert "filters" not in capture["body"]


def test_header_token_overrides_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "from-env")
    capture: dict = {}
    retriever = WebzSearch(
        "ai regulation",
        headers={HEADER_TOKEN_KEY: " from-header "},
        client=_install_transport(SAMPLE_PAYLOAD, capture=capture),
    )
    retriever.search(max_results=1)
    assert capture["authorization"] == "Bearer from-header"


def test_header_token_works_without_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBZ_API_TOKEN", raising=False)
    capture: dict = {}
    retriever = WebzSearch(
        "ai regulation",
        headers={HEADER_TOKEN_KEY: "header-only"},
        client=_install_transport(SAMPLE_PAYLOAD, capture=capture),
    )
    assert retriever.search(max_results=1)[0]["href"] == "https://www.example.com/story"
    assert capture["authorization"] == "Bearer header-only"


def test_cleartext_endpoint_raises_before_the_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    monkeypatch.setenv("WEBZ_NEWS_SEARCH_URL", "http://api.webz.io/api/news/context")
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json=SAMPLE_PAYLOAD)

    with pytest.raises(WebzRetrieverError, match="https"):
        WebzSearch("ai regulation", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert called["count"] == 0


def test_http_error_returns_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    retriever = WebzSearch(
        "ai regulation",
        client=_install_transport({"detail": "nope"}, status_code=500),
    )
    assert retriever.search(max_results=2) == []


def test_result_without_url_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    payload = {
        "query": "ai regulation",
        "total_results": 2,
        "results": [
            {"article": {"url": "", "title": "no url"}, "chunk": {"text": "skip"}},
            SAMPLE_RESULT,
        ],
    }
    retriever = WebzSearch("ai regulation", client=_install_transport(payload))
    results = retriever.search(max_results=5)
    assert len(results) == 1
    assert results[0]["href"] == "https://www.example.com/story"


def test_constructor_accepts_gpt_researcher_keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBZ_API_TOKEN", "test-token")
    retriever = WebzSearch(
        "ai regulation",
        query_domains=["reuters.com"],
        headers={"retriever": "webz"},
        websocket=None,
        researcher=None,
        client=_install_transport(SAMPLE_PAYLOAD),
    )
    assert retriever.query_domains == ["reuters.com"]
    assert retriever.search(max_results=1)
