# webzio-news-search

**Search global news with [Webz.io](https://webz.io) from Python - in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api) covers news and current events from sources worldwide over the last 30 days. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back article titles, URLs, metadata, and the excerpt that matched.

This package calls the [News Search API](https://docs.webz.io/docs/webz/news-search-api) over HTTPS. It has one dependency (`httpx`) and no MCP or agent-framework requirement. Use it in scripts, services, notebooks, or as a function tool for any LLM that supports tool calling.

Looking for a framework wrapper instead? See [`langchain-webz`](../langchain), [`llama-index-tools-webz`](../llamaindex), [`ag2-webzio`](../ag2), [`crewai-webzio`](../crewai), or [`@webz.io/ai-sdk`](../ai-sdk). Those connect through the hosted [MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp).

## What you get

- **Natural-language search** - `"EU AI Act enforcement updates"`, `"How is Tesla stock reacting to earnings?"`
- **Typed results** - `NewsSearchResponse` → `NewsResult` → `article`, `chunk`, `metadata`, plus the raw JSON.
- **Every filter** - language, country, category, sentiment, dates, domain, exclude_domain, topic, person, organization, location, ticker, political_bias, trust_category, source_type, domain rank. Unknown filter names pass straight through, so new server-side filters work without a package update.
- **Sync and async** - `search()` and `asearch()` on the same client.
- **LLM tool calling** - `tool_definition()` gives you the JSON schema; `run_tool()` executes the model's arguments and returns prompt-ready text.

## Install

```bash
pip install webzio-news-search
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io). It is the same token as the News Search API and MCP server.

## Direct search

```python
from webzio_news_search import WebzNewsSearch

client = WebzNewsSearch()  # reads WEBZ_API_TOKEN from the environment
# client = WebzNewsSearch(api_token="your-webz-api-token")

response = client.search("recent developments on EU AI regulation", k=10, days=30)

print(response.total_results, "results |", response.credits_used, "credits used")
for result in response:
    print(result.score, result.title, result.url)
    print("  ", result.text)  # the matching excerpt
```

### Filtered search

```python
# language, country, and date window
client.search(
    "trade agreements between USA and Germany",
    k=10,
    days=7,
    language=["english"],
    country=["US", "DE"],
)

# ticker and trusted publishers
client.search(
    "earnings guidance and analyst reactions",
    ticker=["NVDA"],
    domain=["yahoo.com", "cnn.com"],
    score_gte=5,
    k=5,
)

# explicit dates and a filters dict, exactly as the API documents it
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

`days=N` is shorthand for `published_from = today - N days` (UTC). Pass one or the other, not both.

Bare strings are accepted for list filters: `language="english"` becomes `["english"]`.

### Async

```python
from webzio_news_search import WebzNewsSearch

async with WebzNewsSearch() as client:
    response = await client.asearch("renewable energy investments", k=5)
```

### One-shot helpers

```python
from webzio_news_search import news_search, anews_search

response = news_search("semiconductor export controls", k=3)
response = await anews_search("semiconductor export controls", k=3)
```

## Results

```python
response.query            # echoed query
response.total_results    # matches returned, up to k
response.requests_left    # remaining credit balance
response.credits_used     # credits charged for this call
response.raw              # full JSON payload

result = response.results[0]
result.score              # 0-10 match quality
result.article.title / url / published_at / summary / main_image / article_id
result.chunk.text         # most relevant excerpt
result.metadata           # language, country, category, sentiment, domain, site_type,
                          # topic, person, organization, location, ticker,
                          # political_bias, trust_category, source_type, domain_rank

response.to_text()        # prompt-friendly text block
response.to_dicts()       # flat rows for sheets / dataframes
```

To fetch the full article body, use `result.article.article_id` as a `uuid:` query on the [News API](https://docs.webz.io/docs/webz/news-search-api-response-format#get-the-full-article-text).

## As an LLM tool

The tool schema is framework-agnostic JSON. Example with the OpenAI chat completions API:

```python
import json
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
    tool_output = news.run_tool(call.function.arguments)  # JSON string or dict
    messages.append({"role": "tool", "tool_call_id": call.id, "content": tool_output})
```

`tool_definition()` returns `{"name", "description", "parameters"}` for providers that take a bare function schema (Anthropic, Groq, Gemini, and others). The tool name is `news_search_by_webz`, the same as the MCP server, so prompts written for one work with the other.

`run_tool()` accepts `query`, `k`, `days`, `score_gte`, `score_lte`, `allow_multiple_chunks_per_article`, and any filter name. It returns `response.to_text()`.

A full agent loop is in [`examples/openai_tool_calling.py`](examples/openai_tool_calling.py).

## Errors

| Exception | When |
| --- | --- |
| `WebzConfigError` | Missing token, empty or over-long query, bad `k`/score combination, `days` together with `published_from`, a domain in both `domain` and `exclude_domain` |
| `WebzAPIError` | Any HTTP error. `status_code` and `detail` are set; the message includes a hint for 400, 401, 402, 403, 422, 429, and 5xx. Transport failures raise with `status_code == 0`. |

Failed requests are not charged. See [Errors, Rate Limits & Credits](https://docs.webz.io/docs/webz/news-search-api-errors-limits).

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_NEWS_SEARCH_URL` | `https://api.webz.io/api/news/context` | Endpoint override for testing |

Constructor options: `api_token=`, `api_url=`, `timeout=` (seconds or `httpx.Timeout`), and `client=` / `async_client=` to reuse your own `httpx` clients.

## Development

```bash
cd packages/news-search
pip install -e '.[dev]'
pytest                       # unit tests, no network
WEBZ_API_TOKEN=... pytest    # also runs tests/test_live.py
```

## Links

- [Webz.io](https://webz.io)
- [News Search API documentation](https://docs.webz.io/docs/webz/news-search-api)
- [Request parameters](https://docs.webz.io/docs/webz/news-search-api-parameters)
- [Filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Response format](https://docs.webz.io/docs/webz/news-search-api-response-format)
- [PyPI: webzio-news-search](https://pypi.org/project/webzio-news-search/)
- [GitHub](https://github.com/Webhose/webz-news-search)
