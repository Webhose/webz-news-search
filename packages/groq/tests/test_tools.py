from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from webz_groq.consts import (
    DEFAULT_MCP_URL,
    PREFERRED_TOOL_NAME,
    SERVER_LABEL,
    TOKEN_ENV_NAME,
)
from webz_groq.tools import (
    WebzConfigError,
    build_webz_mcp_tool,
    discovered_tool_names,
    extract_mcp_calls,
    format_mcp_calls,
    resolve_api_token,
    resolve_mcp_url,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TOOLS_SOURCE = (PACKAGE_ROOT / "webz_groq" / "tools.py").read_text(encoding="utf-8")
CONSTS_SOURCE = (PACKAGE_ROOT / "webz_groq" / "consts.py").read_text(encoding="utf-8")

FILTER_NAMES_OWNED_BY_MCP = (
    "allow_all_dates",
    "exclude_domain",
    "domain_rank_gte",
    "domain_rank_lte",
    "trust_category",
    "min_similarity",
    "allow_multiple_chunks_per_article",
)


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


def test_resolve_mcp_url_rejects_cleartext() -> None:
    """Groq forwards the Bearer header to server_url, so it must be https."""
    with pytest.raises(WebzConfigError, match="must be https"):
        resolve_mcp_url("http://news-search-mcp.webz.io/mcp")


def test_build_tool_shape_matches_groq_remote_mcp() -> None:
    tool = build_webz_mcp_tool("secret-token", mcp_url="https://example.test/mcp")
    assert tool["type"] == "mcp"
    assert tool["server_label"] == SERVER_LABEL
    assert tool["server_url"] == "https://example.test/mcp"
    assert tool["headers"] == {"Authorization": "Bearer secret-token"}
    assert tool["require_approval"] == "never"
    assert tool["allowed_tools"] == [PREFERRED_TOOL_NAME]
    assert tool["server_description"]


def test_build_tool_keeps_token_out_of_the_url() -> None:
    """Unlike Tavily and Exa, Webz authenticates by header, never by query string."""
    tool = build_webz_mcp_tool("secret-token")
    assert "secret-token" not in tool["server_url"]
    assert "?" not in tool["server_url"]


def test_build_tool_allows_widening_to_every_server_tool() -> None:
    """An empty list drops the field, since providers disagree on what [] means."""
    tool = build_webz_mcp_tool("tok", allowed_tools=[])
    assert "allowed_tools" not in tool


def test_source_does_not_hardcode_mcp_filters() -> None:
    combined = TOOLS_SOURCE + CONSTS_SOURCE
    for name in FILTER_NAMES_OWNED_BY_MCP:
        assert name not in combined, f"wrapper must not hardcode MCP filter {name}"


def _response(*items: object) -> SimpleNamespace:
    return SimpleNamespace(output=list(items))


def test_extract_mcp_calls_reads_sdk_objects() -> None:
    response = _response(
        SimpleNamespace(type="reasoning"),
        SimpleNamespace(
            type="mcp_call",
            name=PREFERRED_TOOL_NAME,
            server_label=SERVER_LABEL,
            arguments='{"query": "nvidia", "k": 5}',
            output="article excerpts",
            error=None,
        ),
    )
    calls = extract_mcp_calls(response)
    assert len(calls) == 1
    assert calls[0]["name"] == PREFERRED_TOOL_NAME
    assert calls[0]["arguments"] == {"query": "nvidia", "k": 5}


def test_extract_mcp_calls_reads_plain_dicts() -> None:
    response = {
        "output": [
            {
                "type": "mcp_call",
                "name": PREFERRED_TOOL_NAME,
                "server_label": SERVER_LABEL,
                "arguments": {"query": "boeing", "sentiment": ["negative"]},
                "output": "",
                "error": "unauthorized",
            }
        ]
    }
    calls = extract_mcp_calls(response)
    assert calls[0]["arguments"]["sentiment"] == ["negative"]
    assert calls[0]["error"] == "unauthorized"


def test_extract_mcp_calls_survives_unparsable_arguments() -> None:
    response = _response(
        SimpleNamespace(type="mcp_call", name="x", arguments="not json", output="")
    )
    assert extract_mcp_calls(response)[0]["arguments"] == "not json"


def test_discovered_tool_names_reads_mcp_list_tools() -> None:
    response = _response(
        SimpleNamespace(
            type="mcp_list_tools",
            tools=[SimpleNamespace(name=PREFERRED_TOOL_NAME)],
        )
    )
    assert discovered_tool_names(response) == [PREFERRED_TOOL_NAME]


def test_discovered_tool_names_is_empty_without_output() -> None:
    assert discovered_tool_names(SimpleNamespace(output=None)) == []


def test_format_mcp_calls_flags_a_model_that_never_searched() -> None:
    assert "no MCP tool calls" in format_mcp_calls([])


def test_format_mcp_calls_truncates_long_output() -> None:
    calls = [
        {
            "name": PREFERRED_TOOL_NAME,
            "server_label": SERVER_LABEL,
            "arguments": {"query": "nvidia"},
            "output": "x" * 900,
            "error": None,
        }
    ]
    rendered = format_mcp_calls(calls, output_chars=100)
    assert "900 chars total" in rendered
    assert "x" * 200 not in rendered
