# Apify integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) and [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain).
>
> **Suggested URL:** `/docs/webz/news-search-api-apify`
>
> **Suggested title:** Apify integration
>
> **Also add:** a link from the Framework SDKs index page.
>
> The listing is public: [webzio/news-search](https://apify.com/webzio/news-search). Users pay Apify. The Actor uses one shared Webz token. Event prices are on the Actor page: one `search` at $0.002, plus $0.001 per article.

---

# Apify integration

Use **Webz.io Contextual News Search** as an [Apify](https://apify.com) Actor. The Actor is [webzio/news-search](https://apify.com/webzio/news-search). It calls the [News Search API](https://docs.webz.io/docs/webz/news-search-api) (`POST /api/news/context`) once per run and writes one dataset row per article.

This is not a Python or npm package. You run it from Apify Console, from the Apify API, or as a tool on the [Apify MCP server](https://docs.apify.com/integrations/mcp).

You pay on Apify. You do not need a Webz API token. The search is the same News Search API as the REST product.

## What you pay

A successful run charges:

1. One `search` event, for the API call.
2. One `apify-default-dataset-item` event per article written to the dataset.

Prices are on the Actor page. An invalid query is not charged.

## Run in Apify Console

1. Open [webzio/news-search](https://apify.com/webzio/news-search) and sign in to Apify.
2. Enter a **Query**, for example `recent developments on EU AI regulation`.
3. Optionally set **Number of articles** (1–50, default 10), **Published within days**, and any filters.
4. Click **Start**. Memory stays at 256 MB.
5. Open the **Output** tab. Each row is one article: `score`, `title`, `url`, `published_at`, `text`, and source metadata such as `domain`, `language`, `country`, `sentiment`, and `ticker`.
6. Open **Storage → Key-value store** and the `OUTPUT` record for `query` and `total_results`.

Pass **Published within days** or **Published from**, not both. Coverage is the last 30 days.

## Run from code

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("webzio/news-search").call(run_input={
    "query": "recent developments on EU AI regulation",
    "k": 10,
    "days": 7,
    "language": ["english"],
})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["score"], item["title"], item["url"])
```

```bash
pip install apify-client
```

Actor page: [apify.com/webzio/news-search](https://apify.com/webzio/news-search)

## Use it as an agent tool

Apify's MCP server exposes the Actor. Point an MCP client at:

```text
https://mcp.apify.com?tools=webzio/news-search
```

The Actor uses Apify's default limited permissions, so it stays visible to that MCP server.

## Filters

List filters take arrays of strings. Scalar filters take one value. Leave a field empty to skip it.

| Field | What it filters |
| --- | --- |
| `language` | Article language, for example `english` |
| `country` | Source country, ISO-2, for example `US` |
| `category` | Article category |
| `sentiment` | `positive`, `negative`, or `neutral` |
| `domain` | Only these publisher domains |
| `exclude_domain` | Skip these publisher domains |
| `topic` | Topic tags |
| `person` | People mentioned |
| `organization` | Organizations mentioned |
| `location` | Locations mentioned |
| `ticker` | Stock tickers, for example `NVDA` |
| `political_bias` | `left`, `center`, or `right` |
| `trust_category` | `trusted_news`, `fake_news`, or `satirical_news` |
| `source_type` | `local_news`, `newsroom`, or `gov_news` |
| `published_from` / `published_to` | Publish dates, `YYYY-MM-DD` |
| `domain_rank_gte` / `domain_rank_lte` | Tranco domain rank (1 is the most popular) |
| `score_gte` / `score_lte` | Match score, 0–10. The API default floor is 4. |
| `allow_multiple_chunks_per_article` | More than one excerpt from the same article |

Full filter reference: [News Search filters](https://docs.webz.io/docs/webz/news-search-api-filters).

## Troubleshooting

- **Query error:** the query is empty, longer than 750 characters, or longer than 100 words. `k` must be from 1 to 50.
- **Spending limit:** the run stops before the search when the Apify spending cap is below one `search` event.
- **days and published_from:** set one of them, not both.
- **No `ticker` column:** the API omits metadata that does not apply to that article. The field is still in the dataset schema.

## Support

- Website: https://webz.io
- News Search API: https://docs.webz.io/docs/webz/news-search-api
- Actor page: https://apify.com/webzio/news-search
- Issues: https://github.com/Webhose/webz-news-search/issues
- Email: support@webz.io
