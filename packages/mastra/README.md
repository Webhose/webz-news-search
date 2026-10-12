# @webz.io/mastra

**Search global news with [Webz.io](https://webz.io) from [Mastra](https://mastra.ai) agents - in natural language, with the most relevant articles first.**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) covers news and current events from sources worldwide. Ask a question in plain language, narrow results with filters (language, country, date, sentiment, domain, ticker, and more), and get back focused article excerpts with titles, URLs, and metadata.

Use this package with a Mastra `Agent`, or call the hosted MCP tool directly.

## What you get

- **Natural-language search** - no keyword hacking. Example: `"EU AI Act enforcement updates"` or `"How is Tesla stock reacting to earnings?"`
- **Worldwide coverage** - semantic search over Webz.io's global news index.
- **Rich filters** - language, country, days, sentiment, domain, ticker, person, organization, topic, and more. See the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
- **Live schema** - filters are loaded from the hosted MCP server (`tools/list`). New Webz filters appear automatically, without republishing this package.

## Install

```bash
npm install @webz.io/mastra @mastra/core
export WEBZ_API_TOKEN="your-webz-api-token"
```

Get a token from your [Webz.io dashboard](https://webz.io) (same token as the News Search API). Requires Node.js 22.13 or newer, the same baseline as Mastra.

Full setup and client options: [MCP Server docs](https://docs.webz.io/docs/webz/news-search-api-mcp).

## With a Mastra agent

```ts
import { Agent } from "@mastra/core/agent";
import { getWebzTools } from "@webz.io/mastra";

const { tools, close } = await getWebzTools();

try {
  const agent = new Agent({
    id: "webz-news-agent",
    name: "Webz News Agent",
    instructions:
      "You are a news research assistant. Always call news_search_by_webz before answering.",
    model: "openai/gpt-4.1-mini",
    tools,
  });
  const result = await agent.generate(
    "Find recent articles about Nvidia supply-chain risks",
  );
  console.log(result.text);
} finally {
  await close();
}
```

The tool id the model sees is `news_search_by_webz`. Its input schema comes from the hosted server.

## Direct search (no LLM)

```ts
import { callWebzTool, flattenToolResult, webzNewsSearch } from "@webz.io/mastra";

const session = await webzNewsSearch(); // reads WEBZ_API_TOKEN
try {
  const result = await callWebzTool(session.tool, {
    query: "recent developments on EU AI regulation",
    k: 10,
    days: 30,
  });
  console.log(flattenToolResult(result));
} finally {
  await session.close();
}
```

To see every tool your connection supports:

```ts
const { tools, close } = await getWebzTools();
console.log(Object.keys(tools).sort());
await close();
```

## How it works

This package connects to the hosted Webz News Search MCP server at `https://news-search-mcp.webz.io/mcp` via Mastra's `MCPClient` (`@mastra/mcp`). Each call runs a regular News Search API request with your token (same credits and rate limits). It does not hardcode filter fields - the tool schema comes from the live server. The MCP URL must be `https://`. Any other URL is rejected before the token is sent.

## Configuration

| Name | Default | Purpose |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | Webz API token from the dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for local MCP testing. Must be an absolute `https://` URL. |

You can also pass `apiToken` and `mcpUrl` to the helpers.

## Links

- [Webz.io](https://webz.io)
- [News Search MCP documentation](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [MCP server landing page](https://news-search-mcp.webz.io)
- [Mastra tools](https://mastra.ai/docs/agents/tools)
- [GitHub](https://github.com/Webhose/webz-news-search)
