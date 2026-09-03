# LlamaIndex integration

Use **Webz.io Contextual News Search** inside [LlamaIndex](https://www.llamaindex.ai/) agents with the official Python package [`llama-index-tools-webz`](https://pypi.org/project/llama-index-tools-webz/).

The package is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). It uses [`llama-index-tools-mcp`](https://pypi.org/project/llama-index-tools-mcp/) under the hood. Tool names and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Unlike LangChain, LlamaIndex does not maintain a central partner listing page for external PyPI packages today. Discoverability is via PyPI, this docs page, and the package import path `llama_index.tools.webz`.

## Prerequisites

- Python 3.10+
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- LlamaIndex installed in your project (`llama-index-core` and agent dependencies)

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install llama-index-tools-webz
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [pypi.org/project/llama-index-tools-webz](https://pypi.org/project/llama-index-tools-webz)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/llamaindex`)

For agent examples with OpenRouter or OpenAI-compatible models, also install:

```bash
pip install llama-index-llms-openai-like
```

## Quick start: direct search

No LLM required. Call the news search tool directly:

```python
from llama_index.tools.webz import WebzNewsSearch, flatten_tool_result

tool = WebzNewsSearch()  # reads WEBZ_API_TOKEN from the environment

result = tool.call(
    query="recent developments on EU AI regulation",
    k=10,
    days=30,
)
print(flatten_tool_result(result))
```

You can also pass the token explicitly:

```python
tool = WebzNewsSearch(api_token="your-webz-api-token")
```

Each call uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Filtered search

Use the same filters as the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference). Examples:

```python
from llama_index.tools.webz import WebzNewsSearch, flatten_tool_result

tool = WebzNewsSearch()

result = tool.call(
    query="trade agreements between USA and Germany",
    k=10,
    days=7,
    language=["english"],
    country=["US", "GR"],
)
print(flatten_tool_result(result))
```

To list every filter your connection supports (loaded live from MCP):

```python
print(sorted(WebzNewsSearch().metadata.fn_schema.model_fields))
```

## Use with a LlamaIndex agent

Pass Webz tools into a `FunctionAgent`. Any tool-calling LLM works (OpenAI, Claude, Llama via OpenRouter, and others).

```python
import asyncio

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai_like import OpenAILike
from llama_index.tools.webz import get_webz_tools

tools = get_webz_tools()
llm = OpenAILike(
    model="meta-llama/llama-3.3-70b-instruct",
    api_key="your-openrouter-key",
    api_base="https://openrouter.ai/api/v1",
    is_chat_model=True,
    is_function_calling_model=True,
)
agent = FunctionAgent(
    tools=tools,
    llm=llm,
    system_prompt="You are a helpful assistant that searches global news with Webz.",
)

async def main() -> None:
    response = await agent.run(
        "Search Webz news for renewable energy investments "
        "from the past 30 days and summarize with sources."
    )
    print(str(response))

asyncio.run(main())
```

**Important:** `FunctionAgent.run()` is async. Call it inside `asyncio.run()` or another running event loop. Do not wrap `asyncio.run(agent.run(...))` before the loop exists.

### Example prompts for agents

- "Call news_search_by_webz for recent Nvidia supply-chain risks with k=5, then summarize with article titles and URLs."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Search Webz for EU AI regulation news from the past 30 days and list the top sources."

## Async usage

If your app already runs inside an asyncio event loop:

```python
from llama_index.tools.webz import aget_webz_tools, awebz_news_search

tools = await aget_webz_tools()
tool = await awebz_news_search()
```

Do not call the sync helpers (`get_webz_tools`, `WebzNewsSearch`) from inside a running event loop.

## How it works

```
Your Python app
    ↓
llama-index-tools-webz (PyPI)
    ↓
llama-index-tools-mcp
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Import path:** `from llama_index.tools.webz import ...` (namespace package on PyPI, not in the LlamaIndex monorepo)
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

## MCP vs LlamaIndex package

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **llama-index-tools-webz** | Python apps and agents built with LlamaIndex |

Both use the same token, the same MCP server, and the same search logic. Pick the integration that matches your framework.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `api_token=` to the helper.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**`TaskGroup` / event loop errors**  
Use async helpers inside a running loop, or let `WebzNewsSearch()` open a fresh MCP client per call (handled by the package).

**Agent returns empty or wrong answers**  
Ensure the LLM supports tool calling. Use a model with function-calling support (for example via OpenRouter).

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [LlamaIndex MCP tools guide](https://developers.llamaindex.ai/python/framework/module_guides/mcp/llamaindex_mcp/)
- [LlamaIndex agents and tools](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools/)
- [PyPI: llama-index-tools-webz](https://pypi.org/project/llama-index-tools-webz/)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)