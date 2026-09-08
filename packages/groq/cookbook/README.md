# Contribution to groq/groq-api-cookbook

Tutorial submission for the Webz.io News Search MCP server, so it can be listed
on Groq's [integrations catalog](https://console.groq.com/docs/integrations)
next to Tavily, Exa, and Firecrawl.

- Upstream repo: [groq/groq-api-cookbook](https://github.com/groq/groq-api-cookbook)
- Contribution guide: [CONTRIBUTING.md](https://github.com/groq/groq-api-cookbook/blob/main/CONTRIBUTING.md)
- Issue: _not opened yet_
- Pull request: _not opened yet_

## Contents

New file, at its upstream path:

```
tutorials/03-mcp/mcp-webz/mcp-webz.ipynb
```

The `03-mcp` tutorials are one notebook per directory with no extra files, so
this bundle matches that shape. The root `README.md` also needs a line in the
`03. Model Context Protocol (MCP)` list:

```markdown
- [Webz.io MCP with Groq](/tutorials/03-mcp/mcp-webz): Search global news with structured filters using the Webz.io MCP and Groq API.
```

## Notebook structure

Modeled on [`mcp-tavily.ipynb`](https://github.com/groq/groq-api-cookbook/blob/main/tutorials/03-mcp/mcp-tavily/mcp-tavily.ipynb),
which is the reference for a search-provider MCP tutorial:

1. Three-step intro, then getting-started keys
2. Model selection (`openai/gpt-oss-120b`)
3. Step 1 — Groq client
4. Step 2 — Webz.io remote MCP server definition
5. Step 3 — `connect_groq_to_webz()` plus `print_mcp_calls()`
6. Four demos: unfiltered research, sentiment + ticker filters, regional comparison, try-it-yourself
7. Troubleshooting, challenge, and resources

## Differences from the Tavily notebook

- **Auth is a Bearer header, not a URL query parameter.** Tavily and Exa accept
  `?tavilyApiKey=` / `?exaApiKey=`; Webz.io does not, and tokens in URLs leak
  into logs and referrers. The notebook follows the
  [HuggingFace tutorial](https://console.groq.com/docs/huggingface) pattern
  instead: `"headers": {"Authorization": f"Bearer {WEBZ_API_TOKEN}"}`.
- **`server_description` and `allowed_tools` are set.** The server exposes one
  tool, `news_search_by_webz`. The description steers the model toward news
  search rather than generic web search.
- **Base URL is `https://api.groq.com/openai/v1`**, matching Groq's
  [remote MCP docs](https://console.groq.com/docs/tool-use/remote-mcp). The
  Tavily notebook uses `https://api.groq.com/api/openai/v1` and passes the
  literal string `"GROQ_API_KEY"` as the key, which we did not copy.
- **`connect_groq_to_webz()` also returns `tools_discovered`**, read from the
  `mcp_list_tools` output item, so the reader can see the live `tools/list`
  result.
- **Demos are filter-driven.** Webz.io's differentiator is structured news
  metadata (sentiment, ticker, country, political bias, entities), so the demos
  exercise those filters rather than scraping and crawling.
- **`load_dotenv()` is called** so the `.env` written in the first cell is
  actually read in the same session.

## Checks run before opening the PR

```bash
python -c "import json; json.load(open('mcp-webz/mcp-webz.ipynb'))"   # valid notebook JSON
python - <<'PY'                                                       # every code cell parses
import ast, json
nb = json.load(open("mcp-webz/mcp-webz.ipynb"))
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if cell["cell_type"] == "code" and "!echo" not in src:
        ast.parse(src)
PY
```

Outputs are stripped from the committed notebook. Re-run it end to end with a
live `WEBZ_API_TOKEN` and `GROQ_API_KEY` before submitting, and confirm each
demo reports at least one `news_search_by_webz` call.

## After the PR merges

Ask Groq for a docs page at `console.groq.com/docs/webz` and a card in the
**MCP Integration** section of the
[integrations catalog](https://console.groq.com/docs/integrations). That page
is the Groq-side equivalent of
[`console.groq.com/docs/tavily`](https://console.groq.com/docs/tavily); the
Webz-side copy lives in
[`docs/groq_integration_doc.md`](../../../docs/groq_integration_doc.md).
