"""
Construct a WebzioNewsSearchTool and run one search against the hosted MCP server.

Usage:
  python examples/run_news_search.py

Loads WEBZ_API_TOKEN from a nearby .env file (repo root or packages/crewai/.env)
when the variable is not already exported.

Or pass the token in code with WebzioNewsSearchTool(api_token="...").
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def load_env_file() -> None:
    """Load WEBZ_API_TOKEN (and other vars) from a nearby .env file if unset."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        for raw_line in resolved.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.lstrip("=").strip()
            if key and key not in os.environ:
                os.environ[key] = value
        return


from crewai_webzio import WebzioNewsSearchTool

QUERY = "recent developments on EU AI regulation"


def main() -> None:
    load_env_file()
    token = os.getenv("WEBZ_API_TOKEN")
    with (
        WebzioNewsSearchTool(api_token=token)
        if token
        else WebzioNewsSearchTool()
    ) as tool:
        print("tool name:", tool.name)
        print("live args from MCP tools/list:", sorted(tool.arg_names))
        print("---")
        print(tool._run(query=QUERY, k=3), end="\n\n")
        print("SUCCESS ! tool is ready for Agent(tools=[tool])")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
