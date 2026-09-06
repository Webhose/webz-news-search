"""
Construct a WebzioNewsSearchToolkit and list tools from the hosted MCP server.

Usage:
  export WEBZ_API_TOKEN="your-token"
  python examples/run_news_search.py

Or pass the token in code with WebzioNewsSearchToolkit(api_token="...").
"""

from __future__ import annotations

import asyncio
import os
import sys

from ag2_webzio import WebzioNewsSearchToolkit
from ag2_webzio.consts import PREFERRED_TOOL_NAME


async def main() -> None:
    token = os.getenv("WEBZ_API_TOKEN")
    toolkit = (
        WebzioNewsSearchToolkit(api_token=token) if token else WebzioNewsSearchToolkit()
    )

    schemas = await toolkit.schemas(context=None)  # type: ignore[arg-type]
    names = sorted(schema.function.name for schema in schemas)
    print("discovered tools:", names)
    assert PREFERRED_TOOL_NAME in names, f"expected {PREFERRED_TOOL_NAME} in {names}"
    print("SUCCESS ! toolkit is ready for Agent(tools=[toolkit])")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"toolkit setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
