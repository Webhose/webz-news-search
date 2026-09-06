# AG2 Webzio (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex).
>
> **Suggested URL:** `/docs/webz/ag2-webzio`
>
> **Suggested title:** AG2 Webzio
>
> **Also add:** link from the Framework SDKs index page and from MCP Server.

---

# AG2 Webzio

Use **Webz.io Contextual News Search** inside [AG2](https://ag2.ai/) agents with the official Python package [`ag2-webzio`](https://pypi.org/project/ag2-webzio/).

The package is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). It uses AG2's client-side [`MCPToolkit`](https://docs.ag2.ai/docs/user-guide/tools/mcp_servers/) under the hood. Tool names and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Pass `WebzioNewsSearchToolkit(...)` to `Agent(tools=[...])`. Call `toolkit.search()` to register only the news search tool.

## Prerequisites

- Python 3.10+
- AG2 v1 with MCP support (`ag2[mcp]>=1.0`, installed automatically with `ag2-webzio`)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- An LLM provider configured for AG2 (OpenAI, Anthropic, and others)

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install ag2-webzio
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [pypi.org/project/ag2-webzio](https://pypi.org/project/ag2-webzio)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/ag2`)

## Quick start: verify MCP connectivity

No LLM required. Construct the toolkit and list discovered tools:

```python
import asyncio

from ag2_webzio import WebzioNewsSearchToolkit

async def main() -> None:
    toolkit = WebzioNewsSearchToolkit()  # reads WEBZ_API_TOKEN
    schemas = await toolkit.schemas(context=None)
    print([schema.function.name for schema in schemas])

asyncio.run(main())
```

You can also pass the token explicitly:

```python
toolkit = WebzioNewsSearchToolkit(api_token="your-webz-api-token")
```

Each search call uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Tools

| Tool | Description |
| --- | --- |
| `news_search_by_webz` | Semantic news search with filters (language, country, days, sentiment, domain, ticker, and more) |

Filter schemas are loaded live from MCP `tools/list`, not hardcoded in the package.

## Use with an AG2 agent

Pass the toolkit into an AG2 agent. The model decides when to search and which filters to use:

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

### Register only news search

Call `search()` to register the news search tool:

```python
toolkit = WebzioNewsSearchToolkit(api_token="your-webz-api-token")

agent = Agent(
    "researcher",
    config=config,
    tools=[toolkit.search()],
)
```

Today the MCP server exposes a single tool, so `toolkit` and `toolkit.search()` are equivalent. When Webz adds more MCP tools, `search()` remains the news-only entry point.

### Example prompts for agents

- "Search Webz news for recent Nvidia supply-chain risk coverage and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Use the Webz news tool to compare EU and US AI regulation news from the past month."

## Filtered search

The agent reads filter names from the live MCP schema. You can steer it in the prompt using the same filters as the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference). Examples:

```
Search Webz news for analyst reaction to Nvidia earnings.
Use ticker NVDA, the last 7 days, English only, and limit to 5 results.
Give me the headline, publisher, and URL for each.
```

Common filters:

| Filter | Notes |
| --- | --- |
| `query` | Natural language. Required. |
| `k` | 1–100, default 10 |
| `days` | Lookback window. Omit for the last 7 days, or use `allow_all_dates` for full coverage. |
| `language` | Full names: `english`, `french`, `arabic`, `hebrew` |
| `country` | ISO-2 uppercase: `US`, `IL`, `GB`, `DE` |
| `sentiment` | `positive`, `negative`, `neutral` |
| `category` | IPTC categories such as `Politics` or `Science and Technology` |
| `domain` / `exclude_domain` | Restrict to or exclude source domains |
| `topic`, `person`, `organization`, `location` | Entity enrichment |
| `ticker` | Uppercase symbols: `NVDA`, `AAPL` |
| `sort_by` | `best_score` (default), `similarity`, `date_desc`, `date_asc` |

## How it works

```
Your Python app
    ↓
ag2-webzio (PyPI)
    ↓
AG2 MCPToolkit (client-side MCP)
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded at runtime from the MCP server, not hardcoded in the package
- **Auth:** Bearer token via `MCPServerConfig.authorization_token`
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint |

You can also pass `api_token=` and `mcp_url=` to `WebzioNewsSearchToolkit()`.

## MCP vs AG2 Webzio

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **ag2-webzio** | Python apps and agents built with AG2 |
| Raw AG2 `MCPToolkit` | When you want the generic MCP client without the Webzio toolkit |

Both use the same token, the same MCP server, and the same search logic. Pick the integration that matches your framework.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `api_token=` to the toolkit.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**Agent answers without searching**  
The LLM skipped the tool. Use a model with reliable tool calling and mention `news_search_by_webz` explicitly in the system prompt.

**Validation error on `topic`**  
`topic` expects a list of topic tags, not the search subject. Put the subject in `query`.

## AG2 Extensions listing (future)

After `ag2-webzio` is stable on PyPI, Webz.io will contribute `WebzioNewsSearchToolkit` to [ag2ai/ag2](https://github.com/ag2ai/ag2) under `ag2.extensions.tools.search.webzio`, with a docs page at docs.ag2.ai. The `ag2-webzio` package remains the Webz-owned distribution for users who prefer a standalone PyPI install.

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [AG2 MCP servers guide](https://docs.ag2.ai/docs/user-guide/tools/mcp_servers/)
- [PyPI: ag2-webzio](https://pypi.org/project/ag2-webzio/)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
