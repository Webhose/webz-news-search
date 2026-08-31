from __future__ import annotations

import asyncio
import os
from collections.abc import Coroutine
from typing import Any, TypeVar

from llama_index.core.tools import FunctionTool
from llama_index.core.tools.types import BaseTool, ToolOutput
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

from llama_index.tools.webz.consts import (
    DEFAULT_MCP_URL,
    MCP_URL_ENV_NAME,
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
)

T = TypeVar("T")


class WebzConfigError(ValueError):
    """raised when the Webz MCP client cannot be configured or loaded."""


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
    return url.rstrip("/")


def build_mcp_headers(api_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_token}"}


def pick_news_search_tool(tools: list[BaseTool]) -> BaseTool:
    if not tools:
        raise WebzConfigError("MCP server returned no tools.")
    for tool in tools:
        if tool.metadata.name == PREFERRED_TOOL_NAME:
            return tool
    if len(tools) == 1:
        return tools[0]
    names = ", ".join(str(tool.metadata.name) for tool in tools)
    raise WebzConfigError(
        f"MCP server did not expose {PREFERRED_TOOL_NAME}. available tools: {names}"
    )


def tool_arg_names(tool: BaseTool) -> list[str]:
    schema = tool.metadata.fn_schema
    if schema is None:
        return []
    return list(schema.model_fields)


def flatten_mcp_call_result(result: Any) -> str:
    """turns an MCP CallToolResult into article text."""
    content = getattr(result, "content", None)
    if content:
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        if parts:
            return "\n".join(parts)
    return flatten_tool_result(result)


def flatten_tool_result(result: Any) -> str:
    """turns LlamaIndex ToolOutput / MCP content into article text."""
    if isinstance(result, ToolOutput):
        text = (result.content or "").strip()
        if text:
            return text
        result = result.raw_output
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts: list[str] = []
        for item in result:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts)
    return str(result)


def bind_live_mcp_tool(
    tool: FunctionTool,
    api_token: str,
    mcp_url: str,
) -> FunctionTool:
    """
    rebinds an MCP FunctionTool so each call opens a fresh HTTP session.

    llama-index-tools-mcp keeps an httpx client on the first event loop.
    after asyncio.run() used to list tools, that loop is closed and
    tool.call() fails with a TaskGroup error. a new client per call
    keeps listing and invoking on separate loops.
    """
    tool_name = str(tool.metadata.name)

    async def run_async(**kwargs: Any) -> str:
        client = BasicMCPClient(mcp_url, headers=build_mcp_headers(api_token))
        result = await client.call_tool(tool_name, kwargs)
        return flatten_mcp_call_result(result)

    def run_sync(**kwargs: Any) -> str:
        return run_coroutine_sync(run_async(**kwargs))

    return FunctionTool.from_defaults(
        fn=run_sync,
        async_fn=run_async,
        tool_metadata=tool.metadata,
    )


def run_coroutine_sync(coro: Coroutine[Any, Any, T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise WebzConfigError(
        "cannot call the sync helper from a running event loop. "
        "use await aget_webz_tools() or await awebz_news_search()."
    )


async def aget_webz_tools(
    api_token: str | None = None,
    mcp_url: str | None = None,
) -> list[FunctionTool]:
    """
    loads every tool from the hosted Webz MCP server.

    params:
    - api_token: webz api token. defaults to WEBZ_API_TOKEN.
    - mcp_url: mcp endpoint. defaults to production.

    returns:
    - llamaindex function tools whose schemas come from tools/list.
    """
    token = resolve_api_token(api_token)
    url = resolve_mcp_url(mcp_url)
    client = BasicMCPClient(url, headers=build_mcp_headers(token))
    spec = McpToolSpec(client=client)
    # ponytail: schemas come from MCP tools/list; new filters ship with the server, not this package
    tools = await spec.to_tool_list_async()
    if not tools:
        raise WebzConfigError(f"MCP server at {url} returned no tools.")
    return [bind_live_mcp_tool(tool, token, url) for tool in tools]


def get_webz_tools(
    api_token: str | None = None,
    mcp_url: str | None = None,
) -> list[FunctionTool]:
    return run_coroutine_sync(aget_webz_tools(api_token=api_token, mcp_url=mcp_url))


async def awebz_news_search(
    api_token: str | None = None,
    mcp_url: str | None = None,
) -> FunctionTool:
    tools = await aget_webz_tools(api_token=api_token, mcp_url=mcp_url)
    picked = pick_news_search_tool(tools)
    if not isinstance(picked, FunctionTool):
        raise WebzConfigError("preferred MCP tool is not a FunctionTool.")
    return picked


def WebzNewsSearch(
    api_token: str | None = None,
    mcp_url: str | None = None,
) -> FunctionTool:
    """
    returns the live news search tool from the hosted MCP server.

    params:
    - api_token: webz api token. defaults to WEBZ_API_TOKEN.
    - mcp_url: mcp endpoint. defaults to production.

    returns:
    - llamaindex function tool with the current MCP input schema.
    """
    return run_coroutine_sync(
        awebz_news_search(api_token=api_token, mcp_url=mcp_url)
    )
