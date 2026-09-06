from __future__ import annotations

from pathlib import Path

import pytest

from ag2_webzio.consts import (
    DEFAULT_MCP_URL,
    PREFERRED_TOOL_NAME,
    SERVER_LABEL,
    TOKEN_ENV_NAME,
)
from ag2_webzio.toolkit import (
    WebzioConfigError,
    WebzioNewsSearchToolkit,
    build_mcp_server_config,
    resolve_api_token,
    resolve_mcp_url,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TOOLKIT_SOURCE = (PACKAGE_ROOT / "ag2_webzio" / "toolkit.py").read_text(encoding="utf-8")
CONSTS_SOURCE = (PACKAGE_ROOT / "ag2_webzio" / "consts.py").read_text(encoding="utf-8")

FILTER_NAMES_OWNED_BY_MCP = (
    "allow_all_dates",
    "exclude_domain",
    "domain_rank_gte",
    "domain_rank_lte",
    "trust_category",
    "political_bias",
    "min_similarity",
    "allow_multiple_chunks_per_article",
)


def test_resolve_api_token_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_ENV_NAME, raising=False)
    with pytest.raises(WebzioConfigError, match="missing Webz API token"):
        resolve_api_token()


def test_resolve_api_token_prefers_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_ENV_NAME, "from-env")
    assert resolve_api_token(" from-arg ") == "from-arg"


def test_resolve_mcp_url_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBZ_MCP_URL", raising=False)
    assert resolve_mcp_url() == DEFAULT_MCP_URL
    assert resolve_mcp_url("https://localhost:8765/mcp/") == "https://localhost:8765/mcp"


def test_build_mcp_server_config_uses_bearer_and_allowed_tools() -> None:
    config = build_mcp_server_config("secret-token", mcp_url="https://example.test/mcp")
    assert config.server_url == "https://example.test/mcp"
    assert config.authorization_token == "secret-token"
    assert config.allowed_tools == [PREFERRED_TOOL_NAME]
    assert config.server_label == SERVER_LABEL


def test_toolkit_wraps_mcp_server_config() -> None:
    toolkit = WebzioNewsSearchToolkit(api_token="tok", mcp_url="https://example.test/mcp")
    assert isinstance(toolkit, WebzioNewsSearchToolkit)
    assert toolkit.search() is toolkit


def test_toolkit_source_does_not_hardcode_mcp_filters() -> None:
    combined = TOOLKIT_SOURCE + CONSTS_SOURCE
    for name in FILTER_NAMES_OWNED_BY_MCP:
        assert name not in combined, f"wrapper must not hardcode MCP filter {name}"


def test_public_exports() -> None:
    import ag2_webzio

    for name in (
        "WebzioNewsSearchToolkit",
        "WebzioConfigError",
        "DEFAULT_MCP_URL",
        "TOKEN_ENV_NAME",
        "build_mcp_server_config",
        "resolve_api_token",
        "resolve_mcp_url",
    ):
        assert hasattr(ag2_webzio, name)
