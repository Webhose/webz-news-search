# Python client (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex).
>
> **Suggested URL:** `/docs/webz/news-search-api-python`
>
> **Suggested title:** Python client
>
> **Also add:** link from the Framework SDKs index page and from the News Search API quickstart.
>
> **Note:** this page documents the REST client, not the MCP server. It calls `POST /api/news/context` directly.

---

# Python client

Use **Webz.io Contextual News Search** from Python with [`webzio-news-search`](https://pypi.org/project/webzio-news-search/). It calls the [News Search API](https://docs.webz.io/docs/webz/news-search-api) over HTTPS and returns typed results: title, URL, publish date, match score, source metadata, and the excerpt that matched the query.

The package has one dependency (`httpx`). It does not use the [MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp) and it does not require LangChain, LlamaIndex, CrewAI, or any other agent framework. Use it in scripts, services, and notebooks, or hand its JSON tool schema to any LLM that supports function calling.

Framework wrappers that connect through MCP are documented separately: [LangChain](https://docs.webz.io/docs/webz/news-search-api-langchain), [LlamaIndex](https://docs.webz.io/docs/webz/news-search-api-llamaindex), [AG2](https://docs.webz.io/docs/webz/ag2-webzio), [CrewAI](https://docs.webz.io/docs/webz/crewai-webzio), [Vercel AI SDK](https://docs.webz.io/docs/webz/news-search-api-vercel-ai-sdk), [Groq](https://docs.webz.io/docs/webz/news-search-api-groq), [n8n](https://docs.webz.io/docs/webz/news-search-api-n8n), and [Dify](https://docs.webz.io/docs/webz/news-search-api-dify).

## Prerequisites

- Python 3.10+
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
pip install webzio-news-search
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [pypi.org/project/webzio-news-search](https://pypi.org/project/webzio-news-search/)
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/news-search`)

## Quick start

```python
from webzio_news_search import WebzNewsSearch

client = WebzNewsSearch()  # reads WEBZ_API_TOKEN
# client = WebzNewsSearch(api_token="your-webz-api-token")

response = client.search("recent developments on EU AI regulation", k=10, days=30)

print(response.total_results, "results |", response.credits_used, "credits used")
for result in response:
    print(result.score, result.title, result.url)
    print("  ", result.text)
```

Each call is a regular News Search request. The same credits and rate limits apply. See [Errors, Rate Limits & Credits](https://docs.webz.io/docs/webz/news-search-api-errors-limits).

Coverage is the last 30 days. `days=N` is shorthand for `published_from` set to today minus N days (UTC). Pass `days` or `published_from`, not both.

## Filters

Keyword arguments and a `filters` dict both work. A bare string for a list filter is wrapped in a list, so `language="english"` becomes `["english"]`.

```python
client.search(
    "trade agreements between USA and Germany",
    k=10,
    days=7,
    language=["english"],
    country=["US", "DE"],
)

client.search(
    "earnings guidance and analyst reactions",
    ticker=["NVDA"],
    domain=["yahoo.com", "cnn.com"],
    score_gte=5,
    k=5,
)

client.search(
    "central bank interest rate decision",
    filters={
        "published_from": "2026-07-01",
        "published_to": "2026-07-31",
        "sentiment": ["negative"],
        "political_bias": ["center"],
    },
)
```

| Argument | Sent as | Description |
| --- | --- | --- |
| `query` | body | Natural-language topic or question. Required. Max 750 characters and 100 words |
| `k` | body | Articles to return. Server default 10 |
| `score_gte`, `score_lte` | body | Match-score bounds, 0–10. Server default floor is 4; pass `score_gte=0` to disable it |
| `allow_multiple_chunks_per_article` | body | Return more than one matching passage from the same article |
| `days` | `filters.published_from` | Client-side shorthand. Not an API field |
| `language`, `country`, `category`, `sentiment` | `filters` | Same values as [Filters](https://docs.webz.io/docs/webz/news-search-api-filters). Country codes are ISO-2 (`US`, `GB`) |
| `published_from`, `published_to` | `filters` | Date window, `YYYY-MM-DD` |
| `domain`, `exclude_domain` | `filters` | Keep or skip source domains. A domain cannot be in both lists |
| `topic`, `person`, `organization`, `location`, `ticker` | `filters` | Entity and topic tags |
| `political_bias` | `filters` | `left`, `center`, or `right` |
| `trust_category` | `filters` | `trusted_news`, `fake_news`, or `satirical_news` |
| `source_type` | `filters` | `local_news`, `newsroom`, or `gov_news` |
| `domain_rank_gte`, `domain_rank_lte` | `filters` | Tranco domain rank range (lower means more popular) |

Filter names the package does not know about are forwarded as-is, so a new server-side filter works without a new release.

## Results

```python
response.query            # echoed query
response.total_results    # matches returned, up to k
response.requests_left    # remaining credit balance
response.credits_used     # credits charged for this call
response.raw              # full JSON payload

result = response.results[0]
result.score              # match quality, 0–10
result.article            # article_id, url, title, published_at, summary, main_image
result.chunk.text         # the most relevant excerpt
result.metadata           # language, country, category, sentiment, domain, site_type,
                          # topic, person, organization, location, ticker,
                          # political_bias, trust_category, source_type, domain_rank

print(response.to_text())   # prompt-friendly text
rows = response.to_dicts()  # one flat dict per result
```

To fetch the full article body, use `result.article.article_id` as a `uuid:` query on the News API. See [Response format](https://docs.webz.io/docs/webz/news-search-api-response-format#get-the-full-article-text).

## Async

```python
from webzio_news_search import WebzNewsSearch

async with WebzNewsSearch() as client:
    response = await client.asearch("renewable energy investments", k=5)
```

One-shot helpers open a client, run the search, and close it:

```python
from webzio_news_search import news_search, anews_search

response = news_search("semiconductor export controls", k=3)
response = await anews_search("semiconductor export controls", k=3)
```

## Use it as an LLM tool

`tool_definition()` returns a JSON schema named `news_search_by_webz` — the same name as the MCP tool, so a prompt written for one works with the other. `openai_tool_definition()` wraps that schema in the OpenAI chat-completions envelope. `run_tool()` executes the model's arguments and returns `response.to_text()`.

```python
from openai import OpenAI
from webzio_news_search import WebzNewsSearch

openai_client = OpenAI()
news = WebzNewsSearch()

messages = [{"role": "user", "content": "What happened with Nvidia this week? Cite sources."}]
completion = openai_client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages,
    tools=[WebzNewsSearch.openai_tool_definition()],
)

for call in completion.choices[0].message.tool_calls or []:
    messages.append({
        "role": "tool",
        "tool_call_id": call.id,
        "content": news.run_tool(call.function.arguments),
    })
```

`run_tool()` accepts a dict or the JSON string the model returns. Inside an event loop, use `await news.arun_tool(...)`.

## Errors

| Exception | When |
| --- | --- |
| `WebzConfigError` | Missing token, empty or over-long query, `k` below 1, `score_gte` above `score_lte`, `days` together with `published_from`, a domain listed in both `domain` and `exclude_domain` |
| `WebzAPIError` | The API returned an HTTP error, or the host could not be reached. `status_code` and `detail` are set. The message includes a short hint for 400, 401, 402, 403, 422, 429, and 5xx. A network failure uses `status_code` 0 |

Failed requests are not charged.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_NEWS_SEARCH_URL` | `https://api.webz.io/api/news/context` | Endpoint override for testing |

You can also pass `api_token=` and `api_url=` to `WebzNewsSearch()`. `timeout=` takes seconds or an `httpx.Timeout`. Pass `client=` or `async_client=` to reuse your own `httpx` clients.

## REST client vs MCP

| Approach | Best for |
| --- | --- |
| **webzio-news-search** | Python code that should call the News Search API directly, with typed results and no MCP client |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude, ChatGPT, and any client that speaks MCP |
| Framework packages | LangChain, LlamaIndex, AG2, CrewAI, the Vercel AI SDK, n8n, Dify |

All of them use the same token and the same search. Pick the client that matches the runtime.

## Related links

- [News Search API](https://docs.webz.io/docs/webz/news-search-api)
- [News Search API quickstart](https://docs.webz.io/docs/webz/news-search-api-quickstart)
- [Request parameters](https://docs.webz.io/docs/webz/news-search-api-parameters)
- [Filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Response format](https://docs.webz.io/docs/webz/news-search-api-response-format)
- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [PyPI: webzio-news-search](https://pypi.org/project/webzio-news-search/)
- [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain) (draft: [docs/langchain_integration_doc.md](langchain_integration_doc.md))
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
