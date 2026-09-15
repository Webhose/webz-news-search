from __future__ import annotations

import os

import pytest

from tools._mcp import call_news_search, validate_token

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_initialize_does_not_raise() -> None:
    validate_token(os.environ["WEBZ_API_TOKEN"])


def test_live_news_search_returns_articles() -> None:
    text = call_news_search(
        os.environ["WEBZ_API_TOKEN"],
        {"query": "AI regulation Europe", "k": 1},
    )
    assert "Query:" in text
    assert text.strip()
