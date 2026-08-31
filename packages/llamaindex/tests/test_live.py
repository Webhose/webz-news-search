from __future__ import annotations

import os

import pytest

from llama_index.tools.webz import WebzNewsSearch, flatten_tool_result, get_webz_tools
from llama_index.tools.webz.client import tool_arg_names
from llama_index.tools.webz.consts import PREFERRED_TOOL_NAME

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


def test_live_tools_come_from_hosted_mcp() -> None:
    tools = get_webz_tools()
    names = [tool.metadata.name for tool in tools]
    assert PREFERRED_TOOL_NAME in names
    news_tool = next(tool for tool in tools if tool.metadata.name == PREFERRED_TOOL_NAME)
    assert "query" in tool_arg_names(news_tool)


def test_live_news_search_call() -> None:
    tool = WebzNewsSearch()
    result = flatten_tool_result(tool.call(query="AI regulation Europe", k=1))
    assert isinstance(result, str)
    assert "Query:" in result
    assert result.strip()
