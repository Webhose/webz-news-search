from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from webzio_news_search import (
    DEFAULT_API_URL,
    TOKEN_ENV_NAME,
    TOOL_NAME,
    NewsSearchResponse,
    WebzAPIError,
    WebzConfigError,
    WebzNewsSearch,
    build_request_body,
    news_search,
    openai_tool_definition,
    tool_definition,
)
from webzio_news_search.client import (
    normalize_filters,
    published_from_for_days,
    resolve_api_token,
    resolve_api_url,
)

SAMPLE_RESULT = {
    "score": 7.1,
    "article": {
        "article_id": "abc123",
        "url": "https://www.example.com/story",
        "title": "Example headline",
        "published_at": "2026-08-27T07:07:00.000+03:00",
        "summary": "Short summary.",
        "main_image": "https://media.example.com/image.png",
    },
    "chunk": {"chunk_id": "abc123_6", "chunk_index": 6, "text": "Relevant chunk text."},
    "metadata": {
        "language": "english",
        "country": "US",
        "category": ["Economy, Business and Finance"],
        "sentiment": "positive",
        "domain": "example.com",
        "site_type": "news",
        "ticker": ["NVDA"],
        "organization": ["nvidia"],
        "political_bias": "center",
        "domain_rank": 193,
    },
}

SAMPLE_PAYLOAD = {
    "query": "nvidia earnings",
    "total_results": 1,
    "results": [SAMPLE_RESULT],
    "requests_left": 990,
    "credits_used": 10,
}


def make_client(handler, **kwargs) -> WebzNewsSearch:
    transport = httpx.MockTransport(handler)
    return WebzNewsSearch(
        api_token="tok",
        client=httpx.Client(transport=transport),
        async_client=httpx.AsyncClient(transport=transport),
        **kwargs,
    )


def json_handler(payload: dict, status_code: int = 200, capture: dict | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["request"] = request
            capture["body"] = json.loads(request.content or b"{}")
        return httpx.Response(status_code, json=payload)

    return handler


# config


def test_resolve_api_token_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    with pytest.raises(WebzConfigError, match="missing Webz API token"):
        resolve_api_token()


def test_resolve_api_token_prefers_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_ENV_NAME, "from-env")
    assert resolve_api_token(" from-arg ") == "from-arg"
    assert resolve_api_token() == "from-env"


def test_resolve_api_url_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBZ_NEWS_SEARCH_URL", raising=False)
    assert resolve_api_url() == DEFAULT_API_URL
    monkeypatch.setenv("WEBZ_NEWS_SEARCH_URL", "https://localhost:9000/api/news/context")
    assert resolve_api_url() == "https://localhost:9000/api/news/context"
    assert resolve_api_url("https://override.test/ctx") == "https://override.test/ctx"


# request body


def test_build_request_body_minimal() -> None:
    assert build_request_body("  ai regulation ") == {"query": "ai regulation"}


def test_build_request_body_requires_query() -> None:
    with pytest.raises(WebzConfigError, match="query is required"):
        build_request_body("   ")


def test_build_request_body_rejects_long_query() -> None:
    with pytest.raises(WebzConfigError, match="characters"):
        build_request_body("x" * 751)
    with pytest.raises(WebzConfigError, match="words"):
        build_request_body(" ".join(["word"] * 101))


def test_build_request_body_top_level_and_filters() -> None:
    body = build_request_body(
        "nvidia earnings",
        k=5,
        score_gte=3,
        score_lte=9,
        allow_multiple_chunks_per_article=True,
        language="english",
        country=["US", "GB"],
        ticker=("NVDA",),
        published_from="2026-09-01",
        domain_rank_lte=10000,
    )
    assert body == {
        "query": "nvidia earnings",
        "k": 5,
        "score_gte": 3,
        "score_lte": 9,
        "allow_multiple_chunks_per_article": True,
        "filters": {
            "language": ["english"],
            "country": ["US", "GB"],
            "ticker": ["NVDA"],
            "published_from": "2026-09-01",
            "domain_rank_lte": 10000,
        },
    }


