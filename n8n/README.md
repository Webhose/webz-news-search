# Webz.io News Search in n8n

**Search global news with [Webz.io](https://webz.io) from n8n.**

You can use Webz.io news search in n8n two ways:

| Approach | Best for |
| --- | --- |
| [`n8n-nodes-webz-news-search`](../packages/n8n-node) community node | Standalone workflows, structured article rows, Sheets/Slack automations without an LLM |
| Built-in **MCP Client Tool** (below) | AI Agent workflows where the model picks filters from the live MCP schema |

Both talk to the same hosted MCP server and follow the same filter rules as the [`langchain-webz`](../packages/langchain), [`llama-index-tools-webz`](../packages/llamaindex), and [`@webz.io/ai-sdk`](../packages/ai-sdk) packages.

## Community node

Install from **Settings → Community nodes**:

```
n8n-nodes-webz-news-search
```

Then add a **Webz.io News Search** node, create a **Webz.io News Search API** credential with your token, and run a search. With **Simplify** enabled, each article becomes its own item with `title`, `url`, `published`, `score`, and `excerpt`.

To attach the node to an **AI Agent** on self-hosted n8n, set `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true`.

Package docs: [`packages/n8n-node/README.md`](../packages/n8n-node/README.md).

## MCP Client Tool (agent workflows)

n8n ships an **MCP Client Tool** node that talks to remote MCP servers over streamable HTTP. Point it at the hosted Webz.io News Search MCP server and your n8n agents can search global news straight away.

## Setup

1. Get a token from your [Webz.io dashboard](https://webz.io) (the same token as the News Search API).
2. In n8n, add an **AI Agent** node to a workflow and attach a chat model to it.
3. Add an **MCP Client Tool** node and connect it to the agent's **Tool** input.
4. Configure the MCP Client Tool node:

   | Field | Value |
   | --- | --- |
   | Endpoint | `https://news-search-mcp.webz.io/mcp` |
   | Server Transport | `HTTP Streamable` |
   | Authentication | `Bearer` |
   | Tools | `All` |

5. On the Authentication field, create a new **Bearer Auth** credential and paste your Webz.io API token as the bearer token.

The agent now has a `news_search_by_webz` tool. Ask it for news in plain language and it picks the filters itself.

## Templates

Ready-made workflows are in [`templates/`](templates). In n8n, use **Import from File** (workflow menu, top right) and pick one.

| Template | What it does |
| --- | --- |
| [`daily-news-digest-slack.json`](templates/daily-news-digest-slack.json) | Runs every morning, searches the last 24 hours on a topic, and posts a sourced digest to Slack |
| [`ticker-monitor.json`](templates/ticker-monitor.json) | Checks a stock ticker every few hours and alerts Slack only when something material turns up |
| [`news-research-agent.json`](templates/news-research-agent.json) | Chat interface for interactive news research, with conversation memory |
| [`news-to-sheet.json`](templates/news-to-sheet.json) | Manual or scheduled search with the community node, appending structured article rows to Google Sheets |

After importing, open the **Settings** node and change the search query, ticker, or channel there. Everything you would normally want to adjust lives in that one node, so you should not need to touch the agent prompts.

Then add credentials. Templates never ship credentials, so these fields arrive empty by design:

| Node | Credential |
| --- | --- |
| Webz.io News Search (community node) | **Webz.io News Search API**, with your Webz.io API token |
| Webz.io News Search (MCP Client Tool) | **Bearer Auth**, with your Webz.io API token |
| OpenAI Chat Model | Your OpenAI key, or replace the node with any other tool-calling model |
| Slack (digest and ticker templates only) | **Slack API** with a bot token |

For Slack, the bot token needs the `chat:write` scope to post and `channels:read` to resolve the channel name (`groups:read` as well for a private channel). Then invite the bot to the channel with `/invite @YourApp` — correct scopes with an uninvited bot returns `not_in_channel`, which looks like an auth failure but isn't.

Note that your Webz.io token has to be pasted into the n8n credential even if it is already in a `.env` file. n8n keeps credentials in its own encrypted store and never reads your project's environment.

## Filters

The agent reads the filter schema from the server and picks filters itself, but naming them in your prompt gives you far more control. `query` is the only required one.

| Filter | Notes |
| --- | --- |
| `query` | Natural language. Required. |
| `k` | 1-100, default 10 |
| `days` | Lookback window. Omit for the last 7 days, or use `allow_all_dates` for full coverage. |
| `language` | Full names, not codes: `english`, `french`, `arabic`, `hebrew` |
| `country` | ISO-2, uppercase: `US`, `IL`, `GB`, `DE` |
| `sentiment` | `positive`, `negative`, `neutral` |
| `category` | IPTC categories such as `Politics` or `Science and Technology`. Each label is one category. |
| `domain` / `exclude_domain` | Restrict to or exclude source domains. Never put the same domain in both. |
| `topic`, `person`, `organization`, `location` | Context enrichment |
| `ticker` | Uppercase symbols: `NVDA`, `AAPL` |
| `source_type`, `political_bias`, `trust_category` | Source characteristics |
| `domain_rank_gte` / `domain_rank_lte` | Source rank range |
| `score_gte` / `score_lte` | Match score 0-10. `score_gte` defaults to 4; set 0 to disable. |
| `sort_by` | `best_score` (default), `similarity`, `date_desc`, `date_asc` |

Most of these accept a list, so `country: ["US", "GB"]` is valid. The server is the source of truth and exposes a few more parameters than are listed here, so ask it directly with `tools/list` if you need the exact current schema. Reference docs: [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference) and [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters).

One quirk worth knowing: if a search with `category` or `sentiment` returns nothing, drop those two and retry before concluding there is no coverage.

A prompt that uses them well looks like this:

```
Search Webz.io news for analyst reaction to Nvidia earnings.
Use ticker NVDA, the last 7 days, English only, and limit to 5 results.
Give me the headline, publisher, and URL for each.
```

## Things worth knowing

- **Leave Tools set to `All`.** n8n has an open bug ([n8n#23421](https://github.com/n8n-io/n8n/issues/23421)) where the Bearer token is not sent to the MCP server when tool selection is narrowed to specific tools. Since the Webz.io server exposes one tool, `All` is the right setting anyway.
- **Set the timezone before trusting a schedule.** Two of the templates are scheduled and n8n defaults to UTC, so an 08:00 digest fires at 08:00 UTC until you change it. On n8n Cloud set it per workflow under **Workflow Settings → Timezone**, or instance-wide in your account settings. When self-hosting, set the `GENERIC_TIMEZONE` environment variable.
- **The MCP Client Tool is an agent sub-node.** It cannot run on its own, so every workflow using it needs an AI Agent node and a chat model. For news search without an LLM in the loop, use the [`n8n-nodes-webz-news-search`](../packages/n8n-node) community node instead.
- **Any tool-calling model works.** The templates use OpenAI because it is the most common default. Swap the chat model node for Anthropic, Google, Ollama, or an OpenRouter-backed OpenAI-compatible node and the rest of the workflow is unchanged.
- **Self-hosted n8n needs network access** from the n8n container to `news-search-mcp.webz.io` over HTTPS.
- **Calls use your normal API credits.** Each tool call is a regular News Search API request, with the same credits and rate limits as any other client.
- **Name the `query` argument explicitly in prompts.** There is also a `topic` filter, and models will otherwise put the search subject there and get a validation error, since `topic` expects a list. Tell the agent to pass the subject as `query`.
- **A tool failure looks like an empty result.** The agent catches tool errors and answers as though nothing was found, so a broken credential shows up as "no news" rather than a failed run. If a scheduled workflow goes quiet, open a recent execution and check the MCP node for a tool error.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [MCP server landing page](https://news-search-mcp.webz.io)
- [n8n MCP Client Tool docs](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp)
- [GitHub](https://github.com/Webhose/webz-news-search)
