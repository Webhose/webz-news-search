# Webz.io for Kiro

Research public web coverage with seven hosted Webz.io MCP servers. This Power combines semantic news research, structured news/blog/forum searches, and three segmentation tools for content counts.

## Install

Use a current [Kiro release that supports Agent Plugins Powers](https://kiro.dev/docs/powers/installation/).

1. Clone or download [Webz.io's public integrations repository](https://github.com/Webhose/webz-news-search).
2. In Kiro, open **Powers → Add Custom Power → Import power from a folder**.
3. Select `packages/kiro-power`, the directory containing this Power's `plugin.json`.
4. Review and install **webz-io**. Mention Webz.io, news research, blog research, or forum research to activate it.

Kiro also supports **Import power from GitHub** using the repository URL. The Power is in `packages/kiro-power`; see Kiro's [installation guide](https://kiro.dev/docs/powers/installation/) for repository discovery and supported clients.

## Connect Webz.io

You need a [Webz.io account](https://webz.io/) with the relevant product access and available credits.

When a Webz connection needs authentication, complete Kiro's browser-based OAuth flow. Enter your Webz.io API token on the Webz.io authorization page when requested. Authenticate the products you use one at a time.

OAuth discovery, consent, scopes, and credential storage are managed by Kiro. Webz.io authorization uses the `mcp` scope. This Agent Plugins package contains only public connection URLs; the portable format does not declare OAuth credentials or scopes. If authentication reports a scope error, refer to Kiro's [client-managed OAuth configuration](https://kiro.dev/docs/mcp/configuration/#oauth-authentication).

OAuth discovery and registration share Webz.io's MCP rate limits. Multiple bundled connections may initialize together during installation. If OAuth setup returns HTTP 429, stop all retries for at least ten minutes. Then use Kiro's **MCP Servers** panel to choose **Authenticate** or **Retry** for one Webz.io entry at a time.

The package contains no API token, secret header, credential file, or automatic tool approval. Kiro manages the connections with Power activation and deactivation. Its installed server names are namespaced, for example `webz-news-search` may appear as `power-webz-io-webz-news-search`.

## Choose a tool

| Product | Server | Tool | Guide |
| --- | --- | --- | --- |
| Semantic news research | `webz-news-search` | `news_search_by_webz` | [News Search](https://docs.webz.io/docs/webz/news-search-api-mcp) |
| Structured news search | `webz-news` | `search_webz_news` | [News](https://docs.webz.io/docs/webz/news-api-mcp) |
| Blog search | `webz-blogs` | `search_webz_blogs` | [Blogs](https://docs.webz.io/docs/webz/blogs-api-mcp) |
| Forum and discussion search | `webz-forums` | `search_webz_discussions` | [Forums](https://docs.webz.io/docs/webz/forums-api-mcp) |
| News counts and distributions | `webz-news-segmentation` | `aggregate_webz_news` | [News Segmentation](https://docs.webz.io/docs/webz/news-api-segmentation-mcp) |
| Blog counts and distributions | `webz-blogs-segmentation` | `aggregate_webz_blogs` | [Blogs Segmentation](https://docs.webz.io/docs/webz/blogs-api-segmentation-mcp) |
| Forum counts and distributions | `webz-forums-segmentation` | `aggregate_webz_forums` | [Forums Segmentation](https://docs.webz.io/docs/webz/forums-api-segmentation-mcp) |

The `webz-research` skill routes record searches; `webz-segmentation` handles counts and bucket pagination. Tool schemas are discovered from the hosted servers at runtime.

News Search accepts a natural-language `query`. The other tools accept Boolean `q` expressions and field filters; put time windows and result limits in their separate tool arguments. Group alternatives, for example `("electric vehicle" OR "electric vehicles") language:english`. News Search covers the indexed 30-day window; product coverage and limits depend on the connected account.

## Try it

After connecting the relevant product, ask Kiro:

- "Use Webz.io News Search to find two recent renewable-energy articles. Include headlines and source URLs."
- "Use Webz.io News to find two English articles about battery recycling from the past seven days."
- "Use Webz.io Blogs to find two posts about electric vehicles and include their source URLs."
- "Use Webz.io Forums to find two discussions about battery recycling and include their source URLs."
- "Use Webz.io News Segmentation to group renewable-energy coverage by language over the past seven days. Show three buckets and counts."
- "Use Webz.io Blogs Segmentation to group electric-vehicle coverage by language over the past seven days. Show three buckets and counts."
- "Use Webz.io Forums Segmentation to group battery-recycling discussions by language over the past seven days. Show three buckets and counts."

Start with small result sets and make requests serially. Calls may consume Webz.io credits; segmentation can consume one credit per requested field. An empty response is a valid outcome. Authentication failures, unavailable product access, insufficient credits, and rate-limit errors should be reported separately. If HTTP 429 occurs, wait ten minutes before retrying.

## Data and network access

The Power connects over Streamable HTTP to these HTTPS origins:

- `https://news-search-mcp.webz.io/mcp`
- `https://news-mcp.webz.io/mcp`
- `https://blogs-mcp.webz.io/mcp`
- `https://forums-mcp.webz.io/mcp`
- `https://seg-news-mcp.webz.io/mcp`
- `https://seg-blogs-mcp.webz.io/mcp`
- `https://seg-forums-mcp.webz.io/mcp`

OAuth uses the Webz.io authorization endpoints advertised by those servers. Queries and filters are sent to Webz.io; returned records and counts are processed by Kiro and its configured model provider. This package adds no executable scripts, local server processes, hooks, or telemetry.

Returned material comes from third-party sources. Cite source URLs when available and evaluate those sources before relying on their content. Keep credentials and account details out of prompts and shared results.

[Privacy Policy](https://webz.io/privacy/) · [Terms of Service](https://webz.io/tos/) · [Support: support@webz.io](mailto:support@webz.io)

## License

Only this Power's configuration, skills, and documentation are distributed under the [MIT License](LICENSE). The license does not grant access to Webz.io's hosted services or rights to third-party source content; their respective terms and the account's credits and entitlements apply.
