from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools._mcp import WebzMcpError, validate_token


class WebzProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            validate_token((credentials or {}).get("api_token", ""))
        except WebzMcpError as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from exc
