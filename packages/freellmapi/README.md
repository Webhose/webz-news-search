# @webz.io/freellmapi

Search global news from [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) with [Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api).

FreeLLMAPI calls custom search relays with the same JSON body it sends to Tavily: `POST {base_url}/search` and `{ "query", "max_results" }`. This package is that relay. It calls `POST https://api.webz.io/api/news/context` and returns `{ "results": [{ "title", "url", "content", "score" }] }`.

News Search covers the last 30 days. The relay does not send a `days` field. `topic` may be `general` or `news`; both search the news index. `include_answer` is accepted and ignored. News Search returns articles, not a generated answer.

`@freellmapi/server` is a private workspace, so this package does not import `SearchOnlyProvider`. `WebzSearchProvider` follows that contract anyway: it does not serve chat, and `validateKey` does not run a search.

## Install

```bash
npm install @webz.io/freellmapi
export WEBZ_API_TOKEN="your-webz-api-token"
npx webz-freellmapi
```

Get a token from your [Webz.io dashboard](https://webz.io). The relay listens on `http://127.0.0.1:8787`. Set `PORT` and `WEBZ_FREELLMAPI_HOST` to change that. Set `WEBZ_NEWS_SEARCH_URL` only for an HTTPS replacement of the News Search API. Any other URL is rejected before the token is sent.

## Register it in FreeLLMAPI

In the dashboard, open **Keys → Add key → Custom provider** and pick **Web search**. Set the base URL to `http://127.0.0.1:8787` and the model id to `webz-news`.

- Paste the Webz token into the key field. FreeLLMAPI sends it as `Authorization: Bearer` on `POST /search`, and the relay forwards that header to News Search.
- Or leave the key empty. FreeLLMAPI then sends its keyless sentinel, and the relay reads `WEBZ_API_TOKEN` from its own environment.

The same registration is `POST /api/media/custom` with `modality` set to `"search"`.

FreeLLMAPI tries registered relays before catalog engines. A relay that is down fails over to those engines.

## Key check

`GET /usage` checks the token without searching. The probe posts an empty JSON object. A bad token is HTTP 401. A good token is HTTP 422 because `query` is required, and no articles are requested. `WebzSearchProvider.validateKey` uses that same probe.

## Call it from TypeScript

```ts
import { WebzSearchProvider } from "@webz.io/freellmapi";

const provider = new WebzSearchProvider();
const response = await provider.search({
  query: "recent developments on EU AI regulation",
  max_results: 5,
  topic: "news",
});

for (const hit of response.results) {
  console.log(hit.title, hit.url);
}
```

`score` is the News Search match score from 0 to 10. `content` is the matching excerpt, cut at 1,500 characters.

## Develop

```bash
cd packages/freellmapi
npm install
npm test
npm run typecheck
```

Offline tests mock the API. The live test runs only when `WEBZ_API_TOKEN` is set.
