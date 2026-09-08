# CrewAI Webzio (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex), and [AG2 Webzio](https://docs.webz.io/docs/webz/ag2-webzio).
>
> **Suggested URL:** `/docs/webz/crewai-webzio`
>
> **Suggested title:** CrewAI Webzio
>
> **Also add:** link from the Framework SDKs index page and from MCP Server.

---

# CrewAI Webzio

Use **Webz.io Contextual News Search** inside [CrewAI](https://crewai.com/) agents with the official Python package [`crewai-webzio`](https://pypi.org/project/crewai-webzio/).

The package is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). It uses CrewAI's [`MCPServerAdapter`](https://docs.crewai.com/en/mcp/overview) under the hood. Tool names and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Pass `WebzioNewsSearchTool(...)` to `Agent(tools=[...])`. Use it as a context manager (or call `stop()` when done) to shut down the MCP session.

## Prerequisites

- Python 3.10+
- CrewAI with MCP support (`crewai-tools[mcp]>=0.40`, installed automatically with `crewai-webzio`)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- An LLM provider configured for CrewAI (OpenAI, Anthropic, and others)

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install crewai-webzio
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [pypi.org/project/crewai-webzio](https://pypi.org/project/crewai-webzio)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/crewai`)

<!-- HIDDEN until crewAIInc/crewAI#7309 merges - WebzioNewsSearchTool is not in crewai-tools yet.
After `crewai-webzio` is contributed upstream, you can also use:

```bash
pip install 'crewai[tools]'
export WEBZ_API_TOKEN="your-webz-api-token"
```

```python
from crewai_tools import WebzioNewsSearchTool
```

Available in `crewai-tools` after the upstream PR merges (see `packages/crewai/upstream/` in this repo for the contribution bundle).
-->

## Quick start: verify MCP connectivity

No LLM required. Construct the tool and list live filter names:

```python
from crewai_webzio import WebzioNewsSearchTool

with WebzioNewsSearchTool() as tool:  # reads WEBZ_API_TOKEN
    print(tool.name)
    print(sorted(tool.arg_names))
```

You can also pass the token explicitly:

```python
with WebzioNewsSearchTool(api_token="your-webz-api-token") as tool:
    print(tool._run(query="EU AI regulation", k=3))
```

Each search call uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Tools

| Tool | Description |
| --- | --- |
| `news_search_by_webz` | Semantic news search with filters (language, country, days, sentiment, domain, ticker, and more) |

Filter schemas are loaded live from MCP `tools/list`, not hardcoded in the package.

## Use with a CrewAI agent

Pass the tool into a CrewAI agent. The model decides when to search and which filters to use:

```python
import os

from crewai import Agent, Crew, Task
from crewai_webzio import WebzioNewsSearchTool

with WebzioNewsSearchTool(api_token=os.environ["WEBZ_API_TOKEN"]) as news_tool:
    researcher = Agent(
        role="Research Analyst",
        goal="Find recent news on any topic",
        backstory="Expert researcher with access to Webz.io news search.",
        tools=[news_tool],
        verbose=True,
    )

    research_task = Task(
        description=(
            "Search Webz news for recent Nvidia supply-chain risk coverage "
            "and summarize with sources."
        ),
        expected_output="A summary with headline, publisher, and URL for each article.",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[research_task], verbose=True)
    print(crew.kickoff())
```

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
crewai-webzio (PyPI)
    ↓
CrewAI MCPServerAdapter
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded at runtime from the MCP server, not hardcoded in the package
- **Auth:** Bearer token via `Authorization: Bearer {WEBZ_API_TOKEN}`
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint |

You can also pass `api_token=` and `mcp_url=` to `WebzioNewsSearchTool()`.

## MCP vs crewai-webzio

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **crewai-webzio** | Python apps and agents built with CrewAI (standalone PyPI install) |
<!-- HIDDEN until crewAIInc/crewAI#7309 merges - WebzioNewsSearchTool is not in crewai-tools yet.
| **`WebzioNewsSearchTool` in crewai-tools** | CrewAI users who already install `crewai[tools]` (after upstream merge) |
-->
| CrewAI `Agent(mcps=[MCPServerHTTP(...)])` | Zero-install MCP DSL on the agent |

All paths use the same token, the same MCP server, and the same search logic. Pick the integration that matches your framework.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `api_token=` to the tool.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**Agent answers without searching**  
The LLM skipped the tool. Use a model with reliable tool calling and mention `news_search_by_webz` explicitly in the task description.

**Validation error on `topic`**  
`topic` expects a list of topic tags, not the search subject. Put the subject in `query`.

**Forgot to call `stop()`**  
Use `with WebzioNewsSearchTool() as tool:` so the MCP session shuts down when the crew finishes.

<!-- HIDDEN until crewAIInc/crewAI#7309 merges - no docs.crewai.com listing yet.
## CrewAI upstream listing (future)

Webz.io will contribute `WebzioNewsSearchTool` to [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) under `lib/crewai-tools`, with a docs page in the Search & Research suite. The `crewai-webzio` package remains the Webz-owned distribution for users who prefer a standalone PyPI install.

Contribution bundle: `packages/crewai/upstream/` in this repo.
-->

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [CrewAI MCP overview](https://docs.crewai.com/en/mcp/overview)
- [CrewAI Exa Search Tool](https://docs.crewai.com/en/tools/search-research/exasearchtool) (reference pattern)
- [PyPI: crewai-webzio](https://pypi.org/project/crewai-webzio/)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
