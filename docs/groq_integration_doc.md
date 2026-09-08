# Groq integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex).
>
> **Suggested URL:** `/docs/webz/news-search-api-groq`
>
> **Suggested title:** Groq integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server.
>
> **Note:** unlike the other Framework SDK pages, this one documents no package. Groq connects to the hosted MCP server directly.

---

# Groq integration

Use **Webz.io Contextual News Search** with [Groq](https://groq.com)'s [Responses API](https://console.groq.com/docs/responses-api). Groq supports [remote MCP](https://console.groq.com/docs/tool-use/remote-mcp) natively, so you point it at the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp) and Groq handles the whole tool loop: `tools/list`, the model's tool call, `tools/call`, and the final answer.

There is nothing to install beyond an OpenAI-compatible client. Tool names and filter schemas come live from the server, so new Webz filters appear automatically.

## Prerequisites

- Python 3.8+ (or any OpenAI-compatible client — Node, curl, Go)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- A [Groq API key](https://console.groq.com/keys)

Get your Webz token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install openai
export WEBZ_API_TOKEN="your-webz-api-token"
export GROQ_API_KEY="your-groq-api-key"
```

Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/groq`)

## Quick start

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

Each search call uses your News Search API credits and rate limits, same as the MCP server or REST API.

### Tool fields

| Field | Purpose |
| --- | --- |
| `server_url` | The hosted MCP endpoint |
| `headers` | `Authorization: Bearer <WEBZ_API_TOKEN>`. Groq redacts these from its logs. |
| `server_description` | Helps the model choose news search over generic web search |
| `require_approval` | `"never"` runs tool calls without a human approval round trip |
| `allowed_tools` | Restricts the model to `news_search_by_webz` |

## Authentication

Pass the token in `headers`. Do not put it in the URL.

Some Groq MCP examples append the key as a query parameter (`?tavilyApiKey=`, `?exaApiKey=`). The Webz MCP server does not accept that, and putting tokens in URLs leaks them into logs and referrers. The pattern to copy is Groq's [HuggingFace integration](https://console.groq.com/docs/huggingface), which uses a Bearer header.

For interactive clients, the server also supports OAuth — see [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp).

## Tools

| Tool | Description |
| --- | --- |
| `news_search_by_webz` | Semantic news search with filters (language, country, days, sentiment, domain, ticker, and more) |

Filter schemas are loaded live from MCP `tools/list`, not hardcoded in your request.

## Filtered search

Groq gives the model the live schema, so you steer filters from the prompt using the same names as the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference):

```text
Find analyst reaction to Nvidia earnings.
Use news_search_by_webz with ticker NVDA, days 7, language english, k 5.
Give me the headline, publisher, and URL for each.
```

Common filters:

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

### Example prompts

- "Search Webz news for recent Nvidia supply-chain risk coverage and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Compare EU and US AI regulation news from the past month, five articles per region."

## Inspecting tool calls

Groq returns its tool activity in the response `output` array. Read it to confirm the model actually searched and to see which filters it chose:

```python
for item in response.output:
    if item.type == "mcp_list_tools":
        print("discovered:", [tool.name for tool in item.tools])
    if item.type == "mcp_call":
        print("called:", item.name, item.arguments)
        print("error:", item.error)
```

An empty `mcp_call` list means the model answered from memory. Name `news_search_by_webz` in the prompt and keep `temperature` low.

## Supported models

Remote MCP works on Groq models with tool use, including `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and `llama-3.3-70b-versatile`. See Groq's [supported models](https://console.groq.com/docs/tool-use/remote-mcp#supported-models). `openai/gpt-oss-120b` is the most reliable at calling the news tool.

## How it works

```
Your app
    ↓
Groq Responses API (https://api.groq.com/openai/v1)
    ↓ tools/list, then tools/call
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded by Groq at request time, not hardcoded in your app
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`
- **Credits:** same as News Search API and MCP

Groq's remote MCP support is compatible with OpenAI's remote MCP API, so the same tool definition works against [OpenAI](https://platform.openai.com/docs/guides/tools-remote-mcp) and [xAI](https://docs.x.ai/developers/tools/remote-mcp) by swapping the base URL, model, and key.

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `GROQ_API_KEY` | required | API key from the Groq console |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint |

## Groq vs the framework SDKs

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **Groq Responses API** | Apps that want Groq inference with no client-side tool loop |
| [LangChain](https://docs.webz.io/docs/webz/news-search-api-langchain), [LlamaIndex](https://docs.webz.io/docs/webz/news-search-api-llamaindex), [AG2](https://docs.webz.io/docs/webz/ag2-webzio), [CrewAI](https://docs.webz.io/docs/webz/crewai-webzio) | Agent frameworks that run MCP on your side |

All paths use the same token, the same MCP server, and the same search logic.

## Troubleshooting

**`424 Failed Dependency`**  
Groq reached the MCP server but authentication failed. Check `WEBZ_API_TOKEN` and that the token is in `headers`, not the URL.

**`401 Unauthorized` when testing the endpoint in a browser**  
Expected. Browsers do not send your token. Use an MCP client or Groq.

**Model answers without searching**  
It skipped the tool. Mention `news_search_by_webz` in the prompt, set `require_approval: "never"`, and prefer `openai/gpt-oss-120b`.

**Validation error on `topic`**  
`topic` expects a list of topic tags, not the search subject. Put the subject in `query`.

**Tool reported as unavailable**  
Drop `allowed_tools` from the tool definition. The server exposes one tool, so the restriction is optional.

<!-- HIDDEN until the groq-api-cookbook PR merges - there is no console.groq.com/docs/webz page yet.
## Groq integrations catalog (future)

Groq lists partner MCP servers on its [integrations page](https://console.groq.com/docs/integrations) next to Tavily, Exa, and Firecrawl, each backed by a tutorial in [groq/groq-api-cookbook](https://github.com/groq/groq-api-cookbook). Webz.io will submit an `mcp-webz` tutorial and request a catalog listing.

Contribution bundle: `packages/groq/cookbook/` in the [repo](https://github.com/Webhose/webz-news-search).
-->

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Groq remote MCP](https://console.groq.com/docs/tool-use/remote-mcp)
- [Groq Responses API](https://console.groq.com/docs/responses-api)
- [Vercel AI SDK integration](https://docs.webz.io/docs/webz/news-search-api-vercel-ai-sdk) (draft: [docs/ai_sdk_doc.md](ai_sdk_doc.md))
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
