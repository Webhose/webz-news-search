# Dify integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) and [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain).
>
> **Suggested URL:** `/docs/webz/news-search-api-dify`
>
> **Suggested title:** Dify integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server (Dify is an MCP client).

---

# Dify integration

Use **Webz.io Contextual News Search** inside [Dify](https://dify.ai/) agents and workflows.

This is not a PyPI package. Dify Marketplace lists plugins as `.difypkg` files. After review, **Webz News Search** appears at [marketplace.dify.ai](https://marketplace.dify.ai/). The plugin is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp).

Dify v1.6+ can also attach that MCP server directly, without installing a plugin.

| Approach | Best for |
| --- | --- |
| **Webz News Search** Marketplace plugin | One-click install, Authorize with a token, Search tools in Agents and Workflows |
| Built-in **MCP** connector | Dify v1.6+ workspaces that already add remote MCP servers by URL |

Both use the same token, the same MCP server, and the same search logic.

## Prerequisites

- A Dify Cloud or self-hosted workspace that can install Marketplace plugins
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))

Get your token from the [Webz.io dashboard](https://webz.io).

## Install from Marketplace

1. Open [marketplace.dify.ai](https://marketplace.dify.ai/) and search for **Webz News Search**.
2. Install the plugin into your workspace.
3. In Dify, open **Tools → Webz News Search → Authorize** and paste the token.
4. Add **Webz News Search** to an Agent, or add a Tool node in a Workflow / Chatflow.

Authorize calls MCP `initialize` only. Saving the token does not consume search credits. Each tool run uses your News Search API credits and rate limits.

Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/dify`)

## Native MCP (no plugin)

In Dify v1.6 or later:

1. Open **Tools → MCP → Add MCP Server**.
2. Server URL: `https://news-search-mcp.webz.io/mcp`
3. Add a custom header: `Authorization: Bearer <WEBZ_API_TOKEN>`
4. Save. Dify imports `news_search_by_webz` from `tools/list`.

Only HTTP MCP is supported. stdio servers cannot be pasted into this screen.

## What the tool returns

Ranked article excerpts with titles, URLs, published dates, scores, and metadata (sentiment, topic, person, organization, location, ticker, and more). Ask the agent to summarize with sources.

Example prompts:

- Search Webz news for renewable energy investments from the past 30 days and summarize with sources.
- Call news_search_by_webz for Nvidia supply-chain risks with k=5 and days=30.

## Filters

The plugin exposes the main `news_search_by_webz` filters as tool fields. Comma-separated values become lists (`US, GB` → `["US", "GB"]`). Use **Additional filters JSON** for MCP fields that are not listed on the form.

Full filter reference: [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).

## Troubleshooting

- **Authorize fails** — the token is missing or rejected. Use the News Search API token from the Webz.io dashboard.
- **Empty or timeout results** — raise the MCP timeouts in native MCP settings, or retry with a smaller `k`.
- **Plugin not on Marketplace yet** — use native MCP above, or install a local `.difypkg` from Plugins → Install via local file while the listing PR is in review.

## Support

- MCP docs: https://docs.webz.io/docs/webz/news-search-api-mcp
- Issues: https://github.com/Webhose/webz-news-search/issues
- Email: support@webz.io
