from __future__ import annotations

import json
import os
from typing import Any

from webz_groq.consts import (
    DEFAULT_MCP_URL,
    MCP_URL_ENV_NAME,
    PREFERRED_TOOL_NAME,
    SERVER_DESCRIPTION,
    SERVER_LABEL,
    TOKEN_ENV_NAME,
)


class WebzConfigError(ValueError):
    """Raised when the Webz MCP tool cannot be configured."""


def resolve_api_token(api_token: str | None = None) -> str:
    token = (api_token or os.getenv(TOKEN_ENV_NAME) or "").strip()
    if not token:
        raise WebzConfigError(
            f"missing Webz API token. set {TOKEN_ENV_NAME} or pass api_token."
        )
    return token


def resolve_mcp_url(mcp_url: str | None = None) -> str:
    url = (mcp_url or os.getenv(MCP_URL_ENV_NAME) or DEFAULT_MCP_URL).strip()
    if not url:
        raise WebzConfigError("missing MCP url.")
    if not url.startswith("https://"):
        raise WebzConfigError(
            f"MCP url must be https so the token is not sent in cleartext. got: {url}"
        )
    return url.rstrip("/")


def build_webz_mcp_tool(
    api_token: str | None = None,
    *,
    mcp_url: str | None = None,
    server_label: str = SERVER_LABEL,
    server_description: str = SERVER_DESCRIPTION,
    require_approval: str = "never",
    allowed_tools: list[str] | None = None,
) -> dict[str, Any]:
    """Build the remote MCP tool entry for Groq's Responses API ``tools`` list.

    Groq runs the tool loop server side: it calls ``tools/list`` on the Webz MCP
    server, gives the live schema to the model, and executes ``tools/call`` for
    any tool call the model returns. Filter fields are never hardcoded here.

    The token travels as an ``Authorization`` header, which Groq redacts from
    its logs. Webz does not accept the token as a URL query parameter.

    Pass ``allowed_tools=[]`` to drop the restriction and expose every tool the
    server advertises.
    """
    tool: dict[str, Any] = {
        "type": "mcp",
        "server_label": server_label,
        "server_url": resolve_mcp_url(mcp_url),
        "headers": {"Authorization": f"Bearer {resolve_api_token(api_token)}"},
        "require_approval": require_approval,
    }
    if server_description:
        tool["server_description"] = server_description
    names = [PREFERRED_TOOL_NAME] if allowed_tools is None else allowed_tools
    if names:
        tool["allowed_tools"] = names
    return tool


def _field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _output_items(response: Any) -> list[Any]:
    return list(_field(response, "output") or [])


def discovered_tool_names(response: Any) -> list[str]:
    """Tool names Groq discovered on the MCP server, from ``mcp_list_tools`` items."""
    names: list[str] = []
    for item in _output_items(response):
        if _field(item, "type") != "mcp_list_tools":
            continue
        for tool in _field(item, "tools") or []:
            name = _field(tool, "name")
            if name:
                names.append(str(name))
    return names


def extract_mcp_calls(response: Any) -> list[dict[str, Any]]:
    """Flatten ``mcp_call`` output items into plain dicts.

    Use it to confirm the model actually searched instead of answering from
    memory, and to see which filters it chose.
    """
    calls: list[dict[str, Any]] = []
    for item in _output_items(response):
        if _field(item, "type") != "mcp_call":
            continue
        calls.append(
            {
                "name": _field(item, "name", ""),
                "server_label": _field(item, "server_label", ""),
                "arguments": _parse_json(_field(item, "arguments")),
                "output": _field(item, "output", ""),
                "error": _field(item, "error"),
            }
        )
    return calls


def _parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def format_mcp_calls(calls: list[dict[str, Any]], *, output_chars: int = 400) -> str:
    """Render ``extract_mcp_calls()`` output for terminal or notebook printing."""
    if not calls:
        return "no MCP tool calls. the model answered without searching."

    lines = [f"{len(calls)} MCP tool call(s):"]
    for index, call in enumerate(calls, start=1):
        lines.append(f"\n#{index} {call['name']} (server: {call['server_label']})")
        lines.append(f"   arguments: {json.dumps(call['arguments'], ensure_ascii=False)}")
        if call.get("error"):
            lines.append(f"   error: {call['error']}")
            continue
        output = str(call.get("output") or "")
        excerpt = output[:output_chars]
        if len(output) > output_chars:
            excerpt += f"... ({len(output)} chars total)"
        lines.append(f"   output: {excerpt}")
    return "\n".join(lines)
