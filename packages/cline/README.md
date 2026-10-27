# Webz.io MCPs for Cline

Use seven hosted Webz.io MCP servers for news research, news/blog/forum searches, and field-value aggregation. The tools retrieve indexed content or counts; Webz.io hosts the servers. Setup adds remote connections to Cline.

You need a Webz.io account with the relevant product access and available credits, plus Cline and a configured model provider for tool use. Account coverage, history and usage limits apply. Queries can consume credits, including one credit per requested segmentation field.

## Add the connections

Follow Cline's [official MCP guide](https://docs.cline.bot/mcp/mcp-overview). In the IDE, open **MCP Servers → Configure → Configure MCP Servers**, then merge the entries below into the existing `mcpServers` object. Preserve other servers and any existing Webz OAuth state. Stop and review an existing entry with the same name instead of overwriting it.

The same JSON is in [mcp-settings.json](mcp-settings.json). Entries start disabled so you can enable and authorize one at a time. Set `disabled` to `false` only for the entry you are connecting. Use exactly `streamableHttp` as the transport type.

```json
{
  "mcpServers": {
    "webz-news-search": {
      "type": "streamableHttp",
      "url": "https://news-search-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-news": {
      "type": "streamableHttp",
      "url": "https://news-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-blogs": {
      "type": "streamableHttp",
      "url": "https://blogs-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-forums": {
      "type": "streamableHttp",
      "url": "https://forums-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-news-segmentation": {
      "type": "streamableHttp",
      "url": "https://seg-news-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-blogs-segmentation": {
      "type": "streamableHttp",
      "url": "https://seg-blogs-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    },
    "webz-forums-segmentation": {
      "type": "streamableHttp",
      "url": "https://seg-forums-mcp.webz.io/mcp",
      "disabled": true,
      "autoApprove": []
    }
  }
}
```

Cline's **Remote Servers** tab can also add one connection using its name, URL and **Streamable HTTP** transport from the table below.

## Authenticate one server at a time

Enable the first requested Webz entry and select **Authenticate** when Cline reports that authorization is required. Complete the browser OAuth flow, entering your dashboard API token only on the Webz.io consent page. Return to Cline and verify that the expected tool appears. Then connect another product your account can access.

For **Cline CLI 3.0.74**, the released package documents this interactive alternative (a terminal/TTY is required):

```sh
cline mcp install webz-news-search --transport http https://news-search-mcp.webz.io/mcp
```

The command opens the authentication wizard. Choose browser OAuth; leave static authorization headers unset. To authorize an already saved connection, run `cline mcp` and choose **Authorize OAuth**. Repeat with the other names/URLs only as needed. Cline's documented shared settings location is `~/.cline/data/settings/cline_mcp_settings.json`; `CLINE_MCP_SETTINGS_PATH` can select a different settings file.

Webz publishes OAuth discovery/dynamic registration and the `mcp` scope. Cline manages its own OAuth state. Keep API tokens, saved OAuth fields and model-provider credentials out of repository files and chat messages. This example has no secret header or automatic tool approval grant. Cline's global approval settings also apply; review each tool call and keep global MCP auto-approval off when manual approval is wanted.

OAuth discovery, registration and MCP calls share service rate limits. Avoid activating all seven connections together. If HTTP 429 occurs, stop all retries for at least ten minutes, then connect/retry one entry at a time.

## Servers and tools

| Product | Connection name | Hosted endpoint | Expected tool | Documentation |
| --- | --- | --- | --- | --- |
| Webz.io News Search | `webz-news-search` | `https://news-search-mcp.webz.io/mcp` | `news_search_by_webz` | [Guide](https://docs.webz.io/docs/webz/news-search-api-mcp) |
| Webz.io News | `webz-news` | `https://news-mcp.webz.io/mcp` | `search_webz_news` | [Guide](https://docs.webz.io/docs/webz/news-api-mcp) |
| Webz.io Blogs | `webz-blogs` | `https://blogs-mcp.webz.io/mcp` | `search_webz_blogs` | [Guide](https://docs.webz.io/docs/webz/blogs-api-mcp) |
| Webz.io Forums | `webz-forums` | `https://forums-mcp.webz.io/mcp` | `search_webz_discussions` | [Guide](https://docs.webz.io/docs/webz/forums-api-mcp) |
| Webz.io News Segmentation | `webz-news-segmentation` | `https://seg-news-mcp.webz.io/mcp` | `aggregate_webz_news` | [Guide](https://docs.webz.io/docs/webz/news-api-segmentation-mcp) |
| Webz.io Blogs Segmentation | `webz-blogs-segmentation` | `https://seg-blogs-mcp.webz.io/mcp` | `aggregate_webz_blogs` | [Guide](https://docs.webz.io/docs/webz/blogs-api-segmentation-mcp) |
| Webz.io Forums Segmentation | `webz-forums-segmentation` | `https://seg-forums-mcp.webz.io/mcp` | `aggregate_webz_forums` | [Guide](https://docs.webz.io/docs/webz/forums-api-segmentation-mcp) |

Tool schemas are discovered after connection; use the live tool arguments. News Search takes natural-language `query` and a result limit `k`. The other tools use Boolean `q`. Keep time windows and result limits in their separate arguments, and group OR alternatives.

## Verify tool use

Start with one small request per connected product. For example:

- News Search: one renewable-energy article from the past three days, with its source URL.
- News, Blogs or Forums: one result for `energy language:english` from the past three days, with its source URL. Preserve a missing title as unavailable.
- Each segmentation tool: aggregate `energy` over three days by a supported field such as `language`; show three returned buckets and their counts.

Check the actual tool name, arguments and result before describing setup as successful. A returned record page does not establish a corpus total. For aggregation, distinguish the number of buckets on the current page from a server-reported available total; do not treat a limited bucket sum as a document total. An empty result is valid. Report authentication, entitlement, credit and rate-limit failures separately.

For Cline-assisted setup, use [llms-install.md](llms-install.md) together with this guide.

## Privacy, support and license

Queries and filters are sent to Webz.io, and results are processed by Cline and its configured model provider. Third-party source content keeps its own rights and terms. Cite available source URLs and dates.

[Privacy](https://webz.io/privacy/) · [Service terms](https://webz.io/tos/) · [Support: support@webz.io](mailto:support@webz.io)

The [MIT license](LICENSE) covers this configuration and documentation only. Webz.io's hosted services, account entitlements/credits and third-party content remain subject to their applicable terms.
