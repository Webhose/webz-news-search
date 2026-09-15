from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from tools._mcp import (
    DEFAULT_MCP_URL,
    PREFERRED_TOOL_NAME,
    WebzMcpError,
    build_arguments,
    call_news_search,
    flatten_tool_content,
    parse_jsonrpc_body,
    resolve_mcp_url,
    split_csv,
    validate_token,
)


def test_resolve_mcp_url_strips_slash() -> None:
    assert resolve_mcp_url("https://news-search-mcp.webz.io/mcp/") == DEFAULT_MCP_URL


def test_split_csv_drops_blanks() -> None:
    assert split_csv(" US, GB , ") == ["US", "GB"]


def test_build_arguments_maps_csv_and_skips_empty() -> None:
    args = build_arguments(
        {
            "query": "EU AI Act",
            "k": 5,
            "days": 0,
            "language": "english, french",
            "country": "US,GB",
            "allow_all_dates": False,
            "sentiment": "",
        }
    )
    assert args == {
        "query": "EU AI Act",
        "k": 5,
        "language": ["english", "french"],
        "country": ["US", "GB"],
    }


def test_build_arguments_merges_additional_filters() -> None:
    args = build_arguments(
        {
            "query": "Nvidia",
            "ticker": "NVDA",
            "additional_filters": '{"source_type": ["news"], "k": 3}',
        }
    )
    assert args["ticker"] == ["NVDA"]
    assert args["source_type"] == ["news"]
    assert args["k"] == 3


def test_build_arguments_rejects_bad_json() -> None:
    with pytest.raises(WebzMcpError, match="valid JSON"):
        build_arguments({"query": "x", "additional_filters": "{"})


def test_parse_jsonrpc_body_reads_last_sse_event() -> None:
    body = "event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"ok\":true}}\n\n"
    parsed = parse_jsonrpc_body(body, "text/event-stream")
    assert parsed["result"] == {"ok": True}


def test_flatten_tool_content_joins_text_blocks() -> None:
    text = flatten_tool_content(
        {
            "content": [
                {"type": "text", "text": "Query: foo"},
                {"type": "text", "text": "title: bar"},
            ]
        }
    )
    assert "Query: foo" in text
    assert "title: bar" in text


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        body: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = body
        self.headers = headers or {"content-type": "application/json"}


class FakeClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[SimpleNamespace] = []

    def post(self, url: str, headers: dict[str, str], json: dict) -> FakeResponse:
        self.calls.append(SimpleNamespace(url=url, headers=headers, json=json, method="POST"))
        if not self.responses:
            raise AssertionError("unexpected MCP POST")
        return self.responses.pop(0)

    def delete(self, url: str, headers: dict[str, str]) -> FakeResponse:
        self.calls.append(SimpleNamespace(url=url, headers=headers, json=None, method="DELETE"))
        return FakeResponse(204, "")

    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_validate_token_uses_initialize_only(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient(
        [
            FakeResponse(
                200,
                '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}',
                {"mcp-session-id": "sess-1", "content-type": "application/json"},
            ),
            FakeResponse(200, ""),
        ]
    )
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client)
    validate_token("token-1")
    methods = [call.json.get("method") if call.json else None for call in client.calls]
    assert methods[0] == "initialize"
    assert "tools/call" not in methods


def test_call_news_search_posts_preferred_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    result = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"content": [{"type": "text", "text": "Query: EU AI Act"}]},
    }
    client = FakeClient(
        [
            FakeResponse(
                200,
                '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}',
                {"mcp-session-id": "sess-1", "content-type": "application/json"},
            ),
            FakeResponse(200, ""),
            FakeResponse(200, __import__("json").dumps(result)),
        ]
    )
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client)
    text = call_news_search("token-1", {"query": "EU AI Act", "k": 1, "language": "english"})
    assert text == "Query: EU AI Act"
    call_payload = next(call.json for call in client.calls if call.json and call.json.get("method") == "tools/call")
    assert call_payload["params"]["name"] == PREFERRED_TOOL_NAME
    assert call_payload["params"]["arguments"] == {
        "query": "EU AI Act",
        "k": 1,
        "language": ["english"],
    }


def test_call_news_search_rejects_missing_query() -> None:
    with pytest.raises(WebzMcpError, match="query is required"):
        call_news_search("token-1", {"k": 1})
