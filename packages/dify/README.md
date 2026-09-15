# Webz News Search

**Author:** webhose
**Type:** tool
**Repository:** https://github.com/Webhose/webz-news-search

Search global news with [Webz.io](https://webz.io) from Dify agents and workflows. This plugin is a thin wrapper around the hosted News Search MCP server at `https://news-search-mcp.webz.io/mcp`.

## What you get

- Natural-language search, for example `EU AI Act enforcement updates`
- Semantic ranking over Webz.io's global news index
- Filters for date, language, country, sentiment, category, domain, ticker, person, organization, location, and more
- The same token, credits, and rate limits as the News Search API

## Setup

1. Get a Webz.io API token from [webz.io](https://webz.io) (same token as the News Search API).
2. In Dify Marketplace, install **Webz News Search**.
3. Open **Tools → Webz News Search → Authorize** and paste the token.
4. Add the tool to an Agent or a Workflow Tool node.

The authorize step calls MCP `initialize` only, so saving credentials does not consume search credits.

## Native MCP (no plugin)

Dify v1.6+ can also add the hosted server directly:

1. **Tools → MCP → Add MCP Server**
2. URL: `https://news-search-mcp.webz.io/mcp`
3. Custom header: `Authorization: Bearer <WEBZ_API_TOKEN>`

The Marketplace plugin is the one-click listing. Native MCP still works if you do not want to install a plugin.

## Privacy

See [PRIVACY.md](./PRIVACY.md). Webz.io privacy policy: https://webz.io/privacy.

## Support

- Docs: https://docs.webz.io/docs/webz/news-search-api-mcp
- Issues: https://github.com/Webhose/webz-news-search/issues
- Email: support@webz.io
