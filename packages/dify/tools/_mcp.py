from __future__ import annotations

import json
from typing import Any

import httpx

DEFAULT_MCP_URL = "https://news-search-mcp.webz.io/mcp"
PREFERRED_TOOL_NAME = "news_search_by_webz"
MCP_PROTOCOL_VERSION = "2025-06-18"
CLIENT_NAME = "dify-plugin-webz-news-search"
CLIENT_VERSION = "0.1.0"
REQUEST_TIMEOUT_SECONDS = 60.0
CONNECT_TIMEOUT_SECONDS = 15.0

CSV_KEYS = (
    "language",
    "country",
    "sentiment",
    "category",
    "domain",
    "exclude_domain",
    "topic",
    "person",
    "organization",
    "location",
    "ticker",
    "political_bias",
)
NUMBER_KEYS = (
    "k",
    "days",
    "domain_rank_gte",
    "domain_rank_lte",
    "score_gte",
    "score_lte",
)
BOOLEAN_KEYS = ("allow_all_dates", "allow_multiple_chunks_per_article")
JSON_KEY = "additional_filters"
SKIP_WHEN_ZERO = frozenset(
    ("days", "domain_rank_gte", "domain_rank_lte", "score_gte", "score_lte")
)


class WebzMcpError(ValueError):
    """raised when the hosted Webz MCP request cannot complete."""


def resolve_mcp_url(mcp_url: str | None = None) -> str:
    url = (mcp_url or DEFAULT_MCP_URL).strip()
    if not url:
        raise WebzMcpError("missing MCP url.")
    return url.rstrip("/")


def split_csv(value: str) -> list[str]:
    items = [part.strip() for part in value.split(",")]
    return [item for item in items if item]


def build_arguments(tool_parameters: dict[str, Any]) -> dict[str, Any]:
    """
    maps Dify tool fields onto news_search_by_webz arguments.

    params:
    - tool_parameters: values from the Dify tool form.

    returns:
    - json-rpc arguments for tools/call.
    """
    args: dict[str, Any] = {}
    extra: dict[str, Any] = {}

    for key, raw in tool_parameters.items():
        if raw is None:
            continue
        if key == JSON_KEY:
            extra = parse_additional_filters(raw)
            continue
        if isinstance(raw, str) and not raw.strip():
            continue
        if key in CSV_KEYS:
            if isinstance(raw, list):
                values = [str(item).strip() for item in raw if str(item).strip()]
            else:
                values = split_csv(str(raw))
            if values:
                args[key] = values
            continue
        if key in BOOLEAN_KEYS:
            if raw is True or raw == "true":
                args[key] = True
            continue
        if key in NUMBER_KEYS:
            number = to_number(raw)
            if number is None:
                continue
            if key in SKIP_WHEN_ZERO and number == 0:
                continue
            args[key] = number
            continue
        args[key] = raw

    for key, value in extra.items():
        if value is None or value == "":
            continue
        args[key] = value
    return args


