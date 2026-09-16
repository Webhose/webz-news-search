# Dify integration

Use **Webz.io Contextual News Search** inside [Dify](https://dify.ai/) agents and workflows.

This is not a PyPI package. Dify installs a Marketplace plugin. **Webz News Search** is live at:

- Plugin page: [marketplace.dify.ai/plugin/ori-webz/webz_news_search](https://marketplace.dify.ai/plugin/ori-webz/webz_news_search)
- Catalog: [marketplace.dify.ai](https://marketplace.dify.ai/)

The plugin is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). Dify v1.6+ can also attach that MCP server by URL, without installing a plugin.

Prefer the Marketplace plugin. Use native MCP only if you already add remote MCP servers by URL.

| Approach | Best for |
| --- | --- |
| **Webz News Search** Marketplace plugin | Install from the catalog, Authorize with a token, then use the tool in Agents and Workflows |
| Built-in **MCP** connector | Dify v1.6+ workspaces that add remote MCP servers by URL |

Both use the same token, the same MCP server, and the same search logic.

This plugin runs inside Dify. There is no `pip` / `npm` client. To call it from your own code, publish a Dify Agent or Workflow and use the Dify app API. Outside Dify, use the [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp) or another [Framework SDK](https://docs.webz.io/docs/webz/news-search-api-framework-sdks).

## Prerequisites

- A Dify Cloud or self-hosted workspace that can install Marketplace plugins
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))

Get your token from the [Webz.io dashboard](https://webz.io).

## Install from Marketplace

1. Open the [Webz News Search plugin page](https://marketplace.dify.ai/plugin/ori-webz/webz_news_search) (or search [marketplace.dify.ai](https://marketplace.dify.ai/) for **Webz News Search**).
2. Click **Install** and choose your Dify workspace.
3. In Dify, open **Tools** (not the Built-in tools tab). Find **Webz News Search** and click **Authorize**.
4. Fill the form:
   - **Authorization Name:** optional (for example `Webz`).
   - **Webz API token:** paste the token only. Do not prefix `Bearer`.
   - **Who can use:** `All team members` unless you need a tighter scope.
5. Click **Save**.
6. Create an app: **Studio → Create from Blank → Agent**. In **Orchestrate**, add **Webz News Search** (`news_search_by_webz`). You can also add a Tool node in a Workflow or Chatflow.

Authorize calls MCP `initialize` only. Saving the token does not consume search credits. Each tool run uses your News Search API credits and rate limits.

Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/dify`)

## Native MCP (no plugin)

Use this only if you are not installing the Marketplace plugin. In Dify v1.6 or later:

1. Open **Tools → MCP → Add MCP Server**.
2. Server URL: `https://news-search-mcp.webz.io/mcp`
3. Turn **off** **Use Dynamic Client Registration**. The Webz server is not that OAuth flow. Leave Client ID and Client Secret empty.
4. **Server Identifier:** `webz-news-search` (lowercase, hyphens, no spaces). The display name can contain spaces.
5. Open **Headers**. Add `Authorization` with value `Bearer <WEBZ_API_TOKEN>` (the word `Bearer`, a space, then the token).
6. Click **Add & Authorize**. Dify imports `news_search_by_webz` from `tools/list`.

Only HTTP MCP is supported. stdio servers cannot be pasted into this screen.

## What the tool returns

Ranked article excerpts with titles, URLs, published dates, scores, and metadata (sentiment, topic, person, organization, location, ticker, and more). Ask the agent to summarize with sources.

Example prompts:

- Search Webz news for renewable energy investments from the past 30 days and summarize with sources.
- Call news_search_by_webz for Nvidia supply-chain risks with k=5 and days=30.

## Filters

The plugin exposes the main `news_search_by_webz` filters as tool fields. Comma-separated values become lists (`US, GB` becomes `["US", "GB"]`). Use **Additional filters JSON** for MCP fields that are not listed on the form.

Full filter reference: [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).

## Troubleshooting

- **Authorize fails:** the token is missing, has a `Bearer ` prefix in the plugin form, or is not the News Search API token from the [Webz.io dashboard](https://webz.io).
- **Invalid identifier (native MCP):** the Server Identifier must not contain spaces. Use `webz-news-search`.
- **The agent never calls the tool:** the tool is not added on the Agent Orchestrate screen, or you are in a Chatbot without tools.
- **You are on Built-in tools:** Marketplace plugins are not in that tab. Open Tools plugins / installed tools and look for **Webz News Search**.
- **Empty or timeout results:** retry with a smaller `k`. For native MCP, raise the MCP timeouts.

## Support

- Website: https://webz.io
- Plugin: https://marketplace.dify.ai/plugin/ori-webz/webz_news_search
- Marketplace: https://marketplace.dify.ai/
- Framework SDKs: https://docs.webz.io/docs/webz/news-search-api-framework-sdks
- MCP docs: https://docs.webz.io/docs/webz/news-search-api-mcp
- Issues: https://github.com/Webhose/webz-news-search/issues
- Email: support@webz.io
