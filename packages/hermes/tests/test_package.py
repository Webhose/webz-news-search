"""Integration contracts for the shipped package, using Hermes's real loader."""

import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import httpx

from agent.secret_scope import reset_multiplex_context, reset_secret_scope, set_multiplex_context, set_secret_scope
from hermes_cli.agent_plugins import load_agent_plugin
from hermes_cli.plugin_validate import validate_plugin_dir
from tools.mcp_tool_config import _interpolate_env_vars, _load_mcp_config, _require_rendered_remote
from tools.mcp_tool_errors import _make_redirect_header_stripper

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "webz-news-search"
SERVER = "webz"
TOOL = "mcp__webz__news_search_by_webz"
MCP_URL = "https://news-search-mcp.webz.io/mcp"
EXPECTED_SKILLS = {"news-search"}
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".venv")


def _install(home: Path) -> Path:
    installed = home / "plugins" / PLUGIN
    shutil.copytree(ROOT, installed, ignore=IGNORE)
    bundled = home / "empty-bundled"
    bundled.mkdir(exist_ok=True)
    return bundled


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="webz-package-")
        self.addCleanup(self.temp.cleanup)
        self.package = load_agent_plugin(ROOT, Path(self.temp.name))

    def test_hermes_admission_has_no_warnings_or_skipped_components(self):
        report = validate_plugin_dir(ROOT)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.warnings, [])
        self.assertEqual(self.package.diagnostics, ())
        self.assertEqual(self.package.name, PLUGIN)
        self.assertEqual(set(self.package.mcp_servers), {SERVER})
        self.assertEqual({s.name for s in self.package.skills}, EXPECTED_SKILLS)

    def test_manifest_and_skill_versions_match(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        for skill in self.package.skills:
            self.assertEqual(str(skill.frontmatter["version"]), manifest["version"])

    def test_server_is_the_hosted_https_endpoint_with_a_token_placeholder(self):
        server = self.package.mcp_servers[SERVER]
        self.assertEqual(server["url"], MCP_URL)
        self.assertEqual(server["headers"], {"Authorization": "Bearer ${WEBZ_API_TOKEN}"})
        self.assertTrue(server["strict_redirect_headers"])
        self.assertNotIn("command", server)

    def test_a_cleartext_endpoint_is_refused_before_any_token_is_sent(self):
        copy = Path(self.temp.name) / "cleartext"
        shutil.copytree(ROOT, copy, ignore=IGNORE)
        mcp = json.loads((copy / "mcp.json").read_text(encoding="utf-8"))
        mcp["mcpServers"][SERVER]["url"] = "http://news-search-mcp.webz.io/mcp"
        (copy / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        package = load_agent_plugin(copy, Path(self.temp.name) / "cleartext-data")
        self.assertEqual(package.mcp_servers, {})
        self.assertIn("https", " ".join(d.message for d in package.diagnostics))

    def test_profile_credentials_override_foreign_process_credentials(self):
        with patch.dict(os.environ, {"WEBZ_API_TOKEN": "foreign-profile-value"}):
            for key in ("profile-a-value", "profile-b-value"):
                with self.subTest(profile=key):
                    token = set_secret_scope({"WEBZ_API_TOKEN": key})
                    try:
                        server = _interpolate_env_vars(self.package.mcp_servers[SERVER])
                        self.assertEqual(server["headers"]["Authorization"], f"Bearer {key}")
                    finally:
                        reset_secret_scope(token)

    def test_missing_profile_token_fails_before_a_network_request(self):
        with patch.dict(os.environ, {"WEBZ_API_TOKEN": "foreign-profile-value"}):
            multiplex = set_multiplex_context(True)
            token = set_secret_scope({})
            try:
                server = _interpolate_env_vars(self.package.mcp_servers[SERVER])
                with self.assertRaisesRegex(ValueError, "WEBZ_API_TOKEN"):
                    _require_rendered_remote(SERVER, server)
            finally:
                reset_secret_scope(token)
                reset_multiplex_context(multiplex)

    def test_bundled_skill_meets_hermes_authoring_contract(self):
        required = ["When to Use", "Prerequisites", "How to Run", "Quick Reference",
                    "Procedure", "Pitfalls", "Verification"]
        for skill in self.package.skills:
            self.assertLessEqual(len(skill.description), 60)
            self.assertTrue(skill.description.endswith("."))
            self.assertTrue(skill.frontmatter["author"].startswith("Shaked Degani (ShakedDegani)"))
            body = skill.skill_md.read_text(encoding="utf-8")
            self.assertTrue(body.split("---", 2)[2].lstrip().startswith("# "))
            positions = [body.index(f"## {heading}") for heading in required]
            self.assertEqual(positions, sorted(positions))

    def test_skill_examples_match_the_live_tool_schema(self):
        schemas = json.loads((ROOT / "tests" / "fixtures" / "mcp-schema.json").read_text(encoding="utf-8"))
        schema = schemas[TOOL]["parameters"]

        def accepts(value, field):
            options = field.get("anyOf", [field])
            for option in options:
                kind = option.get("type")
                if kind == "null" and value is None:
                    return True
                if kind == "string" and isinstance(value, str):
                    return True
                if kind == "integer" and type(value) is int:
                    return True
                if kind == "number" and type(value) in (int, float):
                    return True
                if kind == "boolean" and type(value) is bool:
                    return True
                if kind == "array" and isinstance(value, list):
                    return all(accepts(item, option.get("items", {})) for item in value)
            return False

        for skill in self.package.skills:
            body = skill.skill_md.read_text(encoding="utf-8")
            languages = re.findall(r"^```([^\n`]+)$", body, re.MULTILINE)
            examples = re.findall(rf"call `({TOOL})` with:\n\n```json\n(.*?)\n```", body,
                                  re.DOTALL | re.IGNORECASE)
            self.assertTrue(examples)
            self.assertEqual(len(examples), len(languages), "Every example must identify its MCP tool")
            for _tool, raw in examples:
                args = json.loads(raw)
                self.assertLessEqual(set(args), set(schema["properties"]))
                self.assertLessEqual(set(schema.get("required", [])), set(args))
                for key, value in args.items():
                    with self.subTest(argument=key):
                        self.assertTrue(accepts(value, schema["properties"][key]), (key, value))

    def test_installed_package_exposes_skill_and_mcp_only_when_enabled(self):
        from hermes_cli.plugins import PluginManager
        from tools.skills_tool import skill_view

        home = Path(self.temp.name) / "home"
        bundled = _install(home)
        with patch.dict(os.environ, {"HERMES_HOME": str(home), "HERMES_BUNDLED_PLUGINS": str(bundled)}):
            for enabled in (False, True):
                with self.subTest(enabled=enabled):
                    (home / "config.yaml").write_text(
                        "plugins:\n  enabled: " + (f"[{PLUGIN}]" if enabled else "[]") + "\n",
                        encoding="utf-8",
                    )
                    manager = PluginManager(scope_key=str(home))
                    try:
                        manager.discover_and_load()
                        self.assertEqual(set(manager.get_portable_mcp_servers()), {SERVER} if enabled else set())
                        skills = manager.list_plugin_skill_metadata()
                        self.assertEqual(len(skills), len(EXPECTED_SKILLS) if enabled else 0)
                        if enabled:
                            row = next(p for p in manager.list_plugins() if p["name"] == PLUGIN)
                            self.assertIsNone(row["error"])
                            with patch("hermes_cli.plugins.get_plugin_manager", return_value=manager):
                                for skill in skills:
                                    self.assertTrue(skill["name"].endswith(":news-search"), skill["name"])
                                    viewed = json.loads(skill_view(skill["name"]))
                                    self.assertTrue(viewed["success"], viewed)
                    finally:
                        manager.unload()

    def test_enabled_package_renders_the_profile_token_into_mcp_config(self):
        from hermes_cli.plugins import PluginManager

        home = Path(self.temp.name) / "configured-home"
        bundled = _install(home)
        (home / "config.yaml").write_text(f"plugins:\n  enabled: [{PLUGIN}]\n", encoding="utf-8")
        with patch.dict(os.environ, {"HERMES_HOME": str(home), "HERMES_BUNDLED_PLUGINS": str(bundled),
                                     "WEBZ_API_TOKEN": "foreign-profile-value"}):
            manager = PluginManager(scope_key=str(home))
            multiplex = set_multiplex_context(True)
            token = set_secret_scope({"WEBZ_API_TOKEN": "profile-token"})
            try:
                manager.discover_and_load()
                with patch("hermes_cli.plugins.get_plugin_manager", return_value=manager):
                    servers = _load_mcp_config()
                self.assertEqual(set(servers), {SERVER})
                server = _require_rendered_remote(SERVER, _interpolate_env_vars(servers[SERVER]))
                self.assertEqual(server["url"], MCP_URL)
                self.assertEqual(server["headers"]["Authorization"], "Bearer profile-token")
                self.assertTrue(server["strict_redirect_headers"])
            finally:
                manager.unload()
                reset_secret_scope(token)
                reset_multiplex_context(multiplex)


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_rpc_requests_send_the_profile_token(self):
        with tempfile.TemporaryDirectory() as data:
            package = load_agent_plugin(ROOT, Path(data))
        token = set_secret_scope({"WEBZ_API_TOKEN": "fixture-token"})
        try:
            server = _require_rendered_remote(SERVER, _interpolate_env_vars(package.mcp_servers[SERVER]))
        finally:
            reset_secret_scope(token)
        received = []

        def capture(request):
            received.append(request)
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {}})

        factory = _make_redirect_header_stripper(
            httpx, httpx.URL(server["url"]), strict=server["strict_redirect_headers"],
            configured_header_names={key.lower() for key in server["headers"]},
        )
        async with factory(headers=server["headers"], transport=httpx.MockTransport(capture)) as client:
            for method in ("initialize", "tools/list", "tools/call"):
                await client.post(server["url"], json={"jsonrpc": "2.0", "id": 1, "method": method})
        self.assertEqual(len(received), 3)
        for request in received:
            self.assertEqual(request.url.scheme, "https")
            self.assertEqual(request.headers["Authorization"], "Bearer fixture-token")

    async def test_redirect_cannot_leak_the_token_to_another_origin(self):
        with tempfile.TemporaryDirectory() as data:
            server = load_agent_plugin(ROOT, Path(data)).mcp_servers[SERVER]
        received = []

        def redirect(request):
            received.append(request)
            if request.url.host == "news-search-mcp.webz.io":
                return httpx.Response(307, headers={"Location": "https://other.example/mcp"})
            return httpx.Response(200)

        headers = {**server["headers"], "Authorization": "Bearer fixture-token"}
        factory = _make_redirect_header_stripper(
            httpx, httpx.URL(server["url"]), strict=server["strict_redirect_headers"],
            configured_header_names={key.lower() for key in headers},
        )
        async with factory(headers=headers, follow_redirects=True, transport=httpx.MockTransport(redirect)) as client:
            await client.post(server["url"], json={"method": "tools/list"})
        self.assertEqual(len(received), 2)
        self.assertNotIn("Authorization", received[-1].headers)
