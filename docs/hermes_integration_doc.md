# Hermes Agent integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) and the Mastra integration.
>
> **Suggested URL:** `/docs/webz/news-search-api-hermes`
>
> **Suggested title:** Hermes Agent integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server. The catalog install command below works once `webz-news-search` is listed in the Hermes plugin catalog; until then, use the install from GitHub.

---

# Hermes Agent integration

Use **Webz.io Contextual News Search** inside [Hermes Agent](https://github.com/NousResearch/hermes-agent) with the `webz-news-search` plugin.

The plugin is a portable Hermes package with no code. It points Hermes's built-in MCP client at the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp) and bundles a skill that tells the agent when to search and how to cite results. The tool's filters come live from `tools/list` on the server, so new Webz filters appear without updating the plugin.

## Prerequisites

- Hermes Agent 0.21.6 or newer
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

From the Hermes plugin catalog:

```bash
hermes plugins install webz-news-search
hermes plugins enable webz-news-search
```

From GitHub:

```bash
git clone --depth 1 https://github.com/Webhose/webz-news-search.git
cp -r webz-news-search/packages/hermes ~/.hermes/plugins/webz-news-search
hermes plugins enable webz-news-search
```

Add the token to the active Hermes profile's `.env` (for the default profile, `~/.hermes/.env`):

```bash
WEBZ_API_TOKEN=your-webz-api-token
```

Start a new Hermes session after enabling the plugin.

Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/hermes`)

## Use it

Ask Hermes a news question. The agent calls `mcp__webz__news_search_by_webz` and answers from the returned excerpts.

- "Find recent articles about Nvidia supply-chain risks and summarize them with sources."
- "What negative coverage has Boeing had in English-language news this week?"
- "Search Webz for EU AI regulation news from the past 30 days and list the top sources."

A typical tool call:

```json
{"query": "Nvidia supply chain risks", "k": 10, "days": 14, "language": ["english"], "ticker": ["NVDA"]}
```

Filters follow the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).

## How it works

```
Hermes Agent
    ↓
webz-news-search plugin (mcp.json + skill)
    ↓
Hermes MCP client (Streamable HTTP)
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `mcp__webz__news_search_by_webz` (Hermes prefixes MCP tools with `mcp__<server>__`)
- **Schema:** loaded at connect time from the MCP server, not stored in the plugin
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`, read from the active Hermes profile
- **Transport:** HTTPS. Hermes refuses plain-HTTP remote servers and drops the token on cross-origin redirects.
- **Credits:** same as News Search API and MCP

## Troubleshooting

**`${WEBZ_API_TOKEN} in url/headers is not set in this profile's .env`**  
Add `WEBZ_API_TOKEN` to the `.env` of the profile you are running.

**The agent does not see the tool**  
Run `hermes plugins list` and check that `webz-news-search` is enabled, then start a new session.

**Empty results**  
Coverage is roughly the last 30 days. Widen `days` or remove the narrowest filter.

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Hermes plugin catalog](https://hermes-agent.nousresearch.com/docs/plugins)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
