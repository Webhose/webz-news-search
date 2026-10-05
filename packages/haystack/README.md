# webz-haystack

Search global news from [Haystack](https://haystack.deepset.ai/) with [Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api).

`WebzWebSearch` is a Haystack component. It returns one `Document` per article: the matching excerpt is `content`, and the title, URL, publish time, source, and entities are in `meta`. Coverage is the last 30 days.

## Install

```bash
pip install webz-haystack
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io). It is the same token as the News Search API.

## Pipeline

```python
from haystack import Pipeline
from haystack_integrations.components.websearch.webz import WebzWebSearch

pipeline = Pipeline()
pipeline.add_component(
    "news",
    WebzWebSearch(top_k=5, days=7, language=["english"], country=["US"]),
)
result = pipeline.run({"news": {"query": "recent developments on EU AI regulation"}})

for document in result["news"]["documents"]:
    print(document.meta["title"])
    print(document.meta["url"])
    print(document.content)
```

`WebzWebSearch()` reads `WEBZ_API_TOKEN`. To pass the token in code, use a Haystack `Secret`:

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.webz import WebzWebSearch

news = WebzWebSearch(api_key=Secret.from_token("your-webz-api-token"), top_k=5)
result = news.run(query="renewable energy investments", domain=["reuters.com"])
```

The same inputs are available on `run()` and override the values from `__init__`.

## Filters

| Input | Sent as |
| --- | --- |
| `top_k` | `k` |
| `language` | `filters.language` |
| `country` | `filters.country` |
| `domain` | `filters.domain` |
| `days` | `filters.published_from` (`YYYY-MM-DD`, UTC, today minus N days) |
| `score_gte`, `score_lte` | top-level score bounds, 0-10 |

The API has no `days` field. A bare string is accepted for the list filters: `language="english"` becomes `["english"]`.

## Token and endpoint

The component calls `POST https://api.webz.io/api/news/context` and sends the token as a bearer header. `api_url` or `WEBZ_NEWS_SEARCH_URL` can replace that endpoint. A URL that is not HTTPS is rejected before the token is sent.

## Coverage

The News Search index is the last 30 days. Leave `days` unset to search that whole window, or set `days` to narrow it. See the [News Search API](https://docs.webz.io/docs/webz/news-search-api).
