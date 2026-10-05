# Webz News Search integrations

Public SDKs for the hosted Webz.io News Search MCP server:

`https://news-search-mcp.webz.io/mcp`

The MCP server is the source of truth. These packages are thin clients. New filters and tools on the server show up at runtime through `tools/list`.

| Package | Registry | Path |
| --- | --- | --- |
| `webzio-news-search` | PyPI | `packages/news-search` |
| `langchain-webz` | PyPI | `packages/langchain` |
| `llama-index-tools-webz` | PyPI | `packages/llamaindex` |
| `ag2-webzio` | PyPI | `packages/ag2` |
| `crewai-webzio` | PyPI | `packages/crewai` |
| `lfx-webz` | PyPI | `packages/langflow` |
| `gpt-researcher-webz` | PyPI | `packages/gpt-researcher` |
| `@webz.io/ai-sdk` | npm | `packages/ai-sdk` |
| `n8n-nodes-webz-news-search` | npm | [github.com/Webhose/n8n-nodes-webz-news-search](https://github.com/Webhose/n8n-nodes-webz-news-search) |
| `webz_news_search` | Dify Marketplace (`.difypkg`) | `packages/dify` |
| `webzio/news-search` | Apify Store | [apify.com/webzio/news-search](https://apify.com/webzio/news-search) |

## Direct API client

[`webzio-news-search`](packages/news-search) calls the [News Search API](https://docs.webz.io/docs/webz/news-search-api) (`POST /api/news/context`) directly with `httpx`, returns typed results, and ships a JSON tool schema plus `run_tool()` for any LLM with function calling. Use it when you do not want an MCP client or agent framework in the loop.

The n8n community node [`n8n-nodes-webz-news-search`](https://github.com/Webhose/n8n-nodes-webz-news-search) calls the same endpoint. The built-in n8n MCP Client Tool still talks to the hosted MCP server.

## Official MCP Registry

The bundle in [`mcp-registry/`](mcp-registry) publishes the hosted server to
[registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io) as
`io.webz/news-search`. Aggregators such as PulseMCP and Glama ingest the
official registry, so this listing propagates downstream automatically.
Publishing requires a one-time DNS TXT record on `webz.io` — see
[`mcp-registry/PUBLISHING.md`](mcp-registry/PUBLISHING.md).

## Groq

No package. Groq's [Responses API](https://console.groq.com/docs/tool-use/remote-mcp) speaks remote MCP itself, so you pass the hosted server in `tools` and Groq runs `tools/list` and `tools/call` server side.

Reference implementation, runnable examples, and the [groq-api-cookbook](https://github.com/groq/groq-api-cookbook) contribution bundle are in [`packages/groq`](packages/groq).

## n8n

Two paths:

- **Community node** ([`n8n-nodes-webz-news-search`](https://github.com/Webhose/n8n-nodes-webz-news-search)): calls `POST https://api.webz.io/api/news/context`. Standalone workflows, structured article output, and optional use as an AI Agent tool.
- **Built-in MCP Client Tool** ([`n8n/`](n8n)): no install step; connect an AI Agent directly to the MCP server so filters still come from `tools/list` at runtime.

Setup steps and importable workflow templates are in [`n8n/`](n8n).

## Apify

Not a PyPI package. The Actor is [`webzio/news-search`](https://apify.com/webzio/news-search). Users pay Apify. The Actor calls `POST https://api.webz.io/api/news/context` with one shared Webz token and writes one dataset row per article.

Docs draft: [`docs/apify_integration_doc.md`](docs/apify_integration_doc.md)

## Dify

Not a PyPI package. Dify Marketplace installs a `.difypkg` plugin from [`packages/dify`](packages/dify). After the listing PR is merged, search for **Webz News Search** on [marketplace.dify.ai](https://marketplace.dify.ai/). Dify v1.6+ can also add `https://news-search-mcp.webz.io/mcp` under Tools → MCP without a plugin.

Docs: https://docs.webz.io/docs/webz/news-search-api-mcp