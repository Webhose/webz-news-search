"""One live News Search call. Skipped when WEBZ_API_TOKEN is unset."""

from __future__ import annotations

import os

import pytest

from movieclaw_webz import WebzNewsSearchProvider

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_search_returns_a_hit() -> None:
    provider = WebzNewsSearchProvider()
    hits = provider.search_sync("AI regulation Europe", max_results=1)
    assert len(hits) <= 1
    for hit in hits:
        assert hit.url.startswith("https://")
        assert hit.title
        assert hit.date is None or len(hit.date) == 10
