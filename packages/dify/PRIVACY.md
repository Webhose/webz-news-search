# Privacy

This plugin connects Dify to the hosted Webz.io News Search MCP server (`https://news-search-mcp.webz.io/mcp`).

## Data sent to Webz.io

When you authorize the plugin or invoke the tool, the following is transmitted to `news-search-mcp.webz.io` over HTTPS:

- The Webz.io API token you configured in plugin credentials, sent as a Bearer token.
- For Authorize / credential checks: an MCP `initialize` handshake. This does not run a news search.
- For tool calls: the query and filters you (or the LLM) pass to `news_search_by_webz`.
- Standard HTTP metadata (User-Agent, IP address).

## Data Webz.io processes

Webz.io runs the news search against its global news index and returns ranked article excerpts (title, URL, published date, snippet, score, and related metadata). Usage is counted against your Webz.io plan, the same as the News Search API.

## Data retention

This plugin does not store search queries, tokens, or results on the plugin side beyond the Dify workspace credential store. Webz.io retains usage metrics tied to your token for billing and analytics. See the Webz.io privacy policy for how search data is processed.

## Third parties

The plugin does not call services other than `news-search-mcp.webz.io`. That server searches Webz.io's news index and may include publisher content in the result excerpts it returns.

## Full policy

See https://webz.io/privacy

## Contact

support@webz.io
