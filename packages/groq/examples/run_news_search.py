"""
Run one Groq Responses call against the hosted Webz News Search MCP server.

usage:
  export WEBZ_API_TOKEN="your-webz-token"
  export GROQ_API_KEY="your-groq-key"
  python examples/run_news_search.py

Groq discovers news_search_by_webz, decides the filters, calls the MCP server,
and writes the answer. Nothing runs locally except this script.
"""

from __future__ import annotations

import os
import sys

from openai import OpenAI

from webz_groq import (
    DEFAULT_MODEL,
    GROQ_BASE_URL,
    GROQ_TOKEN_ENV_NAME,
    PREFERRED_TOOL_NAME,
    build_webz_mcp_tool,
    discovered_tool_names,
    extract_mcp_calls,
    format_mcp_calls,
)

PROMPT = (
    "Search Webz news for Nvidia supply-chain risk coverage from the last 14 days. "
    "Return the top 5 articles with headline, publisher, and URL, then summarize."
)


def main() -> None:
    groq_key = os.getenv(GROQ_TOKEN_ENV_NAME)
    if not groq_key:
        raise SystemExit(f"set {GROQ_TOKEN_ENV_NAME} (https://console.groq.com/keys)")

    client = OpenAI(base_url=GROQ_BASE_URL, api_key=groq_key)
    tools = [build_webz_mcp_tool()]  # reads WEBZ_API_TOKEN

    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=PROMPT,
        tools=tools,
        temperature=0.1,
        top_p=0.4,
    )

    discovered = discovered_tool_names(response)
    print("tools discovered by Groq:", discovered or "(not reported)")
    print("---")
    calls = extract_mcp_calls(response)
    print(format_mcp_calls(calls))
    print("--- final answer ---")
    print(response.output_text)

    if not calls:
        print(
            f"\nwarning: the model never called {PREFERRED_TOOL_NAME}. "
            "the answer above is unsourced.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"groq news search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
