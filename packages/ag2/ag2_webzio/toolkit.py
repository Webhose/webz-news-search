from __future__ import annotations

import os
from collections.abc import Iterable

from ag2.middleware import ToolMiddleware
from ag2.tools import MCPServerConfig, MCPToolkit

from ag2_webzio.consts import (
    DEFAULT_MCP_URL,
    MCP_URL_ENV_NAME,
    PREFERRED_TOOL_NAME,
    SERVER_LABEL,
    TOKEN_ENV_NAME,
)


class WebzioConfigError(ValueError):
    """Raised when the Webzio MCP client cannot be configured or loaded."""


def resolve_api_token(api_token: str | None = None) -> str:
    token = (api_token or os.getenv(TOKEN_ENV_NAME) or "").strip()
    if not token:
        raise WebzioConfigError(
            f"missing Webz API token. set {TOKEN_ENV_NAME} or pass api_token."
        )
    return token


def resolve_mcp_url(mcp_url: str | None = None) -> str:
    url = (mcp_url or os.getenv(MCP_URL_ENV_NAME) or DEFAULT_MCP_URL).strip()
    if not url:
        raise WebzioConfigError("missing MCP url.")
    return url.rstrip("/")


def build_mcp_server_config(
    api_token: str | None = None,
    *,
    mcp_url: str | None = None,
) -> MCPServerConfig:
    return MCPServerConfig(
        server_url=resolve_mcp_url(mcp_url),
        authorization_token=resolve_api_token(api_token),
        allowed_tools=[PREFERRED_TOOL_NAME],
        server_label=SERVER_LABEL,
    )


class WebzioNewsSearchToolkit(MCPToolkit):
    """Toolkit that exposes Webz.io contextual news search to AG2 agents.

    Connects to the hosted News Search MCP server and registers
    ``news_search_by_webz`` with its live input schema from ``tools/list``.
    Filter fields are not hardcoded in this package — new server filters
    appear automatically at runtime.

    Pass the toolkit to an agent to register news search::

        toolkit = WebzioNewsSearchToolkit(api_token=...)
        agent = Agent("researcher", config=config, tools=[toolkit])

    Call ``search()`` when you want to register only the news search tool::

        agent = Agent("researcher", config=config, tools=[toolkit.search()])

    Reads ``WEBZ_API_TOKEN`` from the environment when ``api_token`` is omitted.
    """

    def __init__(
        self,
        api_token: str | None = None,
        *,
        mcp_url: str | None = None,
        middleware: Iterable[ToolMiddleware] = (),
    ) -> None:
        super().__init__(
            build_mcp_server_config(api_token, mcp_url=mcp_url),
            middleware=middleware,
        )

    def search(self) -> WebzioNewsSearchToolkit:
        """Return this toolkit, registering only the news search tool."""
        return self
