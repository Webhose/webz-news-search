# Webz.io for Gemini CLI

Search indexed news, blog posts, and forum discussions, or compare coverage with aggregation counts. This extension connects directly to seven hosted Webz.io MCP servers using Streamable HTTP. It does not download or execute a local server.

## Install and connect

Install from the public Webz.io integrations repository:

```sh
gemini extensions install https://github.com/Webhose/webz-news-search
```

Restart Gemini CLI, run `/mcp`, then authenticate only the servers you need with `/mcp auth <server-name>`. For News Search, for example, run `/mcp auth webz-news-search`. Webz.io's OAuth page asks for your Webz.io API token. Your account must have access to the relevant API and available credits. An HTTP 401 before authentication is expected.

No API token is included in the extension. Gemini CLI discovers the OAuth settings from the servers. Authentication needs a local browser and a reachable localhost callback. An API token with one product entitlement may not work for other products.

## Servers

| Server | Endpoint | Documentation |
| --- | --- | --- |
| webz-news-search | https://news-search-mcp.webz.io/mcp | [Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) |
| webz-news | https://news-mcp.webz.io/mcp | [Webz.io News](https://docs.webz.io/docs/webz/news-api-mcp) |
| webz-blogs | https://blogs-mcp.webz.io/mcp | [Webz.io Blogs](https://docs.webz.io/docs/webz/blogs-api-mcp) |
| webz-forums | https://forums-mcp.webz.io/mcp | [Webz.io Forums](https://docs.webz.io/docs/webz/forums-api-mcp) |
| webz-news-segmentation | https://seg-news-mcp.webz.io/mcp | [Webz.io News Segmentation](https://docs.webz.io/docs/webz/news-api-segmentation-mcp) |
| webz-blogs-segmentation | https://seg-blogs-mcp.webz.io/mcp | [Webz.io Blogs Segmentation](https://docs.webz.io/docs/webz/blogs-api-segmentation-mcp) |
| webz-forums-segmentation | https://seg-forums-mcp.webz.io/mcp | [Webz.io Forums Segmentation](https://docs.webz.io/docs/webz/forums-api-segmentation-mcp) |

## Example prompts

- Find English news about renewable energy from the past week and include source links.
- Find forum discussions about electric vehicles from the past week.
- Which blogs discussed supply chain delays most in the past week?

Search tools return source records and excerpts; segmentation tools return counts. Coverage depends on the indexed sources, query, and account access. Use the live tool schemas for supported filters.

## Support and privacy

[Documentation](https://docs.webz.io/docs/webz) · [Privacy](https://webz.io/privacy/) · [Terms](https://webz.io/tos/)
