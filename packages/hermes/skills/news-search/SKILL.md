---
name: news-search
description: Search recent global news with Webz.io filters.
version: 0.1.0
author: Shaked Degani (ShakedDegani), Webz.io
license: MIT
compatibility: Requires the Webz.io MCP connection supplied by this Hermes plugin.
metadata:
  homepage: https://docs.webz.io/docs/webz/news-search-api-mcp
---

# Webz.io News Search Skill

Answer news and current-events questions with article excerpts from Webz.io's worldwide news index. The plugin connects Hermes to the hosted Webz.io MCP server; this skill explains when to call its tool and how to read the results. It does not fetch full pages or search the general web.

## When to Use

- The user asks what happened, what is new, or how a story developed in the last few weeks.
- The user wants coverage narrowed by language, country, sentiment, source domain, company, person, or stock ticker.
- You need dated, attributable sources for a claim about a recent event.

Use `web_search` instead for evergreen reference material, documentation, or anything that is not news.

## Prerequisites

- `WEBZ_API_TOKEN` set in the active Hermes profile (`hermes setup` or the profile `.env`). Get a token from the [Webz.io dashboard](https://webz.io).
- The `webz-news-search` plugin enabled: `hermes plugins enable webz-news-search`, then start a new session.

## How to Run

Call the MCP tool `mcp__webz__news_search_by_webz`. Its full input schema comes from the server at connect time, so read the parameters Hermes shows for the tool rather than assuming a fixed list. Only `query` is required.

## Quick Reference

| Need | Argument |
| --- | --- |
| Number of articles | `k` (1-100, default 10) |
| Lookback window | `days` (default 7); `allow_all_dates: true` for the whole index |
| Newest first | `sort_by: "date_desc"` |
| Language | `language: ["english"]` |
| Country (ISO-2, uppercase) | `country: ["US"]` |
| Sentiment | `sentiment: ["negative"]` |
| Company or ticker | `organization: ["Nvidia"]`, `ticker: ["NVDA"]` |
| Only or never these sources | `domain: ["reuters.com"]`, `exclude_domain: [...]` |

## Procedure

1. Rewrite the user's question as a natural-language `query`. Do not add boolean operators or keyword syntax.
2. Add filters only for constraints the user stated. Example, call `mcp__webz__news_search_by_webz` with:

```json
{"query": "Nvidia supply chain risks", "k": 10, "days": 14, "language": ["english"], "ticker": ["NVDA"]}
```

3. For "latest" or "today" questions, sort by date. Example, call `mcp__webz__news_search_by_webz` with:

```json
{"query": "EU AI Act enforcement updates", "days": 3, "sort_by": "date_desc"}
```

4. Answer from the returned excerpts. Cite each claim with the article title, source, publish date, and URL.
5. If results are thin, widen `days`, drop the narrowest filter, or rephrase the query once before reporting that nothing was found.

## Pitfalls

- Coverage is roughly the last 30 days. Older events return few or no results.
- An empty result usually means the filters are too narrow, not that the tool failed.
- `country` takes uppercase ISO-2 codes. `domain` and `exclude_domain` must not overlap.
- Every call is a regular News Search API request billed to the user's Webz.io token.
- A 401 or "Authentication required" error means `WEBZ_API_TOKEN` is missing or wrong in the active profile.

## Verification

Call `mcp__webz__news_search_by_webz` with:

```json
{"query": "artificial intelligence regulation", "k": 1}
```

One article with a title and URL means the connection and token work.