def test_build_request_body_merges_filters_dict_and_kwargs() -> None:
    body = build_request_body(
        "q",
        filters={"language": ["english"], "k": 3, "sentiment": "negative"},
        organization=["nvidia"],
    )
    assert body["k"] == 3
    assert body["filters"] == {
        "language": ["english"],
        "sentiment": ["negative"],
        "organization": ["nvidia"],
    }


def test_build_request_body_passes_unknown_filters_through() -> None:
    body = build_request_body("q", filters={"brand_new_filter": "value"})
    assert body["filters"] == {"brand_new_filter": "value"}


def test_build_request_body_drops_empty_values() -> None:
    body = build_request_body("q", language="", ticker=[], country=None, filters={"topic": ["  "]})
    assert "filters" not in body


def test_build_request_body_days_sets_published_from() -> None:
    body = build_request_body("q", days=7)
    assert body["filters"]["published_from"] == published_from_for_days(7)
    with pytest.raises(WebzConfigError, match="either days or published_from"):
        build_request_body("q", days=7, published_from="2026-09-01")


def test_published_from_for_days_uses_utc_date() -> None:
    now = datetime(2026, 9, 30, 1, 0, tzinfo=timezone.utc)
    assert published_from_for_days(7, now=now) == "2026-09-23"
    assert published_from_for_days(0, now=now) == "2026-09-30"
    with pytest.raises(WebzConfigError):
        published_from_for_days(-1)


def test_build_request_body_validates_k_and_scores() -> None:
    with pytest.raises(WebzConfigError, match="k must be"):
        build_request_body("q", k=0)
    with pytest.raises(WebzConfigError, match="score_gte cannot"):
        build_request_body("q", score_gte=8, score_lte=2)


def test_normalize_filters_rejects_domain_overlap() -> None:
    with pytest.raises(WebzConfigError, match="both domain and exclude_domain"):
        normalize_filters({"domain": ["cnn.com"], "exclude_domain": ["cnn.com"]})


# http


def test_search_posts_bearer_json_and_parses_response() -> None:
    capture: dict = {}
    client = make_client(json_handler(SAMPLE_PAYLOAD, capture=capture))
    response = client.search("nvidia earnings", k=1, ticker=["NVDA"])

    request = capture["request"]
    assert request.method == "POST"
    assert str(request.url) == DEFAULT_API_URL
    assert request.headers["Authorization"] == "Bearer tok"
    assert request.headers["Content-Type"] == "application/json"
    assert capture["body"] == {"query": "nvidia earnings", "k": 1, "filters": {"ticker": ["NVDA"]}}

    assert isinstance(response, NewsSearchResponse)
    assert response.query == "nvidia earnings"
    assert response.total_results == 1
    assert response.requests_left == 990
    assert response.credits_used == 10
    assert len(response) == 1
    result = response.results[0]
    assert result.score == 7.1
    assert result.title == "Example headline"
    assert result.url == "https://www.example.com/story"
    assert result.text == "Relevant chunk text."
    assert result.domain == "example.com"
    assert result.article.article_id == "abc123"
    assert result.chunk.chunk_index == 6
    assert result.metadata["ticker"] == ["NVDA"]
    assert result.raw == SAMPLE_RESULT
    assert response.raw == SAMPLE_PAYLOAD


def test_search_uses_custom_api_url() -> None:
    capture: dict = {}
    client = make_client(
        json_handler(SAMPLE_PAYLOAD, capture=capture),
        api_url="https://staging.test/api/news/context",
    )
    client.search("q")
    assert str(capture["request"].url) == "https://staging.test/api/news/context"


async def test_asearch_parses_response() -> None:
    client = make_client(json_handler(SAMPLE_PAYLOAD))
    response = await client.asearch("nvidia earnings")
    assert response.results[0].title == "Example headline"
    await client.aclose()


@pytest.mark.parametrize(
    "status, hint",
    [
        (400, "too long"),
        (401, "API token"),
        (402, "insufficient credits"),
        (403, "inactive"),
        (422, "invalid"),
        (429, "rate limit"),
        (503, "temporary server error"),
    ],
)
def test_search_raises_api_error_with_hint(status: int, hint: str) -> None:
    client = make_client(json_handler({"detail": "server said no"}, status_code=status))
    with pytest.raises(WebzAPIError) as info:
        client.search("q")
    assert info.value.status_code == status
    assert info.value.detail == "server said no"
    assert hint in str(info.value)
    assert "server said no" in str(info.value)


