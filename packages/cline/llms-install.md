# Install the Webz.io remote MCP bundle in Cline

These instructions apply only when the user asks to install or connect this Webz.io bundle. Read README.md for the complete seven-server JSON, endpoint/tool table, authentication and verification examples.

1. Use Cline's own MCP settings or Remote Servers interface. The servers are already hosted by Webz.io; add HTTPS remote connections with type `streamableHttp`.
2. Merge the provided `mcpServers` entries without replacing unrelated settings. If a connection name already exists, preserve its OAuth state and review the difference before making a change.
3. Keep new entries disabled initially. Enable one requested connection, complete browser OAuth with the user's participation, then verify its expected tool before enabling another. The user enters the Webz dashboard token only on the Webz consent page.
4. Leave static token headers unset and `autoApprove` empty. Preserve the user's global approval preferences; do not enable broad approval or bypass prompts to finish setup. Do not save credentials in this repository or print OAuth values.
5. In Cline CLI 3.0.74, `cline mcp install NAME --transport http URL` opens an interactive auth wizard; `cline mcp` also offers Authorize OAuth for saved servers. Both the connection names and URLs are in README.md.
6. Run a small, user-approved request through each product being installed and inspect actual tool execution/results. Saving JSON, seeing a connected status or passing another client's test is not sufficient evidence of Cline tool use. Report only the servers actually checked.
7. For records, preserve source URLs and missing metadata. For segmentation, distinguish returned page buckets from reported available buckets and document totals. Use the live schema rather than inventing arguments.
8. If HTTP 429 appears, stop every retry for at least ten minutes, then resume one connection at a time. Report unresolved OAuth, access, credit or model-provider failures accurately.

Retain the user's other connections and provider configuration. Remove only a Webz entry the user specifically asks to remove. See README.md for privacy, support, credits and service terms.
