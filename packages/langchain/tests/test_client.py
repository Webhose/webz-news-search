from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.tools import BaseTool, StructuredTool, tool

from langchain_webz.client import (
    WebzConfigError,
    WebzNewsSearch,
    aget_webz_tools,
    build_mcp_connection,
    enable_sync_invoke,
    get_webz_tools,
    pick_news_search_tool,
    resolve_api_token,
    resolve_mcp_url,
)
from langchain_webz.consts import (
    DEFAULT_MCP_URL,
    MCP_SERVER_NAME,
    MCP_TRANSPORT,
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = (PACKAGE_ROOT / "langchain_webz" / "client.py").read_text(encoding="utf-8")
CONSTS_SOURCE = (PACKAGE_ROOT / "langchain_webz" / "consts.py").read_text(encoding="utf-8")

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


@tool(PREFERRED_TOOL_NAME)
def fake_news_search(query: str, extra_filter: str = "x") -> str:
    """fake news search tool used in unit tests."""
    return f"{query}:{extra_filter}"


@tool
def fake_other_tool(value: str) -> str:
    """second fake tool to prove all MCP tools are forwarded."""
    return value


class FakeMcpClient:
    def __init__(self, connections: dict) -> None:
        self.connections = connections

    async def get_tools(self) -> list[BaseTool]:
        return [fake_news_search, fake_other_tool]


class EmptyMcpClient(FakeMcpClient):
    async def get_tools(self) -> list[BaseTool]:
        return []


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


def test_build_mcp_connection_uses_bearer_header() -> None:
    connection = build_mcp_connection("secret-token", DEFAULT_MCP_URL)
    server = connection[MCP_SERVER_NAME]
    assert server["transport"] == MCP_TRANSPORT
    assert server["url"] == DEFAULT_MCP_URL
    assert server["headers"]["Authorization"] == "Bearer secret-token"


def test_pick_prefers_named_news_tool() -> None:
    preferred = SimpleNamespace(name=PREFERRED_TOOL_NAME)
    other = SimpleNamespace(name="other_tool")
    assert pick_news_search_tool([other, preferred]) is preferred


def test_pick_falls_back_to_single_tool() -> None:
    only = SimpleNamespace(name="whatever_the_server_exposes")
    assert pick_news_search_tool([only]) is only


def test_pick_errors_when_preferred_missing_among_many() -> None:
    with pytest.raises(WebzConfigError, match="did not expose"):
        pick_news_search_tool(
            [SimpleNamespace(name="alpha"), SimpleNamespace(name="beta")]
        )


@pytest.mark.asyncio
async def test_aget_webz_tools_loads_whatever_mcp_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_client_ctor(connections: dict) -> FakeMcpClient:
        captured["connections"] = connections
        return FakeMcpClient(connections)

    monkeypatch.setattr("langchain_webz.client.MultiServerMCPClient", fake_client_ctor)
    tools = await aget_webz_tools(api_token="tok", mcp_url="https://example.test/mcp")
    assert [item.name for item in tools] == [PREFERRED_TOOL_NAME, "fake_other_tool"]
    assert "extra_filter" in inspect.signature(fake_news_search.func).parameters
    server = captured["connections"][MCP_SERVER_NAME]
    assert server["url"] == "https://example.test/mcp"
    assert server["headers"]["Authorization"] == "Bearer tok"


@pytest.mark.asyncio
async def test_aget_webz_tools_rejects_empty_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("langchain_webz.client.MultiServerMCPClient", EmptyMcpClient)
    with pytest.raises(WebzConfigError, match="returned no tools"):
        await aget_webz_tools(api_token="tok")


def test_sync_helpers_use_loaded_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("langchain_webz.client.MultiServerMCPClient", FakeMcpClient)
    tools = get_webz_tools(api_token="tok")
    news_tool = WebzNewsSearch(api_token="tok")
    assert [item.name for item in tools] == [PREFERRED_TOOL_NAME, "fake_other_tool"]
    assert news_tool.name == PREFERRED_TOOL_NAME
    assert "extra_filter" in news_tool.args
    assert "query" in news_tool.args


def test_wrapper_source_does_not_hardcode_mcp_filters() -> None:
    combined = CLIENT_SOURCE + CONSTS_SOURCE
    for name in FILTER_NAMES_OWNED_BY_MCP:
        assert name not in combined, f"wrapper must not hardcode MCP filter {name}"


def test_public_exports() -> None:
    import langchain_webz

    for name in (
        "WebzNewsSearch",
        "get_webz_tools",
        "aget_webz_tools",
        "awebz_news_search",
        "WebzConfigError",
        "DEFAULT_MCP_URL",
        "TOKEN_ENV_NAME",
    ):
        assert hasattr(langchain_webz, name)


def test_enable_sync_invoke_allows_tool_invoke() -> None:
    async def call_tool(*, query: str) -> str:
        return f"got {query}"

    async_only = StructuredTool(
        name=PREFERRED_TOOL_NAME,
        description="async-only mcp-style tool",
        args_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        coroutine=call_tool,
    )
    with pytest.raises(NotImplementedError, match="sync invocation"):
        async_only.invoke({"query": "hi"})

    wrapped = enable_sync_invoke(async_only)
    assert wrapped.invoke({"query": "hi"}) == "got hi"


def test_enable_sync_invoke_flattens_content_and_artifact() -> None:
    async def call_tool(*, query: str) -> list[dict[str, str]]:
        return [{"type": "text", "text": f"Query: {query}", "id": "lc_test"}]

    mcp_style = StructuredTool(
        name=PREFERRED_TOOL_NAME,
        description="mcp content_and_artifact tool",
        args_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        coroutine=call_tool,
        response_format="content_and_artifact",
    )
    wrapped = enable_sync_invoke(mcp_style)
    assert wrapped.response_format == "content"
    assert wrapped.invoke({"query": "AI"}) == "Query: AI"


def test_flatten_tool_result_unwraps_content_blocks() -> None:
    from langchain_webz.client import flatten_tool_result

    blocks = [
        {
            "type": "text",
            "text": "Query: AI regulation Europe\nTitle: Example",
            "id": "lc_test",
        }
    ]
    assert flatten_tool_result(blocks) == "Query: AI regulation Europe\nTitle: Example"
    assert flatten_tool_result((blocks, None)) == "Query: AI regulation Europe\nTitle: Example"
    assert flatten_tool_result("already text") == "already text"
