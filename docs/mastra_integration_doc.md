# Mastra integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [Vercel AI SDK integration](https://docs.webz.io/docs/webz/news-search-api-vercel-ai-sdk).
>
> **Suggested URL:** `/docs/webz/news-search-api-mastra`
>
> **Suggested title:** Mastra integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server. Mastra's tools integrations list links to packages such as [`@mastra/tavily`](https://mastra.ai/integrations/tools/tavily). After `@webz.io/mastra` is on npm, that list can link here the same way.

---

# Mastra integration

Use **Webz.io Contextual News Search** inside [Mastra](https://mastra.ai/) agents with the official npm package [`@webz.io/mastra`](https://www.npmjs.com/package/@webz.io/mastra).

The package is a thin TypeScript wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). It uses Mastra's [`MCPClient`](https://mastra.ai/reference/tools/mcp-client) (`@mastra/mcp`) under the hood. Tool names, descriptions, and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Pass the tools from `getWebzTools()` to `new Agent({ tools })`. Call `close()` when the agent is done so the MCP session shuts down.

## Prerequisites

- Node.js 22.13+ (required by Mastra)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- `@mastra/core` in your project, plus a model provider key (OpenAI, Anthropic, and others)

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
npm install @webz.io/mastra @mastra/core
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [npmjs.com/package/@webz.io/mastra](https://www.npmjs.com/package/@webz.io/mastra)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/mastra`)

## Quick start: direct search

No LLM required. Call the hosted MCP tool directly:

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

You can also pass the token explicitly:

```ts
const session = await webzNewsSearch({ apiToken: "your-webz-api-token" });
```

Each call uses your News Search API credits and rate limits, same as the MCP server or REST API.

## Filtered search

Use the same filters as the [MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference). Example:

```ts
import { callWebzTool, flattenToolResult, webzNewsSearch } from "@webz.io/mastra";

const session = await webzNewsSearch();
try {
  const result = await callWebzTool(session.tool, {
    query: "trade agreements between USA and Germany",
    k: 10,
    days: 7,
    language: ["english"],
    country: ["US", "GR"],
  });
  console.log(flattenToolResult(result));
} finally {
  await session.close();
}
```

To load every tool and filter your connection supports (from live MCP `tools/list`):

```ts
import { getWebzTools } from "@webz.io/mastra";

const { tools, close } = await getWebzTools();
try {
  console.log(Object.keys(tools).sort());
  console.log(tools.news_search_by_webz?.id);
} finally {
  await close();
}
```

## Use with a Mastra agent

Pass Webz tools into a Mastra agent. The model decides when to search and which filters to use. The tool id is `news_search_by_webz`.

```ts
import { Agent } from "@mastra/core/agent";
import { getWebzTools } from "@webz.io/mastra";

const { tools, close } = await getWebzTools();

try {
  const agent = new Agent({
    id: "webz-news-agent",
    name: "Webz News Agent",
    instructions:
      "You are a news research assistant. Always call news_search_by_webz before answering. Cite article titles and URLs.",
    model: "openai/gpt-4.1-mini",
    tools,
  });
  const result = await agent.generate(
    "Search Webz news for renewable energy investments from the past 30 days and summarize with sources.",
  );
  console.log(result.text);
} finally {
  await close();
}
```

### Example prompts for agents

- "Find recent articles about Nvidia supply-chain risks and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Search Webz for EU AI regulation news from the past 30 days and list the top sources."

## API overview

| Export | Purpose |
| --- | --- |
| `getWebzTools()` | Load all MCP tools as Mastra tools |
| `webzNewsSearch()` | Return the news search tool session (`tool`, `toolName`, `tools`) |
| `callWebzTool()` | Run a loaded tool without an agent |
| `createWebzClient()` | Low-level Mastra `MCPClient` |
| `flattenToolResult()` | Turn MCP content blocks into readable text |
| `WebzConfigError` | Configuration errors (missing token, non-HTTPS URL, empty tool list) |

## How it works

```
Your TypeScript app
    ↓
@webz.io/mastra (npm)
    ↓
@mastra/mcp MCPClient
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded at runtime from the MCP server, not hardcoded in the package
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`
- **Transport:** HTTPS only. Any other MCP URL is rejected before the token is sent.
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint. Must be an absolute `https://` URL. |

You can also pass `apiToken` and `mcpUrl` to `getWebzTools()`, `webzNewsSearch()`, and `createWebzClient()`.

## MCP vs Mastra package

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **@webz.io/mastra** | TypeScript apps and agents built with Mastra |
| **@webz.io/ai-sdk** | TypeScript apps using the Vercel AI SDK (`generateText`, `streamText`) |

Mastra agents take Mastra tools (`createTool` or `MCPClient`). `@webz.io/ai-sdk` is the package for Vercel AI SDK apps. Both use the same token, the same MCP server, and the same search logic.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `apiToken:` to the helper.

**`The Webz.io MCP endpoint must be an absolute https:// URL`**  
`WEBZ_MCP_URL` or `mcpUrl` is missing `https://`. The client rejects it before sending the token.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**Agent answers without searching**  
The LLM skipped the tool. Mention `news_search_by_webz` in the agent instructions, and use a model with reliable tool calling.

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Mastra MCPClient](https://mastra.ai/reference/tools/mcp-client)
- [Mastra Tavily tools](https://mastra.ai/integrations/tools/tavily) (same kind of tools-page link)
- [npm: @webz.io/mastra](https://www.npmjs.com/package/@webz.io/mastra)
- [Vercel AI SDK integration](https://docs.webz.io/docs/webz/news-search-api-vercel-ai-sdk) (draft: [docs/ai_sdk_doc.md](ai_sdk_doc.md))
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)
