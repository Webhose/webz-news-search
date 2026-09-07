from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_tools.tools.webzio_tools.webzio_news_search_tool import (
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
    WebzConfigError,
    WebzioNewsSearchTool,
    build_server_params,
    pick_news_search_tool,
    resolve_api_token,
    resolve_mcp_url,
)


class LiveArgsSchema(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(default=10, description="Number of results")
    extra_filter: str = Field(default="x", description="From MCP server")


class FakeLiveTool(BaseTool):
    name: str = PREFERRED_TOOL_NAME
    description: str = "Live MCP news search tool"
    args_schema: type[BaseModel] = LiveArgsSchema

    def _run(self, **kwargs: object) -> str:
        return f"result:{kwargs.get('query')}"


class FakeMcpAdapter:
    def __init__(
        self,
        serverparams: dict,
        *tool_names: str,
        connect_timeout: int = 30,
    ) -> None:
        self.serverparams = serverparams
        self.tool_names = tool_names
        self.connect_timeout = connect_timeout
        self._stopped = False
        self.tools = [FakeLiveTool()]

    def stop(self) -> None:
        self._stopped = True


def test_resolve_api_token_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    with pytest.raises(WebzConfigError, match="missing Webz API token"):
        resolve_api_token()


@patch(
    "crewai_tools.tools.webzio_tools.webzio_news_search_tool.MCPServerAdapter",
    FakeMcpAdapter,
)
def test_webzio_news_search_tool_loads_live_schema_and_delegates_run() -> None:
    tool = WebzioNewsSearchTool(api_token="tok", mcp_url="https://example.test/mcp")
    try:
        assert tool.name == PREFERRED_TOOL_NAME
        assert "query" in tool.arg_names
        assert "extra_filter" in tool.arg_names
        assert tool._run(query="EU AI", k=3) == "result:EU AI"
    finally:
        tool.stop()


@patch(
    "crewai_tools.tools.webzio_tools.webzio_news_search_tool.MCPServerAdapter",
    FakeMcpAdapter,
)
def test_webzio_news_search_tool_context_manager_stops_adapter() -> None:
    with WebzioNewsSearchTool(api_token="tok") as tool:
        assert tool._adapter is not None
        adapter = tool._adapter
    assert adapter._stopped is True


def test_pick_news_search_tool_prefers_named_tool() -> None:
    preferred = SimpleNamespace(name=PREFERRED_TOOL_NAME)
    other = SimpleNamespace(name="other_tool")
    assert pick_news_search_tool([other, preferred]) is preferred  # type: ignore[arg-type]


def test_build_server_params_uses_bearer_header() -> None:
    params = build_server_params("secret-token", mcp_url="https://example.test/mcp")
    assert params["headers"]["Authorization"] == "Bearer secret-token"
    assert params["transport"] == "streamable-http"


def test_deprecated_alias_excluded_from_tool_specs() -> None:
    from crewai_tools.generate_tool_specs import ToolSpecExtractor

    names = {tool["name"] for tool in ToolSpecExtractor().extract_all_tools()}
    assert "WebzioNewsSearchTool" in names
