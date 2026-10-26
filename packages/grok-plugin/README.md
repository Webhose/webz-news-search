# Webz.io for Grok Build

This plugin connects Grok Build to seven hosted Webz.io MCP servers. Search news, blogs, and forum discussions, or aggregate matching content with the corresponding segmentation tools. Grok discovers tool schemas from the live servers; the plugin contains connection settings and does not implement search locally.

## Install

Install [Grok Build](https://docs.x.ai/build/overview), then install this plugin from Webz.io's public repository:

```sh
grok plugin install Webhose/webz-news-search#packages/grok-plugin --trust
grok plugin enable webz-io
```

Restart Grok Build, or reload plugins with `r` in the Plugins tab. The `--trust` option allows the plugin's MCP connections to load.

## Connect your account

You need a [Webz.io account](https://webz.io/) with access and credits for the products you use.

1. Open `/mcps` in Grok Build.
2. Select a Webz.io server and press `i` to authenticate.
3. Complete the Webz.io authorization page in your browser. If it asks for an API token, use the token from your Webz.io dashboard.
4. Repeat for the other products you want to use. Disable unused servers with `Space` in `/mcps`.

Grok handles OAuth discovery and stores the resulting credentials locally. No API token or OAuth client secret is included in this plugin. Authenticate one server at a time. If Webz.io returns HTTP 429, wait ten minutes before reconnecting; repeated retries during the block will not help.

## Servers and network access

The plugin connects only to these HTTPS MCP endpoints. OAuth uses the authorization endpoints advertised by each server.

| Grok server name | MCP endpoint | Tool | Documentation |
| --- | --- | --- | --- |
| `webz-news-search` | `https://news-search-mcp.webz.io/mcp` | `news_search_by_webz` | [News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) |
| `webz-news` | `https://news-mcp.webz.io/mcp` | `search_webz_news` | [News](https://docs.webz.io/docs/webz/news-api-mcp) |
| `webz-blogs` | `https://blogs-mcp.webz.io/mcp` | `search_webz_blogs` | [Blogs](https://docs.webz.io/docs/webz/blogs-api-mcp) |
| `webz-forums` | `https://forums-mcp.webz.io/mcp` | `search_webz_discussions` | [Forums](https://docs.webz.io/docs/webz/forums-api-mcp) |
| `webz-news-segmentation` | `https://seg-news-mcp.webz.io/mcp` | `aggregate_webz_news` | [News Segmentation](https://docs.webz.io/docs/webz/news-api-segmentation-mcp) |
| `webz-blogs-segmentation` | `https://seg-blogs-mcp.webz.io/mcp` | `aggregate_webz_blogs` | [Blogs Segmentation](https://docs.webz.io/docs/webz/blogs-api-segmentation-mcp) |
| `webz-forums-segmentation` | `https://seg-forums-mcp.webz.io/mcp` | `aggregate_webz_forums` | [Forums Segmentation](https://docs.webz.io/docs/webz/forums-api-segmentation-mcp) |

Queries and filters are sent to Webz.io. Results are returned to Grok Build and its configured model provider. Calls may consume Webz.io credits; available data and access depend on your account. This package adds no scripts, local processes, hooks, filesystem tools, or telemetry.

## Try it

After authenticating the relevant server, ask Grok Build:

- "Use Webz.io News Search to find three recent articles about renewable energy. Include each headline and source URL."
- "Use Webz.io Blogs to find posts about electric vehicles."
- "Use Webz.io Forums to find discussions about battery recycling."
- "Use Webz.io News Segmentation to group matching articles about renewable energy by language."

News Search uses semantic queries. The News, Blogs, Forums, and segmentation tools use the Webz.io query syntax and filters documented for each product. News Search covers the last 30 days. Tool output can contain third-party content; evaluate the sources before relying on it.

## Check the connection

```sh
grok plugin details webz-io
grok inspect --json
grok mcp doctor webz-news-search
```

Run connection checks one server at a time to avoid a burst of requests. Grok Build's `mcp list` command lists manually configured servers and can omit plugin connections; use `/mcps` and the named doctor check for this plugin. If a tool is missing, confirm the plugin is enabled and trusted, authenticate the server in `/mcps`, and reload the MCP list.

[Webz.io privacy policy](https://webz.io/privacy/) · [Webz.io terms](https://webz.io/tos/) · [Support](mailto:support@webz.io)

## License

The plugin configuration and documentation are licensed under the [MIT License](LICENSE). Webz.io's hosted services and third-party source content remain subject to their applicable terms.

