# LangChain integration

Use **Webz.io Contextual News Search** inside [LangChain](https://www.langchain.com/) and [LangGraph](https://www.langchain.com/langgraph) agents with the official Python package [`langchain-webz`](https://pypi.org/project/langchain-webz/).

The package is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). Tool names and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Webz is listed in the [LangChain Python tools catalog](https://docs.langchain.com/oss/python/integrations/tools/index#all-tools-and-toolkits) as **WebzNewsSearch**.

## Prerequisites

- Python 3.10+
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- LangChain installed in your project

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install langchain-webz
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [pypi.org/project/langchain-webz](https://pypi.org/project/langchain-webz)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/langchain`)

## Quick start: direct search

No LLM required. Call the news search tool directly:

```python
from langchain_webz import WebzNewsSearch

tool = WebzNewsSearch()  # reads WEBZ_API_TOKEN from the environment

print(tool.invoke({
    "query": "recent developments on EU AI regulation",
    "k": 10,
    "days": 30,
}))
```

You can also pass the token explicitly:

```python
tool = WebzNewsSearch(api_token="your-webz-api-token")
```

Each call uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Filtered search

Use the same filters as the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference). Examples:

```python
from langchain_webz import WebzNewsSearch

tool = WebzNewsSearch()

# language, country, and date window
print(tool.invoke({
    "query": "trade agreements between USA and Germany",
    "k": 10,
    "days": 7,
    "language": ["english"],
    "country": ["US", "GR"],
}))

# ticker and trusted publishers
print(tool.invoke({
    "query": "earnings guidance and analyst reactions",
    "ticker": ["NVDA"],
    "domain": ["yahoo.com", "cnn.com"],
    "k": 5,
}))
```

To list every filter your connection supports (loaded live from MCP):

```python
print(sorted(WebzNewsSearch().args))
```

## Use with a LangChain / LangGraph agent

Pass Webz tools into a LangChain agent. The model decides when to search and which filters to use:

```python
from langchain.agents import create_agent
from langchain_webz import get_webz_tools

tools = get_webz_tools()
agent = create_agent("openai:gpt-4.1-mini", tools)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": (
            "Search Webz news for renewable energy investments "
            "from the past 30 days and summarize with sources."
        ),
    }]
})
print(result["messages"][-1].content)
```

### Example prompts for agents

- "Search Webz news for recent Nvidia supply-chain risk coverage and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Use the Webz news tool to compare EU and US AI regulation news from the past month."

## Async usage

If your app already runs inside an asyncio event loop:

```python
from langchain_webz import aget_webz_tools, awebz_news_search

tools = await aget_webz_tools()
tool = await awebz_news_search()
```

Do not call the sync helpers (`get_webz_tools`, `WebzNewsSearch`) from inside a running event loop.

## How it works

```
Your Python app
    ↓
langchain-webz (PyPI)
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded at runtime from the MCP server, not hardcoded in the package
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint |

You can also pass `api_token=` and `mcp_url=` to `WebzNewsSearch()`, `get_webz_tools()`, and the async helpers.

## MCP vs LangChain package

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **langchain-webz** | Python apps and agents built with LangChain / LangGraph |

Both use the same token, the same MCP server, and the same search logic. Pick the integration that matches your framework.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `api_token=` to the helper.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**Sync helper inside event loop**  
Use `aget_webz_tools()` / `awebz_news_search()` instead.

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [LangChain tools listing (WebzNewsSearch)](https://docs.langchain.com/oss/python/integrations/tools/index#all-tools-and-toolkits)
- [PyPI: langchain-webz](https://pypi.org/project/langchain-webz/)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)