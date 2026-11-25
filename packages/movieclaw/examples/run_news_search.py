"""Call the provider directly. Set WEBZ_API_TOKEN before running."""

from __future__ import annotations

import asyncio

from movieclaw_webz import WebzNewsSearchProvider, format_hits


async def main() -> None:
    provider = WebzNewsSearchProvider()
    hits = await provider.search(
        "recent developments on EU AI regulation",
        max_results=5,
        domain="reuters.com",
    )
    print(format_hits("recent developments on EU AI regulation", hits))


if __name__ == "__main__":
    asyncio.run(main())
