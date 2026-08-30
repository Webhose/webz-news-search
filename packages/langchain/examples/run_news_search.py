"""
run a single News Search call through the LangChain wrapper.

usage:
  export WEBZ_API_TOKEN="your-token"
  python examples/run_news_search.py

or pass the token in code with WebzNewsSearch(api_token="...").
"""

from __future__ import annotations

import os
import sys

from langchain_webz import WebzNewsSearch

QUERY = "How many goals does Cristiano have and how many left to 1000?"


def main() -> None:
    # preferred: WEBZ_API_TOKEN in the environment
    # also valid: WebzNewsSearch(api_token="paste-token-here")
    token = os.getenv("WEBZ_API_TOKEN")
    tool = WebzNewsSearch(api_token=token) if token else WebzNewsSearch()

    print("tool name:", tool.name)
    print("live args from MCP tools/list:", sorted(tool.args))
    print("---")
    print(tool.invoke({"query": QUERY, "k": 3}), end="\n\n")
    print("SUCCESS ! End of tool")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
