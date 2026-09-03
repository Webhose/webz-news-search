# Vercel AI SDK integration (draft for docs.webz.io)

> **For docs team:** Publish under **Framework SDKs**, same level as [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp), [LangChain integration](https://docs.webz.io/docs/webz/news-search-api-langchain), and [LlamaIndex integration](https://docs.webz.io/docs/webz/news-search-api-llamaindex).
>
> **Suggested URL:** `/docs/webz/news-search-api-vercel-ai-sdk`
>
> **Suggested title:** Vercel AI SDK integration
>
> **Also add:** link from the Framework SDKs index page and from MCP Server.

---

# Vercel AI SDK integration

Use **Webz.io Contextual News Search** in [Vercel AI SDK](https://ai-sdk.dev/) applications with the official npm package [`@webz.io/ai-sdk`](https://www.npmjs.com/package/@webz.io/ai-sdk).

The package is a thin TypeScript wrapper around the hosted [News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp). It uses [`@ai-sdk/mcp`](https://www.npmjs.com/package/@ai-sdk/mcp) under the hood. Tool names, descriptions, and filter schemas come live from `tools/list` on the server. When Webz adds new filters, they appear automatically without republishing the package.

Goal: appear in the [Vercel AI SDK tools registry](https://ai-sdk.dev/tools-registry) next to tools like Tavily and Exa, so developers can connect Webz news search to agents in a few lines of code.

## Prerequisites

- Node.js 18+ (Node 22+ recommended for latest `@ai-sdk/mcp` v2)
- A Webz.io API token (same token as the [News Search API](https://docs.webz.io/docs/webz/news-search-api-quickstart))
- Vercel AI SDK (`ai`) and a provider for your LLM (OpenAI, OpenRouter, and others)

Get your token from the [Webz.io dashboard](https://webz.io).

## Install

```bash
npm install @webz.io/ai-sdk ai @ai-sdk/openai
export WEBZ_API_TOKEN="your-webz-api-token"
```

Package: [npmjs.com/package/@webz.io/ai-sdk](https://www.npmjs.com/package/@webz.io/ai-sdk)  
Source: [github.com/Webhose/webz-news-search](https://github.com/Webhose/webz-news-search) (`packages/ai-sdk`)

## Quick start: direct search

No LLM required. Call the hosted MCP tool directly:

```ts
import { flattenToolResult, webzNewsSearch } from "@webz.io/ai-sdk";

const session = await webzNewsSearch(); // reads WEBZ_API_TOKEN

try {
  const result = await session.client.callTool({
    name: session.toolName,
    arguments: {
      query: "recent developments on EU AI regulation",
      k: 10,
      days: 30,
    },
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
import { flattenToolResult, webzNewsSearch } from "@webz.io/ai-sdk";

const session = await webzNewsSearch();
try {
  const result = await session.client.callTool({
    name: session.toolName,
    arguments: {
      query: "trade agreements between USA and Germany",
      k: 10,
      days: 7,
      language: ["english"],
      country: ["US", "GR"],
    },
  });
  console.log(flattenToolResult(result));
} finally {
  await session.close();
}
```

To load every tool and filter your connection supports (from live MCP `tools/list`):

```ts
import { getWebzTools } from "@webz.io/ai-sdk";

const { tools, close } = await getWebzTools();
try {
  const newsTool = tools.news_search_by_webz as {
    inputSchema?: { jsonSchema?: { properties?: Record<string, unknown> } };
  };
  const filterNames = Object.keys(
    newsTool.inputSchema?.jsonSchema?.properties ?? {},
  ).sort();
  console.log(filterNames);
} finally {
  await close();
}
```

## Use with `generateText` / `streamText`

Pass Webz tools into the Vercel AI SDK. Use an explicit provider module (`@ai-sdk/openai`). Do **not** rely on bare model strings like `"openai/gpt-4.1-mini"` unless you configure [Vercel AI Gateway](https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools) with `AI_GATEWAY_API_KEY`.

### OpenAI

```ts
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, isStepCount } from "ai";
import { getWebzTools } from "@webz.io/ai-sdk";

const openai = createOpenAI({ apiKey: process.env.OPENAI_API_KEY });
const { tools, close } = await getWebzTools();

try {
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    system:
      "You are a news research assistant. Always call news_search_by_webz before answering.",
    prompt:
      'Call news_search_by_webz once for "Nvidia supply chain risks" with k=5 and days=30, then summarize with sources.',
    tools,
    stopWhen: isStepCount(4),
  });
  console.log(text);
} finally {
  await close();
}
```

### OpenRouter

```ts
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, isStepCount } from "ai";
import { getWebzTools } from "@webz.io/ai-sdk";

const openrouter = createOpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: "https://openrouter.ai/api/v1",
});
const { tools, close } = await getWebzTools();

try {
  const { text } = await generateText({
    model: openrouter("openai/gpt-4o-mini"),
    system:
      "You are a news research assistant. Always call news_search_by_webz before answering.",
    prompt:
      'Call news_search_by_webz once for "Nvidia supply chain risks" with k=5 and days=30, then summarize with sources.',
    tools,
    stopWhen: isStepCount(4),
  });
  console.log(text);
} finally {
  await close();
}
```

**Model note:** Some OpenRouter models (for example `meta-llama/llama-3.3-70b-instruct`) may skip tool calls. Prefer `openai/gpt-4o-mini` or native OpenAI models for reliable `news_search_by_webz` usage.

### Example prompts for agents

- "Find recent articles about Nvidia supply-chain risks and summarize with sources."
- "Find negative coverage about Boeing from the last 7 days using Webz news search."
- "Search Webz for EU AI regulation news from the past 30 days and list the top sources."

## API overview

| Export | Purpose |
| --- | --- |
| `getWebzTools()` | Load all MCP tools as Vercel AI SDK tools |
| `webzNewsSearch()` | Return the news search tool session (`toolName`, `client`, `tools`) |
| `createWebzClient()` | Low-level MCP client |
| `flattenToolResult()` | Turn MCP content blocks into readable text |
| `WebzConfigError` | Configuration errors (missing token, empty tool list) |

## How it works

```
Your TypeScript app
    ↓
@webz.io/ai-sdk (npm)
    ↓
@ai-sdk/mcp
    ↓
Hosted MCP server: https://news-search-mcp.webz.io/mcp
    ↓
Webz News Search API
```

- **Tool name:** `news_search_by_webz` (from MCP `tools/list`)
- **Schema:** loaded at runtime from the MCP server, not hardcoded in the package
- **Auth:** `Authorization: Bearer <WEBZ_API_TOKEN>`
- **Credits:** same as News Search API and MCP

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `WEBZ_API_TOKEN` | required | API token from the Webz.io dashboard |
| `WEBZ_MCP_URL` | `https://news-search-mcp.webz.io/mcp` | Override for testing against another MCP endpoint |

You can also pass `apiToken` and `mcpUrl` to `getWebzTools()`, `webzNewsSearch()`, and `createWebzClient()`.

## MCP vs Vercel AI SDK package

| Approach | Best for |
| --- | --- |
| [MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp) | Cursor, Claude Desktop, ChatGPT connectors |
| **@webz.io/ai-sdk** | TypeScript apps using Vercel AI SDK (`generateText`, `streamText`, agents) |

Both use the same token, the same MCP server, and the same search logic. Pick the integration that matches your framework.

## Troubleshooting

**`missing Webz API token`**  
Set `WEBZ_API_TOKEN` or pass `apiToken:` to the helper.

**`MCP server returned no tools`**  
Check your token, network access to `news-search-mcp.webz.io`, and that `WEBZ_MCP_URL` is correct.

**`GatewayAuthenticationError` / `AI_GATEWAY_API_KEY`**  
You used a bare model string like `"openai/gpt-4.1-mini"` without AI Gateway. Use `createOpenAI()` from `@ai-sdk/openai` instead.

**Agent answers without searching**  
The LLM skipped the tool. Use a model with reliable tool calling (for example `openai/gpt-4o-mini` via OpenRouter or OpenAI directly).

## Vercel tools registry (future)

After `@webz.io/ai-sdk` is published on npm, Webz will submit a one-time metadata PR to [vercel/ai `registry.ts`](https://github.com/vercel/ai/blob/main/content/tools-registry/registry.ts) so the package appears on [ai-sdk.dev/tools-registry](https://ai-sdk.dev/tools-registry). Guide: [add-new-tool-to-registry.md](https://github.com/vercel/ai/blob/main/contributing/add-new-tool-to-registry.md).

Suggested listing name: **Webz.io Contextual News Search**

## Related links

- [News Search MCP Server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [News Search API filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Vercel AI SDK MCP tools](https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools)
- [Vercel AI SDK tools registry](https://ai-sdk.dev/tools-registry)
- [npm: @webz.io/ai-sdk](https://www.npmjs.com/package/@webz.io/ai-sdk)
- [GitHub: webz-news-search](https://github.com/Webhose/webz-news-search)