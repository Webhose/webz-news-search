from __future__ import annotations

import os
from types import TracebackType
from typing import Any

from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from crewai_tools.adapters.mcp_adapter import MCPServerAdapter

DEFAULT_MCP_URL = "https://news-search-mcp.webz.io/mcp"
TOKEN_ENV_NAME = "WEBZ_API_TOKEN"
MCP_URL_ENV_NAME = "WEBZ_MCP_URL"
PREFERRED_TOOL_NAME = "news_search_by_webz"
MCP_TRANSPORT = "streamable-http"


class WebzConfigError(ValueError):
    """Raised when the Webz MCP client cannot be configured or loaded."""


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


def build_server_params(
    api_token: str | None = None,
    *,
    mcp_url: str | None = None,
) -> dict[str, Any]:
    token = resolve_api_token(api_token)
    url = resolve_mcp_url(mcp_url)
    return {
        "url": url,
        "transport": MCP_TRANSPORT,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def pick_news_search_tool(tools: list[BaseTool]) -> BaseTool:
    if not tools:
        raise WebzConfigError("MCP server returned no tools.")
    for tool in tools:
        if tool.name == PREFERRED_TOOL_NAME:
            return tool
    if len(tools) == 1:
        return tools[0]
    names = ", ".join(tool.name for tool in tools)
    raise WebzConfigError(
        f"MCP server did not expose {PREFERRED_TOOL_NAME}. available tools: {names}"
    )


class WebzioNewsSearchToolSchema(BaseModel):
    """Minimal static schema; replaced at init with the live MCP schema."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(..., description="Natural-language news search query")


class WebzioNewsSearchTool(BaseTool):
    """Search global news with Webz.io via the hosted News Search MCP server.

    Filter fields are loaded live from MCP ``tools/list``. New server filters appear
    automatically at runtime without republishing crewai-tools.

    Use as a context manager or call ``stop()`` when done to shut down the MCP session.
    """

    name: str = PREFERRED_TOOL_NAME
    description: str = (
        "Search global news with Webz.io. Returns article excerpts with titles, "
        "URLs, and metadata. Filter by language, country, date, sentiment, domain, "
        "ticker, and more."
    )
    args_schema: type[BaseModel] = WebzioNewsSearchToolSchema
    package_dependencies: list[str] = Field(default_factory=lambda: ["mcp"])
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [
            EnvVar(
                name=TOKEN_ENV_NAME,
                description="Webz.io API token from the dashboard",
                required=True,
            ),
            EnvVar(
                name=MCP_URL_ENV_NAME,
                description="Override MCP endpoint for testing",
                required=False,
            ),
        ]
    )

    _adapter: MCPServerAdapter | None = PrivateAttr(default=None)
    _live_tool: BaseTool | None = PrivateAttr(default=None)

    def __init__(
        self,
        api_token: str | None = None,
        *,
        mcp_url: str | None = None,
        connect_timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._adapter = MCPServerAdapter(
            build_server_params(api_token, mcp_url=mcp_url),
            PREFERRED_TOOL_NAME,
            connect_timeout=connect_timeout,
        )
        self._live_tool = pick_news_search_tool(list(self._adapter.tools))
        self.args_schema = self._live_tool.args_schema
        self.description = self._live_tool.description

    @property
    def arg_names(self) -> list[str]:
        """Live argument names from the MCP tool schema."""
        return list(self.args_schema.model_fields.keys())

    def _run(self, **kwargs: Any) -> str:
        if self._live_tool is None:
            raise WebzConfigError("MCP news search tool is not initialized.")
        result = self._live_tool._run(**kwargs)
        return str(result)

    def stop(self) -> None:
        """Stop the underlying MCP server connection."""
        if self._adapter is not None:
            self._adapter.stop()
            self._adapter = None
            self._live_tool = None

    def __enter__(self) -> WebzioNewsSearchTool:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()
