from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from llama_index.core.tools import FunctionTool
from llama_index.core.tools.types import ToolOutput

from llama_index.tools.webz.client import (
    WebzConfigError,
    WebzNewsSearch,
    aget_webz_tools,
    build_mcp_headers,
    flatten_tool_result,
    get_webz_tools,
    pick_news_search_tool,
    resolve_api_token,
    resolve_mcp_url,
    tool_arg_names,
)
from llama_index.tools.webz.consts import (
    DEFAULT_MCP_URL,
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = (
    PACKAGE_ROOT / "llama_index" / "tools" / "webz" / "client.py"
).read_text(encoding="utf-8")
CONSTS_SOURCE = (
    PACKAGE_ROOT / "llama_index" / "tools" / "webz" / "consts.py"
).read_text(encoding="utf-8")

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


def fake_news_search(query: str, extra_filter: str = "x") -> str:
    """fake news search tool used in unit tests."""
    return f"{query}:{extra_filter}"


def fake_other_tool(value: str) -> str:
    """second fake tool to prove all MCP tools are forwarded."""
    return value


FAKE_NEWS_TOOL = FunctionTool.from_defaults(
    fn=fake_news_search,
    name=PREFERRED_TOOL_NAME,
)
FAKE_OTHER_TOOL = FunctionTool.from_defaults(
    fn=fake_other_tool,
    name="fake_other_tool",
)


class FakeMcpClient:
    def __init__(self, url: str, headers: dict | None = None, **kwargs: object) -> None:
        self.url = url
        self.headers = headers

    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> str:
        arguments = arguments or {}
        if tool_name == PREFERRED_TOOL_NAME:
            return f"{arguments.get('query')}:{arguments.get('extra_filter', 'x')}"
        return str(arguments.get("value", ""))


class FakeMcpSpec:
    def __init__(self, client: object) -> None:
        self.client = client

    async def to_tool_list_async(self) -> list[FunctionTool]:
        return [FAKE_NEWS_TOOL, FAKE_OTHER_TOOL]


class EmptyMcpSpec(FakeMcpSpec):
    async def to_tool_list_async(self) -> list[FunctionTool]:
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


def test_build_mcp_headers_uses_bearer() -> None:
    assert build_mcp_headers("secret-token") == {
        "Authorization": "Bearer secret-token"
    }


def test_pick_prefers_named_news_tool() -> None:
    preferred = SimpleNamespace(metadata=SimpleNamespace(name=PREFERRED_TOOL_NAME))
    other = SimpleNamespace(metadata=SimpleNamespace(name="other_tool"))
    assert pick_news_search_tool([other, preferred]) is preferred


def test_pick_falls_back_to_single_tool() -> None:
    only = SimpleNamespace(
        metadata=SimpleNamespace(name="whatever_the_server_exposes")
    )
    assert pick_news_search_tool([only]) is only


def test_pick_errors_when_preferred_missing_among_many() -> None:
    with pytest.raises(WebzConfigError, match="did not expose"):
        pick_news_search_tool(
            [
                SimpleNamespace(metadata=SimpleNamespace(name="alpha")),
                SimpleNamespace(metadata=SimpleNamespace(name="beta")),
            ]
        )


@pytest.mark.asyncio
async def test_aget_webz_tools_loads_whatever_mcp_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_client_ctor(url: str, headers: dict | None = None, **kwargs: object) -> FakeMcpClient:
        captured["url"] = url
        captured["headers"] = headers
        return FakeMcpClient(url, headers=headers)

    monkeypatch.setattr(
        "llama_index.tools.webz.client.BasicMCPClient", fake_client_ctor
    )
    monkeypatch.setattr("llama_index.tools.webz.client.McpToolSpec", FakeMcpSpec)
    tools = await aget_webz_tools(api_token="tok", mcp_url="https://example.test/mcp")
    assert [item.metadata.name for item in tools] == [
        PREFERRED_TOOL_NAME,
        "fake_other_tool",
    ]
    assert "extra_filter" in tool_arg_names(FAKE_NEWS_TOOL)
    assert captured["url"] == "https://example.test/mcp"
    assert captured["headers"]["Authorization"] == "Bearer tok"


@pytest.mark.asyncio
async def test_aget_webz_tools_rejects_empty_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("llama_index.tools.webz.client.BasicMCPClient", FakeMcpClient)
    monkeypatch.setattr("llama_index.tools.webz.client.McpToolSpec", EmptyMcpSpec)
    with pytest.raises(WebzConfigError, match="returned no tools"):
        await aget_webz_tools(api_token="tok")


def test_sync_helpers_use_loaded_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("llama_index.tools.webz.client.BasicMCPClient", FakeMcpClient)
    monkeypatch.setattr("llama_index.tools.webz.client.McpToolSpec", FakeMcpSpec)
    tools = get_webz_tools(api_token="tok")
    news_tool = WebzNewsSearch(api_token="tok")
    assert [item.metadata.name for item in tools] == [
        PREFERRED_TOOL_NAME,
        "fake_other_tool",
    ]
    assert news_tool.metadata.name == PREFERRED_TOOL_NAME
    assert "extra_filter" in tool_arg_names(news_tool)
    assert "query" in tool_arg_names(news_tool)
    output = news_tool.call(query="AI", extra_filter="live")
    assert flatten_tool_result(output) == "AI:live"


def test_wrapper_source_does_not_hardcode_mcp_filters() -> None:
    combined = CLIENT_SOURCE + CONSTS_SOURCE
    for name in FILTER_NAMES_OWNED_BY_MCP:
        assert name not in combined, f"wrapper must not hardcode MCP filter {name}"


def test_public_exports() -> None:
    import llama_index.tools.webz as pkg

    for name in (
        "WebzNewsSearch",
        "get_webz_tools",
        "aget_webz_tools",
        "awebz_news_search",
        "flatten_tool_result",
        "WebzConfigError",
        "DEFAULT_MCP_URL",
        "TOKEN_ENV_NAME",
    ):
        assert hasattr(pkg, name)


def test_flatten_mcp_call_result_reads_text_content() -> None:
    from llama_index.tools.webz.client import flatten_mcp_call_result

    payload = SimpleNamespace(
        content=[SimpleNamespace(text="Query: AI\nTitle: Example")]
    )
    assert flatten_mcp_call_result(payload) == "Query: AI\nTitle: Example"


def test_flatten_tool_result_unwraps_content_blocks() -> None:
    blocks = [
        {
            "type": "text",
            "text": "Query: AI regulation Europe\nTitle: Example",
            "id": "lc_test",
        }
    ]
    output = ToolOutput(
        blocks=[],
        tool_name=PREFERRED_TOOL_NAME,
        raw_input={"query": "AI"},
        raw_output=blocks,
    )
    assert flatten_tool_result(blocks) == "Query: AI regulation Europe\nTitle: Example"
    assert flatten_tool_result(output) == "Query: AI regulation Europe\nTitle: Example"
    assert flatten_tool_result("already text") == "already text"