def test_search_wraps_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = make_client(handler)
    with pytest.raises(WebzAPIError, match="could not reach"):
        client.search("q")


def test_search_rejects_non_json_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>nope</html>")

    client = make_client(handler)
    with pytest.raises(WebzAPIError, match="not valid JSON"):
        client.search("q")


def test_news_search_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(json_handler(SAMPLE_PAYLOAD))
    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: real_client(transport=transport, **kw))
    response = news_search("q", api_token="tok", k=1)
    assert response.total_results == 1


def test_context_manager_closes_owned_client() -> None:
    with WebzNewsSearch(api_token="tok") as client:
        assert client._client is None
        client._sync_client()
        assert client._client is not None
    assert client._client is None


# formatting


def test_to_text_and_to_dicts() -> None:
    response = NewsSearchResponse.from_dict(SAMPLE_PAYLOAD)
    text = response.to_text()
    assert text.startswith("Query: nvidia earnings\nResults: 1")
    assert "1. Example headline" in text
    assert "URL: https://www.example.com/story" in text
    assert "Score: 7.1" in text
    assert "Source: example.com | US | english" in text
    assert "Ticker: NVDA" in text
    assert "Excerpt: Relevant chunk text." in text

    rows = response.to_dicts()
    assert rows[0]["title"] == "Example headline"
    assert rows[0]["excerpt"] == "Relevant chunk text."
    assert rows[0]["metadata_domain"] == "example.com"


def test_to_text_empty() -> None:
    response = NewsSearchResponse.from_dict({"query": "q", "total_results": 0, "results": []})
    assert response.to_text() == "Query: q\nResults: 0\nNo matching articles."


# tool calling


def test_tool_definition_shape() -> None:
    definition = tool_definition()
    assert definition["name"] == TOOL_NAME
    params = definition["parameters"]
    assert params["required"] == ["query"]
    for name in ("query", "k", "days", "language", "ticker", "published_from", "domain_rank_lte"):
        assert name in params["properties"]
    wrapped = openai_tool_definition()
    assert wrapped["type"] == "function"
    assert wrapped["function"] is not definition
    assert wrapped["function"]["name"] == TOOL_NAME
    assert WebzNewsSearch.tool_definition()["name"] == TOOL_NAME


def test_run_tool_accepts_json_string_and_dict() -> None:
    capture: dict = {}
    client = make_client(json_handler(SAMPLE_PAYLOAD, capture=capture))
    text = client.run_tool('{"query": "nvidia earnings", "k": 2, "ticker": ["NVDA"], "days": 3}')
    assert "Example headline" in text
    body = capture["body"]
    assert body["k"] == 2
    assert body["filters"]["ticker"] == ["NVDA"]
    assert body["filters"]["published_from"] == published_from_for_days(3)

    text = client.run_tool({"query": "nvidia earnings"})
    assert "Example headline" in text


def test_run_tool_rejects_bad_arguments() -> None:
    client = make_client(json_handler(SAMPLE_PAYLOAD))
    with pytest.raises(WebzConfigError, match="valid JSON"):
        client.run_tool("{not json")
    with pytest.raises(WebzConfigError, match="JSON object"):
        client.run_tool("[1, 2]")
    with pytest.raises(WebzConfigError, match="query is required"):
        client.run_tool({"k": 3})


async def test_arun_tool() -> None:
    client = make_client(json_handler(SAMPLE_PAYLOAD))
    text = await client.arun_tool({"query": "nvidia earnings"})
    assert "Example headline" in text
    await client.aclose()


def test_public_exports() -> None:
    import webzio_news_search

    for name in (
        "WebzNewsSearch",
        "news_search",
        "anews_search",
        "tool_definition",
        "openai_tool_definition",
        "NewsSearchResponse",
        "NewsResult",
        "WebzAPIError",
        "WebzConfigError",
        "DEFAULT_API_URL",
        "TOKEN_ENV_NAME",
        "TOOL_NAME",
    ):
        assert hasattr(webzio_news_search, name)
