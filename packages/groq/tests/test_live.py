from __future__ import annotations

import os

import pytest

from webz_groq import (
    DEFAULT_MODEL,
    GROQ_BASE_URL,
    GROQ_TOKEN_ENV_NAME,
    PREFERRED_TOOL_NAME,
    TOKEN_ENV_NAME,
    build_webz_mcp_tool,
    extract_mcp_calls,
    resolve_api_token,
    resolve_mcp_url,
)

needs_webz_token = pytest.mark.skipif(
    not os.getenv(TOKEN_ENV_NAME),
    reason=f"{TOKEN_ENV_NAME} is not set",
)
needs_groq_key = pytest.mark.skipif(
    not os.getenv(GROQ_TOKEN_ENV_NAME),
    reason=f"{GROQ_TOKEN_ENV_NAME} is not set",
)

INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "webz-groq-live-test", "version": "0.1.0"},
    },
}
MCP_ACCEPT = "application/json, text/event-stream"


@needs_webz_token
def test_live_mcp_endpoint_accepts_the_bearer_header() -> None:
    """The exact auth Groq performs on its side. A 401 here surfaces as a 424 from Groq."""
    import httpx

    response = httpx.post(
        resolve_mcp_url(),
        json=INITIALIZE_REQUEST,
        headers={
            "Authorization": f"Bearer {resolve_api_token()}",
            "Accept": MCP_ACCEPT,
        },
        timeout=30,
    )
    assert response.status_code == 200, response.text


def test_live_mcp_endpoint_rejects_anonymous_access() -> None:
    import httpx

    response = httpx.post(
        resolve_mcp_url(),
        json=INITIALIZE_REQUEST,
        headers={"Accept": MCP_ACCEPT},
        timeout=30,
    )
    assert response.status_code == 401


@needs_webz_token
@needs_groq_key
def test_live_groq_runs_the_webz_tool_loop() -> None:
    from openai import OpenAI

    client = OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=os.environ[GROQ_TOKEN_ENV_NAME],
    )
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=(
            f"Call {PREFERRED_TOOL_NAME} once with query 'EU AI regulation', "
            "k 3, days 30, then list the headlines with URLs."
        ),
        tools=[build_webz_mcp_tool()],
        temperature=0.1,
        top_p=0.4,
    )

    calls = extract_mcp_calls(response)
    assert calls, "model answered without calling the Webz MCP tool"
    assert calls[0]["name"] == PREFERRED_TOOL_NAME
    assert not calls[0]["error"], calls[0]["error"]
    assert response.output_text.strip()
