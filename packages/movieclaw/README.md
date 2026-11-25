# movieclaw-webz

Search global news from the last 30 days with [Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api).

[MovieClaw](https://github.com/movieclaw/MovieClaw) keeps its built-in `web_search` providers for the general web. This package is separate. A MovieClaw user installs it and copies one skill into `data/agent-skills/`. The command takes the same inputs as that built-in tool: a query, a result count from 1 to 8, and an optional site.

MovieClaw's own agent does not connect to remote MCP servers. The skill runs `movieclaw-webz`, which calls `POST https://api.webz.io/api/news/context`. An outside agent that already talks to MovieClaw can add the hosted News Search MCP server on its own. That server is `https://news-search-mcp.webz.io/mcp` and the tool name is `news_search_by_webz`.

## Install

```bash
pip install movieclaw-webz
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io). It is the same token as the News Search API.

Install the package on the machine where MovieClaw runs shell commands, and set `WEBZ_API_TOKEN` in that environment.

## MovieClaw skill

Copy the skill directory into MovieClaw's user skill directory. The default path is `data/agent-skills/` inside the MovieClaw data directory. A skill already named `webz-news-search` is replaced by this copy.

```bash
python -c "import movieclaw_webz, pathlib; print(pathlib.Path(movieclaw_webz.__file__).resolve().parent / 'skill' / 'webz-news-search')"
```

Copy that directory to `data/agent-skills/webz-news-search/`. MovieClaw loads it on the next turn. No restart.

The skill tells the agent to run:

```bash
movieclaw-webz --max-results 5 "recent developments on EU AI regulation"
movieclaw-webz --max-results 5 --domain reuters.com "recent developments on EU AI regulation"
```

`--domain` is one hostname, such as `reuters.com`. It is sent as `filters.domain`.

## Python

```python
import asyncio

from movieclaw_webz import WebzNewsSearchProvider, format_hits


async def main() -> None:
    provider = WebzNewsSearchProvider()
    hits = await provider.search(
        "recent developments on EU AI regulation",
        max_results=5,
        domain="reuters.com",
    )
    print(format_hits("recent developments on EU AI regulation", hits))


asyncio.run(main())
```

`WebzNewsSearchProvider()` reads `WEBZ_API_TOKEN`. Pass `api_key` to supply the token in code. Each hit has `title`, `url`, `snippet`, and `date` (`YYYY-MM-DD`).

`search` always limits the request to the last 30 days. The API has no `days` field. The client sends that window as `filters.published_from`.

## Token and endpoint

The command sends the token as a bearer header. `WEBZ_NEWS_SEARCH_URL` can replace the endpoint. A URL that is not HTTPS is rejected before the token is sent.

## Outside agents

MovieClaw exposes its own MCP server. It does not call other MCP servers. Cursor, Claude, or ChatGPT can connect to News Search beside MovieClaw:

| Setting | Value |
| --- | --- |
| Server URL | `https://news-search-mcp.webz.io/mcp` |
| Header | `Authorization: Bearer <WEBZ_API_TOKEN>` |
| Tool | `news_search_by_webz` |

Use the HTTPS URL above. Do not send the token to any other address.

## Coverage

The News Search index is the last 30 days. See the [News Search API](https://docs.webz.io/docs/webz/news-search-api).
