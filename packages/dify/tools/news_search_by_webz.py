from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._mcp import WebzMcpError, call_news_search


class WebzNewsSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        api_token = (self.runtime.credentials or {}).get("api_token", "")
        try:
            text = call_news_search(api_token, tool_parameters)
        except WebzMcpError as exc:
            raise ValueError(str(exc)) from exc
        yield self.create_text_message(text)
