"""Webz.io News Search on Groq's Responses API via remote MCP.

Groq orchestrates the tool loop server side. This module only builds the
remote MCP tool entry and reads the tool calls back out of a response.
"""

from webz_groq.consts import (
    DEFAULT_MCP_URL,
    DEFAULT_MODEL,
    GROQ_BASE_URL,
    GROQ_TOKEN_ENV_NAME,
    MCP_URL_ENV_NAME,
    PREFERRED_TOOL_NAME,
    SERVER_DESCRIPTION,
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

__all__ = [
    "DEFAULT_MCP_URL",
    "DEFAULT_MODEL",
    "GROQ_BASE_URL",
    "GROQ_TOKEN_ENV_NAME",
    "MCP_URL_ENV_NAME",
    "PREFERRED_TOOL_NAME",
    "SERVER_DESCRIPTION",
    "SERVER_LABEL",
    "TOKEN_ENV_NAME",
    "WebzConfigError",
    "build_webz_mcp_tool",
    "discovered_tool_names",
    "extract_mcp_calls",
    "format_mcp_calls",
    "resolve_api_token",
    "resolve_mcp_url",
]
