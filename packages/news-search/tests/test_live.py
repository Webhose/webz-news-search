from __future__ import annotations

import os

import pytest

from webzio_news_search import WebzNewsSearch, news_search

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_search_returns_typed_results() -> None:
    with WebzNewsSearch() as client:
        response = client.search("AI regulation Europe", k=2, days=30, language=["english"])
    assert response.query
    assert response.credits_used is not None
    assert len(response.results) <= 2
    for result in response.results:
        assert result.url.startswith("http")
        assert result.title
        assert 0 <= result.score <= 10


def test_live_run_tool_text() -> None:
    text = news_search("central bank interest rate decision", k=1).to_text()
    assert text.startswith("Query: central bank interest rate decision")


async def test_live_asearch() -> None:
    async with WebzNewsSearch() as client:
        response = await client.asearch("renewable energy investments", k=1)
    assert len(response.results) <= 1
