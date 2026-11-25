"""Command line entry for the MovieClaw agent skill."""

from __future__ import annotations

import argparse
import sys

from movieclaw_webz.provider import (
    DEFAULT_RESULTS,
    WebzNewsError,
    WebzNewsSearchProvider,
    format_hits,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="movieclaw-webz",
        description="Search global news from the last 30 days.",
    )
    parser.add_argument("query", help="Natural-language news query")
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_RESULTS,
        help="How many articles to return (1 to 8, default 5)",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="Optional hostname, for example reuters.com",
    )
    args = parser.parse_args(argv)
    try:
        provider = WebzNewsSearchProvider()
        hits = provider.search_sync(
            args.query,
            max_results=args.max_results,
            domain=args.domain,
        )
    except WebzNewsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(format_hits(args.query, hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
