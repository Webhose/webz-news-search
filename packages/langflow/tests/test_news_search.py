"""Offline tests for the Webz.io News Search Langflow extension."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from components.lfx_webz.webz_news_search import (
    API_URL,
    TOKEN_ENV_NAME,
    WebzConfigError,
    WebzNewsSearchComponent,
    article_row,
    build_request_body,
    published_from_for_days,
    require_https,
    resolve_api_token,
    search,
)

SAMPLE_RESULT = {
    "score": 7.1,
    "article": {
        "article_id": "abc123",
        "url": "https://www.example.com/story",
        "title": "Example headline",
        "published_at": "2026-08-27T07:07:00.000+03:00",
        "summary": "Short summary.",
    },
    "chunk": {"chunk_id": "abc123_6", "chunk_index": 6, "text": "Relevant chunk text."},
    "metadata": {
        "language": "english",
        "country": "US",
        "category": ["Economy, Business and Finance"],
        "sentiment": "positive",
        "domain": "example.com",
    },
}

SAMPLE_PAYLOAD = {"query": "nvidia earnings", "total_results": 1, "results": [SAMPLE_RESULT]}


def test_component_metadata() -> None:
    assert WebzNewsSearchComponent.display_name == "Webz.io News Search"
    assert WebzNewsSearchComponent.name == "WebzNewsSearch"
    assert WebzNewsSearchComponent.documentation.startswith("https://")
    query = next(item for item in WebzNewsSearchComponent.inputs if item.name == "query")
    assert query.tool_mode is True
    output_names = [item.name for item in WebzNewsSearchComponent.outputs]
    assert output_names == ["data", "dataframe", "tools"]


def test_require_https_rejects_cleartext_before_any_request() -> None:
    with pytest.raises(WebzConfigError, match="https"):
        require_https("http://api.webz.io/api/news/context")
    assert require_https(API_URL) == API_URL


def test_resolve_api_token_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    with pytest.raises(WebzConfigError, match="Webz API key is required"):
        resolve_api_token("")
    with pytest.raises(WebzConfigError, match="Webz API key is required"):
        resolve_api_token(None)


def test_resolve_api_token_prefers_input_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_ENV_NAME, "from-env")
    assert resolve_api_token(" from-input ") == "from-input"
    assert resolve_api_token("") == "from-env"


def test_days_becomes_published_from_and_is_not_sent() -> None:
    now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    body = build_request_body(
        "  eu ai regulation ",
        k=5,
        days=7,
        language="english",
        country="US, GB",
        domain="cnn.com",
        sentiment="negative",
        category="Politics",
        now=now,
    )
    assert "days" not in body
    assert body == {
        "query": "eu ai regulation",
        "k": 5,
        "filters": {
            "published_from": "2026-09-28",
            "language": ["english"],
            "country": ["US", "GB"],
            "domain": ["cnn.com"],
            "sentiment": ["negative"],
            "category": ["Politics"],
        },
    }
    assert body["filters"]["published_from"] == published_from_for_days(7, now=now)


def test_zero_days_omits_the_date_filter() -> None:
    body = build_request_body("q", days=0)
    assert "days" not in body
    assert "filters" not in body
    assert body["k"] == 10


def test_build_request_body_rejects_empty_query_and_bad_k() -> None:
    with pytest.raises(WebzConfigError, match="query is required"):
        build_request_body("   ")
    with pytest.raises(WebzConfigError, match="k must be"):
        build_request_body("q", k=0)


def test_article_row_maps_title_url_and_excerpt() -> None:
    row = article_row(SAMPLE_RESULT)
    assert row["title"] == "Example headline"
    assert row["url"] == "https://www.example.com/story"
    assert row["excerpt"] == "Relevant chunk text."
    assert row["published_at"] == "2026-08-27T07:07:00.000+03:00"
    assert row["score"] == 7.1
    assert row["domain"] == "example.com"
    assert row["category"] == "Economy, Business and Finance"


def _mock_client(capture: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        capture["url"] = str(request.url)
        capture["authorization"] = request.headers.get("authorization")
        capture["body"] = json.loads(request.content or b"{}")
        return httpx.Response(200, json=SAMPLE_PAYLOAD)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_posts_https_body_without_days(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    capture: dict = {}
    now = datetime(2026, 10, 5, tzinfo=timezone.utc)
    rows = search(
        "nvidia earnings",
        api_key="test-token",
        k=3,
        days=7,
        language="english",
        client=_mock_client(capture),
        now=now,
    )
    assert capture["url"] == API_URL
    assert capture["url"].startswith("https://")
    assert capture["authorization"] == "Bearer test-token"
    assert "days" not in capture["body"]
    assert capture["body"]["filters"]["published_from"] == "2026-09-28"
    assert capture["body"]["k"] == 3
    assert rows[0]["title"] == "Example headline"


def _component(**overrides: object) -> WebzNewsSearchComponent:
    component = WebzNewsSearchComponent()
    component.api_key = "test-token"
    component.query = "nvidia earnings"
    component.k = 3
    component.days = 7
    component.language = "english"
    component.country = ""
    component.domain = ""
    component.sentiment = ""
    component.category = ""
    for key, value in overrides.items():
        setattr(component, key, value)
    return component


def test_component_fetch_content_maps_data_and_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict = {}

    def fake_search(query: str, **kwargs: object) -> list[dict]:
        capture["query"] = query
        capture["days"] = kwargs["days"]
        return [article_row(SAMPLE_RESULT)]

    monkeypatch.setattr("components.lfx_webz.webz_news_search.search", fake_search)
    component = _component()
    data = component.fetch_content()
    frame = component.fetch_content_dataframe()
    assert capture["query"] == "nvidia earnings"
    assert capture["days"] == 7
    assert data[0].data["title"] == "Example headline"
    assert data[0].data["url"] == "https://www.example.com/story"
    assert data[0].data["excerpt"] == "Relevant chunk text."
    assert list(frame["title"]) == ["Example headline"]


def test_component_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    component = _component(api_key="")
    with pytest.raises(WebzConfigError, match="Webz API key is required"):
        component.fetch_content()


def test_tool_uses_component_filters_and_returns_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_search(query: str, **kwargs: object) -> list[dict]:
        assert query == "from the tool"
        assert kwargs["language"] == "english"
        return [article_row(SAMPLE_RESULT)]

    monkeypatch.setattr("components.lfx_webz.webz_news_search.search", fake_search)
    tools = _component().build_tools()
    assert [item.name for item in tools] == ["news_search"]
    text = tools[0].invoke({"query": "from the tool"})
    assert "Example headline" in text
    assert "https://www.example.com/story" in text