def parse_additional_filters(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise WebzMcpError("additional_filters must be a JSON object.")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WebzMcpError(f"additional_filters must be valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise WebzMcpError("additional_filters must be a JSON object.")
    return parsed


def to_number(raw: Any) -> int | float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    if "." in text:
        return float(text)
    return int(text)


def parse_jsonrpc_body(body: str, content_type: str = "") -> dict[str, Any]:
    text = (body or "").strip()
    if "text/event-stream" in content_type or text.startswith("event:") or "data:" in text:
        data_lines = [
            line[5:].strip()
            for line in text.splitlines()
            if line.strip().startswith("data:")
        ]
        data_lines = [line for line in data_lines if line]
        if not data_lines:
            raise WebzMcpError("MCP server returned no parseable SSE event.")
        text = data_lines[-1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WebzMcpError(f"MCP server returned invalid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise WebzMcpError("MCP server returned an unexpected payload.")
    return parsed


def flatten_tool_content(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in result.get("content") or []:
        if isinstance(block, dict) and block.get("text"):
            parts.append(str(block["text"]))
    if parts:
        return "\n".join(parts)
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and isinstance(structured.get("result"), str):
        return structured["result"]
    if structured:
        return json.dumps(structured)
    return ""


def request_headers(api_token: str, session_id: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return headers


def session_id_from_response(response: httpx.Response) -> str | None:
    return response.headers.get("mcp-session-id") or response.headers.get("Mcp-Session-Id")


def post_jsonrpc(
    client: httpx.Client,
    url: str,
    api_token: str,
    payload: dict[str, Any],
    session_id: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    response = client.post(
        url,
        headers=request_headers(api_token, session_id),
        json=payload,
    )
    if response.status_code in (401, 403):
        raise WebzMcpError("Webz rejected the API token.")
    if response.status_code >= 400:
        raise WebzMcpError(
            f"MCP request failed with HTTP {response.status_code}: {response.text[:500]}"
        )
    if not (response.text or "").strip() and str(payload.get("method", "")).startswith(
        "notifications/"
    ):
        return {}, session_id_from_response(response) or session_id
    envelope = parse_jsonrpc_body(response.text, response.headers.get("content-type", ""))
    if envelope.get("error"):
        err = envelope["error"]
        message = err.get("message") if isinstance(err, dict) else str(err)
        raise WebzMcpError(str(message) or "MCP request failed.")
    next_session = session_id_from_response(response) or session_id
    return envelope, next_session


def open_session(client: httpx.Client, url: str, api_token: str) -> str | None:
    envelope, session_id = post_jsonrpc(
        client,
        url,
        api_token,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
            },
        },
    )
    if not envelope.get("result"):
        raise WebzMcpError("MCP initialize returned no result.")
    if session_id:
        post_jsonrpc(
            client,
            url,
            api_token,
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            session_id,
        )
    return session_id


def close_session(
    client: httpx.Client,
    url: str,
    api_token: str,
    session_id: str | None,
) -> None:
    if not session_id:
        return
    try:
        client.delete(url, headers=request_headers(api_token, session_id))
    except httpx.HTTPError:
        return


def validate_token(api_token: str, mcp_url: str | None = None) -> None:
    token = (api_token or "").strip()
    if not token:
        raise WebzMcpError("Webz API token is required.")
    url = resolve_mcp_url(mcp_url)
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS)
    try:
        with httpx.Client(timeout=timeout) as client:
            session_id = open_session(client, url, token)
            close_session(client, url, token, session_id)
    except httpx.HTTPError as exc:
        raise WebzMcpError(f"could not reach Webz MCP: {exc}") from exc


def call_news_search(
    api_token: str,
    tool_parameters: dict[str, Any],
    mcp_url: str | None = None,
) -> str:
    """
    calls news_search_by_webz on the hosted MCP server.

    params:
    - api_token: webz api token.
    - tool_parameters: Dify tool fields.
    - mcp_url: mcp endpoint override.

    returns:
    - flattened article text from the tool result.
    """
    token = (api_token or "").strip()
    if not token:
        raise WebzMcpError("Webz API token is required.")
    url = resolve_mcp_url(mcp_url)
    arguments = build_arguments(tool_parameters)
    if not arguments.get("query"):
        raise WebzMcpError("query is required.")

    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS)
    try:
        with httpx.Client(timeout=timeout) as client:
            session_id = open_session(client, url, token)
            envelope, session_id = post_jsonrpc(
                client,
                url,
                token,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": PREFERRED_TOOL_NAME,
                        "arguments": arguments,
                    },
                },
                session_id,
            )
            close_session(client, url, token, session_id)
    except httpx.HTTPError as exc:
        raise WebzMcpError(f"could not reach Webz MCP: {exc}") from exc

    result = envelope.get("result") or {}
    if not isinstance(result, dict):
        raise WebzMcpError("MCP tools/call returned no result.")
    if result.get("isError"):
        raise WebzMcpError(flatten_tool_content(result) or "MCP tool call failed.")
    text = flatten_tool_content(result)
    if not text:
        raise WebzMcpError("MCP tools/call returned empty content.")
    return text
