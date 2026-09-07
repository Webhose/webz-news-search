from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_webzio.consts import (
    DEFAULT_MCP_URL,
    MCP_TRANSPORT,
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
)
from crewai_webzio.tool import (
    WebzConfigError,
    WebzioNewsSearchTool,
    build_server_params,
    pick_news_search_tool,
    resolve_api_token,
    resolve_mcp_url,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TOOL_SOURCE = (PACKAGE_ROOT / "crewai_webzio" / "tool.py").read_text(encoding="utf-8")
CONSTS_SOURCE = (PACKAGE_ROOT / "crewai_webzio" / "consts.py").read_text(encoding="utf-8")

FILTER_NAMES_OWNED_BY_MCP = (
    "allow_all_dates",
    "exclude_domain",
    "domain_rank_gte",
    "domain_rank_lte",
    "trust_category",
    "political_bias",
    "min_similarity",
    "allow_multiple_chunks_per_article",
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


def test_resolve_api_token_prefers_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_ENV_NAME, "from-env")
    assert resolve_api_token(" from-arg ") == "from-arg"


def test_resolve_mcp_url_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBZ_MCP_URL", raising=False)
    assert resolve_mcp_url() == DEFAULT_MCP_URL
    assert resolve_mcp_url("https://localhost:8765/mcp/") == "https://localhost:8765/mcp"


def test_build_server_params_uses_bearer_and_streamable_http() -> None:
    params = build_server_params("secret-token", mcp_url="https://example.test/mcp")
    assert params["url"] == "https://example.test/mcp"
    assert params["transport"] == MCP_TRANSPORT
    assert params["headers"]["Authorization"] == "Bearer secret-token"


def test_pick_news_search_tool_prefers_named_tool() -> None:
    preferred = SimpleNamespace(name=PREFERRED_TOOL_NAME)
    other = SimpleNamespace(name="other_tool")
    assert pick_news_search_tool([other, preferred]) is preferred  # type: ignore[arg-type]


def test_pick_news_search_tool_falls_back_to_single_tool() -> None:
    only = SimpleNamespace(name="whatever_the_server_exposes")
    assert pick_news_search_tool([only]) is only  # type: ignore[arg-type]


def test_pick_news_search_tool_errors_when_preferred_missing_among_many() -> None:
    with pytest.raises(WebzConfigError, match="did not expose"):
        pick_news_search_tool(
            [SimpleNamespace(name="alpha"), SimpleNamespace(name="beta")]  # type: ignore[list-item]
        )


@patch("crewai_webzio.tool.MCPServerAdapter", FakeMcpAdapter)
def test_webzio_news_search_tool_loads_live_schema_and_delegates_run() -> None:
    tool = WebzioNewsSearchTool(api_token="tok", mcp_url="https://example.test/mcp")
    try:
        assert tool.name == PREFERRED_TOOL_NAME
        assert "query" in tool.arg_names
        assert "extra_filter" in tool.arg_names
        assert tool.description == "Live MCP news search tool"
        assert tool._run(query="EU AI", k=3) == "result:EU AI"
    finally:
        tool.stop()


@patch("crewai_webzio.tool.MCPServerAdapter", FakeMcpAdapter)
def test_webzio_news_search_tool_context_manager_stops_adapter() -> None:
    with WebzioNewsSearchTool(api_token="tok") as tool:
        assert tool._adapter is not None
        adapter = tool._adapter
    assert adapter._stopped is True
    assert tool._adapter is None


def test_wrapper_source_does_not_hardcode_mcp_filters() -> None:
    combined = TOOL_SOURCE + CONSTS_SOURCE
    for name in FILTER_NAMES_OWNED_BY_MCP:
        assert name not in combined, f"wrapper must not hardcode MCP filter {name}"


def test_public_exports() -> None:
    import crewai_webzio

    for name in (
        "WebzioNewsSearchTool",
        "WebzConfigError",
        "DEFAULT_MCP_URL",
        "TOKEN_ENV_NAME",
        "build_server_params",
        "resolve_api_token",
        "resolve_mcp_url",
    ):
        assert hasattr(crewai_webzio, name)
