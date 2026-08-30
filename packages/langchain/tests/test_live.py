from __future__ import annotations

import os

import pytest

from langchain_webz import WebzNewsSearch, get_webz_tools
from langchain_webz.consts import PREFERRED_TOOL_NAME

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_tools_come_from_hosted_mcp() -> None:
    tools = get_webz_tools()
    names = [tool.name for tool in tools]
    assert PREFERRED_TOOL_NAME in names
    news_tool = next(tool for tool in tools if tool.name == PREFERRED_TOOL_NAME)
    assert "query" in news_tool.args


def test_live_news_search_invoke() -> None:
    tool = WebzNewsSearch()
    result = tool.invoke({"query": "AI regulation Europe", "k": 1})
    assert isinstance(result, str)
    assert "Query:" in result
    assert result.strip()
