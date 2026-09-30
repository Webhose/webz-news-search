"""
run a single News Search API call.

usage:
  export WEBZ_API_TOKEN="your-token"
  python examples/run_news_search.py

or pass the token in code with WebzNewsSearch(api_token="...").
"""

from __future__ import annotations

import sys

from webzio_news_search import WebzNewsSearch

QUERY = "How many goals does Cristiano have and how many left to 1000?"


def main() -> None:
    with WebzNewsSearch() as client:  # reads WEBZ_API_TOKEN
        response = client.search(QUERY, k=3, days=30)

    print(response.to_text())
    print("---")
    print("credits used:", response.credits_used, "| requests left:", response.requests_left)
    for result in response:
        print(f"{result.score:>4} {result.domain:<20} {result.title}")
    print("SUCCESS ! End of tool")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
