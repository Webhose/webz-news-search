"""
Run one search through the GPT Researcher retriever contract.

usage:
  export WEBZ_API_TOKEN="your-token"
  python examples/run_news_search.py
"""

from __future__ import annotations

import sys

from gpt_researcher_webz import WebzSearch

QUERY = "recent developments on EU AI regulation"


def main() -> None:
    retriever = WebzSearch(QUERY, query_domains=["reuters.com"])
    hits = retriever.search(max_results=3)
    if not hits:
        print("no results")
        return
    for hit in hits:
        print(hit["href"])
        print(hit["body"])
        print("---")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
