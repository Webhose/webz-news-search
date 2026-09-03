# n8n integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex).
>
> **Suggested URL:** `/docs/webz/news-search-api-n8n`
>
> **Suggested title:** n8n integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server (n8n is an MCP client, so it belongs in the Step 2 client list next to Cursor and Claude Code).

---

# n8n integration

Use **Webz.io Contextual News Search** inside [n8n](https://n8n.io/) workflows and AI agents with the official community node [`n8n-nodes-webz-news-search`](https://www.npmjs.com/package/n8n-nodes-webz-news-search).

The node is a thin wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). Filter schemas come live from `tools/list` on the server. When Webz adds new filters, they are reachable through **Additional Fields (JSON)** without republishing the node.

n8n also ships a built-in **MCP Client Tool** node that talks to remote MCP servers, so there are two ways to search Webz news from n8n:

| Approach | Best for |
| --- | --- |
| **`n8n-nodes-webz-news-search`** community node | Standalone workflows, one output item per article, Sheets and Slack automations with no LLM in the loop |
| Built-in [**MCP Client Tool**](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp) node | AI Agent workflows where the model picks filters itself from the live MCP schema |

Both use the same token, the same MCP server, and the same search logic, and they can be combined in one workflow.

Webz is distributed as an [n8n community node](https://docs.n8n.io/integrations/community-nodes/) on npm. Discoverability is via npm, this docs page, and the node search box inside n8n.

## Prerequisites

- n8n 2.x, Cloud or self-hosted (the community node declares an `n8n-workflow >= 2 < 3` peer dependency and installs on self-hosted n8n; n8n Cloud can use the built-in MCP Client Tool)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- For agent workflows: an **AI Agent** node and any tool-calling chat model

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

In n8n, open **Settings → Community nodes → Install a community node**, enter the package name, acknowledge the risk prompt, and install:

```
n8n-nodes-webz-news-search
```

Package: [npmjs.com/package/n8n-nodes-webz-news-search](https://www.npmjs.com/package/n8n-nodes-webz-news-search)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/n8n-node`)

The node has zero runtime npm dependencies and uses only n8n's own HTTP helpers.

On self-hosted n8n, set this before attaching the node to an AI Agent as a tool:

```bash
N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true
```

## Credentials

Add a **Webz.io News Search API** credential and paste your Webz.io API token.

The credential test calls MCP `initialize` only, so saving it does not consume search credits.

Paste the token even if it already exists in a `.env` file on the host. n8n keeps credentials in its own encrypted store and never reads your project's environment.

## Quick start: direct search

No LLM required. Add the node and run it:

1. Add a **Webz.io News Search** node to a workflow.
2. Set **Query** to a natural language search, for example `Nvidia earnings analyst reaction`.
3. Leave **Simplify** enabled.
4. Execute the node.

| Field | Default | Description |
| --- | --- | --- |
| Query | required | Natural language search. Put the search subject here, not in the Topic filter |
| Limit | 50 | Maximum articles to return |
| Simplify | enabled | Split the response into one item per article |
| Additional Filters | — | Optional filter collection, see below |

With **Simplify** enabled, each article arrives as its own n8n item:

```json
{
  "title": "Michael Burry sends another Nvidia stock verdict to investors",
  "url": "https://finance.yahoo.com/...",
  "published": "2026-08-30T20:33:00.000+03:00",
  "score": 8.6,
  "excerpt": "Nvidia earnings beat and August 27 stock reaction...",
  "query": "Nvidia earnings analyst reaction",
  "resultIndex": 1
}
```

Turn **Simplify** off to get the raw MCP text response as a single `{ "result": "..." }` item.

Each execution uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Filtered search

Open **Additional Filters** and add any of the following. Everything is optional, most filters accept multiple values, and the accepted values match the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).

| Filter | Notes |
| --- | --- |
| Days | Lookback window. Leave at 0 for the server default |
| Search All Dates | Search the full indexed window instead of a lookback period |
| Language | Full names, not codes: `english`, `french`, `arabic` |
| Country | ISO-2 uppercase: `US`, `GB`, `IL` |
| Sentiment | `positive`, `negative`, `neutral` |
| Category | IPTC category labels such as `Politics` or `Science and Technology` |
| Domain / Exclude Domain | Restrict to or skip source domains. A domain must never appear in both |
| Topic, Person, Organization, Location | Entity and context enrichment |
| Ticker | Uppercase symbols: `NVDA`, `AAPL` |
| Source Type, Political Bias, Trust Category | Source characteristics |
| Domain Rank ≥ / ≤ | Source rank range, lower is more popular |
| Score ≥ / ≤ | Match score 0-10. Leave at 0 to use the server default |
| Trust ≥ | Minimum trust score, 0.0 to 1.0 |
| Sort By | `best_score`, `similarity`, `date_desc`, `date_asc` |
| Allow Multiple Chunks Per Article | Return more than one matching passage from the same article |
| Additional Fields (JSON) | Escape hatch for server-side filters newer than the node |

See [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters) for the full list of accepted values.

## Use with an n8n AI Agent

Two options, and they behave differently.

### Option 1: the community node as an agent tool

The node ships with `usableAsTool: true`, so n8n also exposes a **Webz.io News Search Tool** variant. Connect it to an **AI Agent** node's **Tool** input the same way you would connect any other tool node.

On self-hosted n8n this requires `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true`. It is not available on n8n Cloud.

### Option 2: the built-in MCP Client Tool node

Add an **MCP Client Tool** node, connect it to the agent's **Tool** input, and configure:

| Field | Value |
| --- | --- |
| Endpoint | `https://news-search-mcp.webz.io/mcp` |
| Server Transport | `HTTP Streamable` |
| Authentication | `Bearer` |
| Tools | `All` |

On the Authentication field, create a **Bearer Auth** credential and paste your Webz.io API token as the bearer token. The agent now has a `news_search_by_webz` tool and reads the filter schema live from the server.

**Leave Tools set to `All`.** n8n has an open bug ([n8n#23421](https://github.com/n8n-io/n8n/issues/23421)) where the Bearer token is not sent when tool selection is narrowed to specific tools. The Webz.io server exposes a single tool, so `All` is the correct setting regardless.

The MCP Client Tool is an agent sub-node and cannot run on its own, so every workflow using it needs an AI Agent node and a chat model. For news search without an LLM, use the community node instead.

### Example prompts for agents

- "Search Webz news for analyst reaction to Nvidia earnings. Use ticker NVDA, the last 7 days, English only, and limit to 5 results."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Use the Webz news tool to compare EU and US AI regulation news from the past month, with sources."

**Name the `query` argument explicitly.** There is also a `topic` filter, and models will otherwise put the search subject there and hit a validation error, because `topic` expects a list.

## Ready-made templates

Four workflows are available in [`n8n/templates`](https://github.com/Webhose/webz-news-search/tree/master/n8n/templates). In n8n, use **Import from File** from the workflow menu and pick one.

| Template | What it does | Integration |
| --- | --- | --- |
| [`news-to-sheet.json`](https://github.com/Webhose/webz-news-search/blob/master/n8n/templates/news-to-sheet.json) | Manual search that appends structured article rows to Google Sheets | Community node |
| [`daily-news-digest-slack.json`](https://github.com/Webhose/webz-news-search/blob/master/n8n/templates/daily-news-digest-slack.json) | Runs every morning at 08:00, searches the last 24 hours on a topic, and posts a sourced digest to Slack | MCP Client Tool |
| [`ticker-monitor.json`](https://github.com/Webhose/webz-news-search/blob/master/n8n/templates/ticker-monitor.json) | Checks a stock ticker every 6 hours and alerts Slack only when something material turns up | MCP Client Tool |
| [`news-research-agent.json`](https://github.com/Webhose/webz-news-search/blob/master/n8n/templates/news-research-agent.json) | Chat interface for interactive news research, with conversation memory | MCP Client Tool |

### Configuring a template

Every template keeps its adjustable values in one **Settings** node, so you should not need to touch the agent prompts.

| Template | Settings fields |
| --- | --- |
| `news-to-sheet.json` | `query`, `limit`, `days`, `sheetId`, `sheetName` |
| `daily-news-digest-slack.json` | `searchQuery`, `lookbackDays`, `resultCount`, `slackChannel` |
| `ticker-monitor.json` | `ticker`, `lookbackDays`, `resultCount`, `slackChannel` |

### Adding credentials

Templates never ship credentials, so these fields arrive empty by design.

| Node | Credential |
| --- | --- |
| Webz.io News Search (community node) | **Webz.io News Search API** with your Webz.io token |
| Webz.io News Search (MCP Client Tool) | **Bearer Auth** with your Webz.io token |
| OpenAI Chat Model | Your OpenAI key, or swap the node for any other tool-calling model |
| Append rows | Google Sheets OAuth2 |
| Slack | **Slack API** with a bot token |

The three agent templates use OpenAI because it is the most common default. Swap the chat model node for Anthropic, Google, Ollama, or an OpenAI-compatible provider and the rest of the workflow is unchanged.

For Slack, the bot token needs `chat:write` to post and `channels:read` to resolve the channel name, plus `groups:read` for a private channel. Then invite the bot with `/invite @YourApp`. Correct scopes with an uninvited bot returns `not_in_channel`, which looks like an auth failure but is not.

### Scheduled templates and timezones

`daily-news-digest-slack.json` and `ticker-monitor.json` are scheduled, and n8n defaults to UTC. An 08:00 digest fires at 08:00 UTC until you change it.

- **n8n Cloud:** set it per workflow under **Workflow Settings → Timezone**, or instance-wide in account settings
- **Self-hosted:** set the `GENERIC_TIMEZONE` environment variable

Both alerting templates guard their output, so they post only when the agent actually returns content and raise a workflow error otherwise instead of sending an empty message.

## How it works

```
n8n workflow
    ↓
n8n-nodes-webz-news-search (npm)   or   built-in MCP Client Tool node
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Node type:** `n8n-nodes-webz-news-search.webzNewsSearch`, plus `...webzNewsSearchTool` for agent use
- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** read live from the MCP server, not hardcoded in the node
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`
- **Sessions:** the community node opens one MCP session per execution and closes it when finished
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| API Token | required | Credential field, from the Webz.io dashboard |
| MCP URL | `https://news-search-mcp.webz.io/mcp` | Hidden credential field, for testing against another MCP endpoint |
| `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE` | `false` | Self-hosted only. Required to use the node as an AI Agent tool |
| `GENERIC_TIMEZONE` | `UTC` | Self-hosted only. Affects scheduled workflows |

## MCP vs n8n community node

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| MCP Client Tool node in n8n | n8n AI Agent workflows that pick filters from the live schema |
| **n8n-nodes-webz-news-search** | n8n workflows that need structured article rows without an LLM |

Both use the same token, the same MCP server, and the same search logic. Pick the integration that matches your workflow.

## Troubleshooting

**A tool failure looks like an empty result**  
An AI Agent catches tool errors and answers as though nothing was found, so a broken credential shows up as "no news" rather than a failed run. If a scheduled workflow goes quiet, open a recent execution and inspect the search node directly.

**`Unrecognized node type: n8n-nodes-webz-news-search.webzNewsSearch`**  
The package is not installed on this instance, or the workflow was imported from a release that used a different package name. Install from **Settings → Community nodes** and re-import the template.

**The node does not appear in the node panel**  
Community packages are disabled. Check `N8N_COMMUNITY_PACKAGES_ENABLED` on self-hosted n8n.

**The node cannot be attached to an AI Agent**  
Set `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true` and restart n8n. This is not configurable on n8n Cloud.

**Empty results with `category` or `sentiment` set**  
Drop those two filters and retry before concluding there is no coverage.

**Validation error on `topic`**  
`topic` expects a list of topic tags, not the search subject. Put the subject in **Query**.

**`401 Unauthorized` from the MCP Client Tool**  
Confirm the Bearer Auth credential holds the token, and leave **Tools** set to `All` because of [n8n#23421](https://github.com/n8n-io/n8n/issues/23421).

**Self-hosted instance cannot reach the server**  
Allow outbound HTTPS from the n8n container to `news-search-mcp.webz.io`.

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [n8n community nodes documentation](https://docs.n8n.io/integrations/community-nodes/)
- [n8n MCP Client Tool node](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp)
- [npm: n8n-nodes-webz-news-search](https://www.npmjs.com/package/n8n-nodes-webz-news-search)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
