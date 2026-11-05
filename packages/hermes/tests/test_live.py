"""Live check against the hosted server. Skipped unless WEBZ_API_TOKEN is set."""

import json
import os
from pathlib import Path
import tempfile
import unittest

import httpx

from agent.secret_scope import reset_secret_scope, set_secret_scope
from hermes_cli.agent_plugins import load_agent_plugin
from tools.mcp_tool_config import _interpolate_env_vars, _require_rendered_remote

ROOT = Path(__file__).resolve().parents[1]
ACCEPT = "application/json, text/event-stream"


def _result(response: httpx.Response) -> dict:
    response.raise_for_status()
    body = response.text
    if response.headers.get("content-type", "").startswith("text/event-stream"):
        body = next(line[len("data: "):] for line in body.splitlines() if line.startswith("data: "))
    message = json.loads(body)
    if "error" in message:
        raise AssertionError(message["error"])
    return message["result"]


@unittest.skipUnless(os.environ.get("WEBZ_API_TOKEN"), "WEBZ_API_TOKEN is not set")
class LiveTests(unittest.TestCase):
    def test_tools_list_and_search_through_the_packaged_server(self):
        with tempfile.TemporaryDirectory() as data:
            package = load_agent_plugin(ROOT, Path(data))
        token = set_secret_scope({"WEBZ_API_TOKEN": os.environ["WEBZ_API_TOKEN"]})
        try:
            server = _require_rendered_remote("webz", _interpolate_env_vars(package.mcp_servers["webz"]))
        finally:
            reset_secret_scope(token)

        headers = {**server["headers"], "Accept": ACCEPT}
        with httpx.Client(headers=headers, timeout=60, follow_redirects=False) as client:
            init = client.post(server["url"], json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "webz-hermes-plugin-test", "version": "0.1.0"}},
            })
            _result(init)
            session = init.headers.get("mcp-session-id")
            if session:
                client.headers["Mcp-Session-Id"] = session
            client.post(server["url"], json={"jsonrpc": "2.0", "method": "notifications/initialized"})

            tools = _result(client.post(server["url"], json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
            tool = next(t for t in tools["tools"] if t["name"] == "news_search_by_webz")
            self.assertIn("query", tool["inputSchema"]["properties"])

            called = _result(client.post(server["url"], json={
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "news_search_by_webz",
                           "arguments": {"query": "artificial intelligence regulation", "k": 1}},
            }))
            self.assertFalse(called.get("isError"), called)
            text = "".join(part.get("text", "") for part in called["content"])
            self.assertIn("http", text)
            print(f"\nlive: {len(tool['inputSchema']['properties'])} parameters from tools/list; "
                  f"first result: {text[:200]!r}")
