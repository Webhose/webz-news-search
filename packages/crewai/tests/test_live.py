from __future__ import annotations

import os

import pytest

from crewai_webzio import WebzioNewsSearchTool
from crewai_webzio.consts import PREFERRED_TOOL_NAME

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_tool_discovers_news_search_schema() -> None:
    with WebzioNewsSearchTool() as tool:
        assert tool.name == PREFERRED_TOOL_NAME
        assert "query" in tool.arg_names
        assert len(tool.arg_names) > 1


def test_live_tool_runs_news_search() -> None:
    with WebzioNewsSearchTool() as tool:
        result = tool._run(query="EU AI regulation", k=1)
        assert isinstance(result, str)
        assert len(result) > 0
