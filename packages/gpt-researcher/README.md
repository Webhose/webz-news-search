# gpt-researcher-webz

Search global news from [GPT Researcher](https://github.com/assafelovic/gpt-researcher) with [Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api).

The plugin registers under the `gpt_researcher.retrievers` entry point as `webz`. Set `RETRIEVER=webz` and GPT Researcher uses it like any built-in retriever. Install [GPT Researcher](https://github.com/assafelovic/gpt-researcher) separately; this package does not replace it.

Results are article links plus a short excerpt. GPT Researcher still fetches the page. Coverage is the last 30 days.

## Install

```bash
pip install gpt-researcher gpt-researcher-webz
export RETRIEVER=webz
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io). It is the same token as the News Search API.

`RETRIEVER` accepts a comma-separated list. `RETRIEVER=webz,duckduckgo` runs this plugin next to a built-in retriever. Built-in names win when they collide, and `webz` is not a built-in name.

## Example

```python
import asyncio

from gpt_researcher import GPTResearcher


async def main() -> None:
    researcher = GPTResearcher(
        query="recent developments on EU AI regulation",
        report_type="research_report",
        query_domains=["reuters.com", "bbc.com"],
    )
    await researcher.conduct_research()
    print(await researcher.write_report())


asyncio.run(main())
```

`query_domains` is sent as the News Search `filters.domain` list. The retriever contract passes the query and that domain list. Language, country, sentiment, ticker, and the rest of the [News Search filters](https://docs.webz.io/docs/webz/news-search-api) are available on the [`webzio-news-search`](https://pypi.org/project/webzio-news-search/) client.

Call the retriever directly when you want the raw hits:

```python
from gpt_researcher_webz import WebzSearch

hits = WebzSearch(
    "recent developments on EU AI regulation",
    query_domains=["reuters.com"],
).search(max_results=5)

for hit in hits:
    print(hit["href"])
    print(hit["body"])
```

Each hit is `{"href": url, "body": text}`. `body` starts with the headline, source domain, and publish time, then the matching excerpt.

## Token

`WEBZ_API_TOKEN` is required. When you construct `WebzSearch` yourself, `headers["webz_api_key"]` overrides the environment variable. GPT Researcher's search path passes the query and `query_domains` only, so a normal `RETRIEVER=webz` run reads the environment variable.

The plugin calls `POST https://api.webz.io/api/news/context` over HTTPS and sends the token as a bearer header. A URL that is not HTTPS is rejected before the token is sent. Set `WEBZ_NEWS_SEARCH_URL` only for an HTTPS replacement.

A missing token raises `WebzRetrieverError`. A failed request returns `[]`, so a run that also uses other providers continues.

## Coverage

The News Search index is the last 30 days. This retriever leaves the date filter unset and sends `max_results` as `k`. Date windows on the API use `filters.published_from` (`YYYY-MM-DD`). See the [News Search API](https://docs.webz.io/docs/webz/news-search-api).
