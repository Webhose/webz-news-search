# Webz News Search integrations

Public SDKs for the hosted Webz.io News Search MCP server:

`https://news-search-mcp.webz.io/mcp`

The MCP server is the source of truth. These packages are thin clients. New filters and tools on the server show up at runtime through `tools/list`.

| Package | Registry | Path |
| --- | --- | --- |
| `langchain-webz` | PyPI | `packages/langchain` |
| `llama-index-tools-webz` | PyPI | `packages/llamaindex` |
| `@webz.io/ai-sdk` | npm | `packages/ai-sdk` |
| `@webz.io/n8n-nodes-news-search` | npm | `packages/n8n-node` |

## n8n

Two paths:

- **Community node** ([`packages/n8n-node`](packages/n8n-node)): standalone workflows, structured article output, and optional use as an AI Agent tool.
- **Built-in MCP Client Tool** ([`n8n/`](n8n)): no install step; connect an AI Agent directly to the MCP server so filters still come from `tools/list` at runtime.

Setup steps and importable workflow templates are in [`n8n/`](n8n).

Docs: https://docs.webz.io/docs/webz/news-search-api-mcp