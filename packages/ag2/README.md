# ag2-webzio

**Search global news with [Webz.io](https://webz.io) from [AG2](https://ag2.ai) agents — in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back focused article excerpts with titles, URLs, and metadata.

Use this package with AG2 agents, or construct the toolkit directly to verify MCP connectivity.

## What you get

- **Natural-language search** — no keyword hacking. Example: `"EU AI Act enforcement updates"` or `"How is Tesla stock reacting to earnings?"`
- **Worldwide coverage** — semantic search over Webz.io's global news index.
- **Rich filters** — language, country, days, sentiment, domain, ticker, person, organization, topic, and more. See the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
- **Live schema** — filters are loaded from the hosted MCP server (`tools/list`). New Webz filters appear automatically, without republishing this package.
- **AG2 toolkit** — pass `WebzioNewsSearchToolkit(...)` to `Agent(tools=[...])`, or use `toolkit.search()` to register only news search.

## Install

```bash
pip install ag2-webzio
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io) (same token as the News Search API).

Requires AG2 v1 with MCP support (`ag2[mcp]>=1.0`, installed automatically).

Full setup and client options: [MCP Server docs](https://docs.webz.io/docs/webz/news-search-api-mcp).

## With an AG2 agent

```python
import os
from ag2 import Agent
from ag2.config import AnthropicConfig
from ag2_webzio import WebzioNewsSearchToolkit

agent = Agent(
    "researcher",
    config=AnthropicConfig(model="claude-sonnet-4-6"),
    tools=[WebzioNewsSearchToolkit(api_token=os.environ["WEBZ_API_TOKEN"])],
)
```

The model discovers the live `news_search_by_webz` schema and picks filters itself. Example prompts:

- "Search Webz news for recent Nvidia supply-chain risk coverage and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Use the Webz news tool to compare EU and US AI regulation news from the past month."

### Register only news search

When the MCP server exposes more than one tool, register news search with `search()`:

```python
toolkit = WebzioNewsSearchToolkit(api_token="your-webz-api-token")
agent = Agent("researcher", config=config, tools=[toolkit.search()])
```

Today the server exposes a single tool, so `toolkit` and `toolkit.search()` are equivalent.

## Verify MCP connectivity (no LLM)

```bash
export WEBZ_API_TOKEN="your-token"
python examples/run_news_search.py
```

## How it works

This package wraps AG2's client-side [`MCPToolkit`](https://docs.ag2.ai/docs/user-guide/tools/mcp_servers/) around the hosted Webz News Search MCP server at `https://news-search-mcp.webz.io/mcp`. Each tool call runs a regular News Search API request with your token (same credits and rate limits). Filter fields are not hardcoded — the tool schema comes from the live server.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for local MCP testing |

You can also pass `api_token=` and `mcp_url=` to `WebzioNewsSearchToolkit()`.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [MCP server landing page](https://news-search-mcp.webz.io)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [AG2 MCP servers guide](https://docs.ag2.ai/docs/user-guide/tools/mcp_servers/)
- [GitHub](https://github.com/Webhose/webz-news-search)
