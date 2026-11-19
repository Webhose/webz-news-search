# FreeLLMAPI integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, next to the other search integrations.
>
> **Suggested URL:** `/docs/webz/news-search-api-freellmapi`
>
> **Suggested title:** FreeLLMAPI integration

---

# FreeLLMAPI integration

Use **Webz.io News Search** from a self-hosted [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) gateway with [`@webz.io/freellmapi`](https://www.npmjs.com/package/@webz.io/freellmapi).

FreeLLMAPI sends web search to a custom relay that speaks Tavily's JSON shape. This package is that relay. It calls `POST https://api.webz.io/api/news/context` and returns article title, URL, excerpt, and score.

Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/freellmapi`)

## Prerequisites

- Node.js 20.18 or newer
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api))
- FreeLLMAPI running on the same machine as the relay, or another network path you control

Get the token from the [Webz.io dashboard](https://webz.io).

## Install and run

```bash
npm install @webz.io/freellmapi
export WEBZ_API_TOKEN="your-webz-api-token"
npx webz-freellmapi
```

The relay listens on `http://127.0.0.1:8787`. `PORT` and `WEBZ_FREELLMAPI_HOST` change the bind address. `WEBZ_NEWS_SEARCH_URL` must be an `https://` URL. The token is not sent to any other URL.

## Register the relay

In FreeLLMAPI, open **Keys → Add key → Custom provider** and choose **Web search**.

| Field | Value |
| --- | --- |
| Base URL | `http://127.0.0.1:8787` |
| Model id | `webz-news` |
| API key | Your Webz token, or leave it empty when `WEBZ_API_TOKEN` is set on the relay |

FreeLLMAPI calls `POST {base_url}/search` with `{ "query", "max_results" }`. Optional `topic` (`general` or `news`) and `include_answer` are accepted. Both topics search news from the last 30 days. The API has no `days` field, and this relay does not send one. `include_answer` does not add a generated answer.

Each search uses News Search credits. `GET /usage` on the relay checks the token with an empty body and does not request articles.

## Direct call

```ts
import { WebzSearchProvider } from "@webz.io/freellmapi";

const provider = new WebzSearchProvider();
const response = await provider.search({
  query: "recent developments on EU AI regulation",
  max_results: 5,
});

for (const hit of response.results) {
  console.log(hit.title, hit.url, hit.content);
}
```

`score` is the News Search match score from 0 to 10.
