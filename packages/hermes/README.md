# Webz.io News Search for Hermes Agent

**Search global news with [Webz.io](https://webz.io) from [Hermes Agent](https://github.com/NousResearch/hermes-agent), in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back article excerpts with titles, URLs, publish dates, and match scores.

This is a portable Hermes plugin. It connects Hermes's built-in MCP client to the hosted Webz.io News Search MCP server and bundles one skill that tells the agent when and how to search. It contains no Python code and has no dependencies.

## What you get

- **MCP tool `mcp__webz__news_search_by_webz`** - semantic news search. Its input schema comes from the server's `tools/list` when Hermes connects, so new Webz filters appear without updating the plugin.
- **Skill `news-search`** - when to use the tool, how to pick filters, and how to cite results.

## Install

From the Hermes plugin catalog:

```bash
hermes plugins install webz-news-search
hermes plugins enable webz-news-search
```

Or from this repository:

```bash
git clone --depth 1 https://github.com/Webhose/webz-news-search.git
cp -r webz-news-search/packages/hermes ~/.hermes/plugins/webz-news-search
hermes plugins enable webz-news-search
```

Then add your token to the active profile's `.env` (for the default profile, `~/.hermes/.env`):

```bash
WEBZ_API_TOKEN=your-webz-api-token
```

Get a token from your [Webz.io dashboard](https://webz.io). It is the same token as the News Search API. Start a new Hermes session after enabling the plugin.

## Try it

```text
Find recent articles about Nvidia supply-chain risks and summarize them with sources.
```

```text
What negative coverage has Boeing had in English-language news this week?
```

The agent calls `mcp__webz__news_search_by_webz`, for example with `{"query": "Nvidia supply chain risks", "days": 14, "ticker": ["NVDA"]}`, and answers from the returned excerpts.

## How it works

`mcp.json` declares one Streamable HTTP server named `webz` at `https://news-search-mcp.webz.io/mcp` with the header `Authorization: Bearer ${WEBZ_API_TOKEN}`. Hermes fills in the token from the active profile when it connects. If the token is unset, Hermes refuses to connect and names the missing variable instead of sending an empty header.

Hermes accepts only `https://` URLs for remote plugin servers (plain HTTP is allowed for loopback hosts only) and drops the `Authorization` header on any cross-origin redirect.

## Configuration

| Name | Required | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | Yes | Webz.io API token, read from the active Hermes profile |

To use a different endpoint, add an `mcp_servers.webz` entry in `config.yaml`. A `config.yaml` server with the same name replaces the plugin's entry.

## Disclosure

- **Network:** connects to `news-search-mcp.webz.io` over HTTPS and sends the search queries and filters the agent chooses, authenticated with your `WEBZ_API_TOKEN`.
- **Cost:** every search is a regular News Search API request billed to your Webz.io account, with the same credits and rate limits.
- **No local side effects:** no shell commands, no background processes, no files read or written outside Hermes's own plugin directory, no telemetry. The plugin does not store credentials; Hermes reads the token from your profile.

## Development

The tests load the package with Hermes's own plugin loader, validator, and MCP config code. Point the runner at a Hermes checkout:

```bash
python -m pip install -r requirements-dev.in
python scripts/test.py --hermes-source /path/to/hermes-agent
hermes plugins validate . --install-deps
```

Set `WEBZ_API_TOKEN` to also run the live check against the hosted server.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [Hermes plugin catalog](https://hermes-agent.nousresearch.com/docs/plugins)
- [GitHub](https://github.com/Webhose/webz-news-search)
