# Webz News Search on Groq

**Search global news with [Webz.io](https://webz.io) from [Groq](https://groq.com)'s Responses API — in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back focused article excerpts with titles, URLs, and metadata.

Groq supports [remote MCP](https://console.groq.com/docs/tool-use/remote-mcp) natively: you pass the hosted Webz MCP server in `tools`, and Groq runs `tools/list`, the model's tool calls, and `tools/call` on its side. **There is no package to install** — the code here is a reference implementation and a test harness.

## What you get

- **Natural-language search** — no keyword hacking. Example: `"EU AI Act enforcement updates"` or `"How is Tesla stock reacting to earnings?"`
- **Worldwide coverage** — semantic search over Webz.io's global news index.
- **Rich filters** — language, country, days, sentiment, domain, ticker, person, organization, topic, and more. See the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
- **Live schema** — Groq loads filters from the hosted MCP server (`tools/list`) at request time. New Webz filters appear automatically.
- **No tool loop to write** — Groq orchestrates discovery, execution, and synthesis server side.

## Quick start

```bash
pip install openai
export WEBZ_API_TOKEN="your-webz-api-token"   # https://webz.io dashboard
export GROQ_API_KEY="your-groq-api-key"       # https://console.groq.com/keys
```

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

tools = [{
    "type": "mcp",
    "server_label": "webzio-news-search",
    "server_url": "https://news-search-mcp.webz.io/mcp",
    "server_description": (
        "Webz.io contextual news search. Semantic search over a global news index, "
        "filtered by language, country, days, sentiment, ticker, domain, and entities."
    ),
    "headers": {"Authorization": f"Bearer {os.getenv('WEBZ_API_TOKEN')}"},
    "require_approval": "never",
    "allowed_tools": ["news_search_by_webz"],
}]

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input="Search Webz news for Nvidia supply-chain risk and summarize with sources.",
    tools=tools,
    temperature=0.1,
    top_p=0.4,
)

print(response.output_text)
```

Each search runs a regular News Search API request with your token — same credits and rate limits as the MCP server or REST API.

## Auth: header, not query string

Some Groq MCP integrations put the key in the URL (`?tavilyApiKey=`, `?exaApiKey=`). **Webz does not accept that.** Pass the token in `headers`, the way Groq's [HuggingFace integration](https://console.groq.com/docs/huggingface) does. Groq redacts those headers from its logs, and your token stays out of URLs and referrers.

## Filter-steered prompts

Groq gives the model the live schema, so the prompt can name filters directly:

```text
Find negative coverage about Boeing from the last 7 days.
Use news_search_by_webz with sentiment negative, days 7, language english, k 10.
Give headline, publisher, date, and URL for each.
```

| Filter | Notes |
| --- | --- |
| `query` | Natural language. Required. |
| `k` | 1–50, default 10 |
| `days` | Lookback window, default 7. Use `allow_all_dates` for full coverage. |
| `language` | Full names: `english`, `french`, `arabic`, `hebrew` |
| `country` | ISO-2 uppercase: `US`, `IL`, `GB`, `DE` |
| `sentiment` | `positive`, `negative`, `neutral` |
| `category` | IPTC categories such as `Politics` or `Science and Technology` |
| `domain` / `exclude_domain` | Restrict to or exclude source domains |
| `topic`, `person`, `organization`, `location` | Entity enrichment |
| `ticker` | Uppercase symbols: `NVDA`, `AAPL` |
| `political_bias` | `left`, `center`, `right` |

## Run the examples

```bash
cd packages/groq
pip install openai
export WEBZ_API_TOKEN="your-webz-api-token"
export GROQ_API_KEY="your-groq-api-key"

python examples/run_news_search.py      # one call, prints discovered tools + tool calls
python examples/run_research_agent.py   # sentiment, ticker, and country filter demos
```

Both use the `webz_groq` helper in this directory:

| Helper | Purpose |
| --- | --- |
| `build_webz_mcp_tool()` | Build the remote MCP entry for the Groq `tools` list |
| `discovered_tool_names()` | Tool names Groq found on the server (`mcp_list_tools`) |
| `extract_mcp_calls()` | Flatten `mcp_call` items — confirms the model actually searched |
| `format_mcp_calls()` | Print tool calls, chosen filters, and output excerpts |

## Tests

```bash
cd packages/groq
../../venv/bin/python -m pytest
```

Unit tests run offline. The live tests skip unless the matching keys are set:

| Test | Needs | Checks |
| --- | --- | --- |
| `test_live_mcp_endpoint_accepts_the_bearer_header` | `WEBZ_API_TOKEN` | The exact auth Groq performs; a 401 here surfaces as a 424 from Groq |
| `test_live_mcp_endpoint_rejects_anonymous_access` | — | Endpoint is not open |
| `test_live_groq_runs_the_webz_tool_loop` | both keys | The model calls `news_search_by_webz` and the call succeeds |

## How it works

```
Your app
    ↓  client.responses.create(tools=[{"type": "mcp", ...}])
Groq Responses API
    ↓  tools/list, then tools/call
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded by Groq at request time, not hardcoded here
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>` in the tool's `headers`
- **Credits:** same as News Search API and MCP

Unlike `langchain-webz`, `ag2-webzio`, or `crewai-webzio`, nothing runs MCP on your side. That is why there is no package to publish.

The same tool definition works on any provider with OpenAI-compatible remote MCP — [OpenAI](https://platform.openai.com/docs/guides/tools-remote-mcp) and [xAI](https://docs.x.ai/developers/tools/remote-mcp) — by swapping the base URL, model, and key.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `GROQ_API_KEY` | required | Groq API key from the Groq console |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for local MCP testing |

You can also pass `api_token=` and `mcp_url=` to `build_webz_mcp_tool()`.

## Troubleshooting

**`424 Failed Dependency` from Groq** — MCP auth failed. Groq reached the server but the token was rejected. Run the live Bearer test above.

**Model answers without searching** — it skipped the tool. Name `news_search_by_webz` in the prompt and keep `temperature` low. `openai/gpt-oss-120b` is the most reliable of the [supported models](https://console.groq.com/docs/tool-use/remote-mcp#supported-models).

**`MCP url must be https`** — the token would be sent in cleartext. Fix `WEBZ_MCP_URL`.

**Tool reported as unavailable** — retry with `build_webz_mcp_tool(allowed_tools=[])`. The server exposes one tool, so the restriction is optional.

**Validation error on `topic`** — `topic` expects a list of topic tags, not the search subject. Put the subject in `query`.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [Groq remote MCP docs](https://console.groq.com/docs/tool-use/remote-mcp)
- [Groq Responses API](https://console.groq.com/docs/responses-api)
- [Cookbook contribution bundle](cookbook/)
- [GitHub](https://github.com/Webhose/webz-news-search)
