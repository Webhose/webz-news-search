# Webz News Search

**Author:** ori-webz
**Type:** tool
**Website:** [webz.io](https://webz.io)
**Repository:** https://github.com/Webhose/webz-news-search

Search global news with [Webz.io](https://webz.io) from Dify agents and workflows. This plugin wraps the hosted News Search MCP server at `https://news-search-mcp.webz.io/mcp`.

Use it for research, monitoring, RAG, and due diligence. Ask in natural language. Results come back ranked, with titles, URLs, dates, excerpts, and metadata.

## Links

| | |
| --- | --- |
| Company | https://webz.io |
| Get an API token | https://webz.io (dashboard, same token as the News Search API) |
| MCP server docs | https://docs.webz.io/docs/webz/news-search-api-mcp |
| Framework SDKs (LangChain, LlamaIndex, n8n, Dify, and more) | https://docs.webz.io/docs/webz/news-search-api-framework-sdks |
| Filters | https://docs.webz.io/docs/webz/news-search-api-filters |
| Source code | https://github.com/Webhose/webz-news-search (`packages/dify`) |
| Issues | https://github.com/Webhose/webz-news-search/issues |
| Privacy | https://webz.io/privacy |
| Support | support@webz.io |

## What you get

- Natural-language search, for example `EU AI Act enforcement updates`
- Semantic ranking over Webz.io's global news index
- Filters for date, language, country, sentiment, category, domain, ticker, person, organization, location, and more
- The same token, credits, and rate limits as the News Search API

## Setup

1. Get a Webz.io API token from the [dashboard](https://webz.io). It is the same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart).
2. In Dify Marketplace, install **Webz News Search**.
3. Open **Tools → Webz News Search → Authorize** and paste the token.
4. Add the tool to an Agent or a Workflow Tool node.

Authorize calls MCP `initialize` only, so saving credentials does not consume search credits. Each search uses your News Search credits. Details: [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp).

## Example prompts

- Search Webz news for recent developments on EU AI regulation and summarize with sources.
- Call news_search_by_webz for renewable energy investments with k=10 and days=30.

## Native MCP (no plugin)

Dify v1.6+ can also add the hosted server directly:

1. **Tools → MCP → Add MCP Server**
2. URL: `https://news-search-mcp.webz.io/mcp`
3. Turn off Dynamic Client Registration
4. Header: `Authorization: Bearer <WEBZ_API_TOKEN>`
5. Server identifier: `webz-news-search` (lowercase, hyphens, no spaces)

Walkthrough: [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp). Other frameworks: [Framework SDKs](https://docs.webz.io/docs/webz/news-search-api-framework-sdks).

## Privacy

See [PRIVACY.md](./PRIVACY.md) and https://webz.io/privacy.

## Support

- Website: https://webz.io
- Docs hub: https://docs.webz.io/docs/webz/news-search-api-framework-sdks
- MCP and filters: https://docs.webz.io/docs/webz/news-search-api-mcp
- Email: support@webz.io
