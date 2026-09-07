# crewai-webzio

**Search global news with [Webz.io](https://webz.io) from [CrewAI](https://crewai.com) agents — in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back focused article excerpts with titles, URLs, and metadata.

Use this package with CrewAI agents, or construct the tool directly to verify MCP connectivity.

## What you get

- **Natural-language search** — no keyword hacking. Example: `"EU AI Act enforcement updates"` or `"How is Tesla stock reacting to earnings?"`
- **Worldwide coverage** — semantic search over Webz.io's global news index.
- **Rich filters** — language, country, days, sentiment, domain, ticker, person, organization, topic, and more. See the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
- **Live schema** — filters are loaded from the hosted MCP server (`tools/list`). New Webz filters appear automatically, without republishing this package.
- **CrewAI tool** — pass `WebzioNewsSearchTool(...)` to `Agent(tools=[...])`.

## Install

```bash
pip install crewai-webzio
export WEBZ_API_TOKEN="your-webz-api-token"
```

For the agent example below, also configure an LLM provider (for example `OPENAI_API_KEY`).

Get a token from your [Webz.io dashboard](https://webz.io) (same token as the News Search API).

Requires CrewAI with MCP support (`crewai-tools[mcp]`, installed automatically).

Full setup and client options: [MCP Server docs](https://docs.webz.io/docs/webz/news-search-api-mcp).

## With a CrewAI agent

```python
import os

from crewai import Agent, Crew, Task
from crewai_webzio import WebzioNewsSearchTool

with WebzioNewsSearchTool(api_token=os.environ["WEBZ_API_TOKEN"]) as news_tool:
    researcher = Agent(
        role="Research Analyst",
        goal="Find recent news using news_search_by_webz",
        backstory=(
            "When calling news_search_by_webz, pass only the parameters explicitly "
            "listed in the task. Do not add min_similarity, trust_gte, language, "
            "country, or domain filters unless the task asks for them."
        ),
        tools=[news_tool],
        verbose=True,
    )

    research_task = Task(
        description=(
            "Call news_search_by_webz with exactly these arguments: "
            "query='recent developments on EU AI regulation', k=3, days=30. "
            "Do not add any other filters. Summarize headline, publisher, and URL."
        ),
        expected_output="A summary with headline, publisher, and URL for each article.",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[research_task], verbose=True)
    print(crew.kickoff())
```

Use the tool as a context manager (or call `stop()` when done) to shut down the MCP session.

## Direct search (no agent required)

```bash
python examples/run_news_search.py
```

The script loads `WEBZ_API_TOKEN` from a nearby `.env` file (repo root or `packages/crewai/.env`) when the variable is not already exported.

```python
from crewai_webzio import WebzioNewsSearchTool

with WebzioNewsSearchTool() as tool:
    print(sorted(tool.arg_names))  # live filters from MCP tools/list
    print(tool._run(
        query="recent developments on EU AI regulation",
        k=3,
        days=30,
    ))
```

## Using Webz via MCP (no package install)

CrewAI can connect to the hosted MCP server directly:

```python
from crewai import Agent
from crewai.mcp import MCPServerHTTP

agent = Agent(
    role="News Researcher",
    goal="Find and summarize current news",
    mcps=[
        MCPServerHTTP(
            url="https://news-search-mcp.webz.io/mcp",
            headers={"Authorization": "Bearer YOUR_WEBZ_API_TOKEN"},
        ),
    ],
)
```

## How it works

This package wraps CrewAI's [`MCPServerAdapter`](https://docs.crewai.com/en/mcp/overview) around the hosted Webz News Search MCP server at `https://news-search-mcp.webz.io/mcp`. Each tool call runs a regular News Search API request with your token (same credits and rate limits). Filter fields are not hardcoded — the tool schema comes from the live server.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for local MCP testing |

You can also pass `api_token=` and `mcp_url=` to `WebzioNewsSearchTool()`.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [MCP server landing page](https://news-search-mcp.webz.io)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [CrewAI MCP overview](https://docs.crewai.com/en/mcp/overview)
- [GitHub](https://github.com/Webhose/webz-news-search)
