# langchain-webz

**Search global news with [Webz.io](https://webz.io) from Python - in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back focused article excerpts with titles, URLs, and metadata.

Use this package on its own, or plug it into LangChain / LangGraph agents.

## What you get

- **Natural-language search** - no keyword hacking. Example: `"EU AI Act enforcement updates"` or `"How is Tesla stock reacting to earnings?"`
- **Worldwide coverage** - semantic search over Webz.io's global news index.
- **Rich filters** - language, country, days, sentiment, domain, ticker, person, organization, topic, and more. See the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
- **Live schema** - filters are loaded from the hosted MCP server (`tools/list`). New Webz filters appear automatically, without republishing this package.

## Install

```bash
pip install langchain-webz
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io) (same token as the News Search API).

Full setup and client options: [MCP Server docs](https://docs.webz.io/docs/webz/news-search-api-mcp).

## Direct search (no agent required)

```python
from langchain_webz import WebzNewsSearch

tool = WebzNewsSearch()  # reads WEBZ_API_TOKEN from the environment
# tool = WebzNewsSearch(api_token="your-webz-api-token")

print(tool.invoke({
    "query": "recent developments on EU AI regulation",
    "k": 10,
    "days": 30,
}))
```

### Filtered search

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

To see every filter your connection supports:

```python
print(sorted(WebzNewsSearch().args))
```

## With a LangChain / LangGraph agent

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

Async helpers (when you already run inside an event loop):

```python
from langchain_webz import aget_webz_tools, awebz_news_search

tools = await aget_webz_tools()
tool = await awebz_news_search()
```

## How it works

This package connects to the hosted Webz News Search MCP server at `https://news-search-mcp.webz.io/mcp`. Each call runs a regular News Search API request with your token (same credits and rate limits). It does not hardcode filter fields - the tool schema comes from the live server.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for local MCP testing |

You can also pass `api_token=` and `mcp_url=` to the helpers.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [MCP server landing page](https://news-search-mcp.webz.io)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [GitHub](https://github.com/Webhose/webz-news-search)
