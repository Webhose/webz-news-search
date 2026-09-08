# Contribution to groq/groq-api-cookbook

Tutorial submission for the Webz.io News Search MCP server, and the first step
toward a listing on Groq's
[integrations catalog](https://console.groq.com/docs/integrations) next to
Tavily, Exa, and Firecrawl.

- Upstream repo: [groq/groq-api-cookbook](https://github.com/groq/groq-api-cookbook)
- Contribution guide: [CONTRIBUTING.md](https://github.com/groq/groq-api-cookbook/blob/main/CONTRIBUTING.md)
- Branch: [`ShakedDegani/groq-api-cookbook:feat/mcp-webz-tutorial`](https://github.com/ShakedDegani/groq-api-cookbook/tree/feat/mcp-webz-tutorial)
- Pull request: _not opened yet — the notebook still needs an end-to-end run with saved outputs_

## Contents

New file, at its upstream path:

```
tutorials/03-mcp/mcp-webz/mcp-webz.ipynb
```

The `03-mcp` tutorials are one notebook per directory with no extra files, so
this bundle matches that shape. The root `README.md` gets one line appended to
the `03. Model Context Protocol (MCP)` list:

```markdown
- [Webz.io MCP with Groq](/tutorials/03-mcp/mcp-webz): Search global news with the Webz.io MCP and Groq API, filtering by sentiment, ticker, country, and other article metadata.
```

`build_notebook.py` generates the notebook, so this bundle and the branch on the
fork cannot drift:

```bash
python build_notebook.py mcp-webz/mcp-webz.ipynb
```

## Notebook structure

Modeled on [`mcp-tavily.ipynb`](https://github.com/groq/groq-api-cookbook/blob/main/tutorials/03-mcp/mcp-tavily/mcp-tavily.ipynb)
and [`mcp-firecrawl.ipynb`](https://github.com/groq/groq-api-cookbook/blob/main/tutorials/03-mcp/mcp-firecrawl/mcp-firecrawl.ipynb),
which are the reference shape for a search-provider MCP tutorial:

1. Three-step intro, dependency install, then getting-started keys
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
- **Keys load from Colab `userdata` with a `.env` fallback**, matching the
  HuggingFace tutorial, so the notebook runs unchanged in Colab.

## Meeting the contribution rubric

`CONTRIBUTING.md` scores submissions on usefulness, originality, clarity,
accuracy, depth, and grammar. Scoring below 3 in any one area is likely to be
rejected. Two of those need active design work:

- **Originality** is the real risk, because `mcp-tavily` and `mcp-exa` already
  cover search over MCP. The defensible angle is that Webz.io is a licensed
  news index rather than open-web search, so the notebook leads with the
  structured article metadata and never demonstrates scraping or crawling.
- **Accuracy** is graded on working code, so the notebook must be executed end
  to end with outputs saved before the PR is opened. That needs a real Groq key
  (`gsk_` prefix, from [console.groq.com/keys](https://console.groq.com/keys)).

The guide also asks for a **neutral** tone on tools and products. The notebook
is written as a Groq tutorial that happens to use Webz.io, not as Webz.io
marketing.

## Checks run before opening the PR

```bash
python -c "import json; json.load(open('mcp-webz/mcp-webz.ipynb'))"   # valid notebook JSON
python - <<'PY'                                                       # every code cell parses
import ast, json
nb = json.load(open("mcp-webz/mcp-webz.ipynb"))
for cell in nb["cells"]:
    src = "".join(cell["source"])
    lines = cell["source"]
    is_magic = any(line.lstrip().startswith(("!", "%")) for line in lines)
    if cell["cell_type"] == "code" and not is_magic:
        ast.parse(src)
PY
```

Still to do: run the notebook end to end with a live `WEBZ_API_TOKEN` and
`GROQ_API_KEY`, confirm every demo reports at least one `news_search_by_webz`
call, and commit the executed outputs.

## Getting the catalog listing

The cookbook PR is necessary but **not sufficient**, and it is the only part of
this that is self-serve.

- `console.groq.com/docs` is not open source. The "Suggest Edits" control on a
  docs page is an in-app button, not a link to a GitHub repo, and there is no
  public docs repository. A `console.groq.com/docs/webz` page has to be written
  and published by Groq.
- Every MCP card in the catalog has a matching docs page: `tavily`, `exa`,
  `firecrawl`, `huggingface`, `parallel`, `browserbase`, `browseruse`,
  `mastra`, and `e2b` all resolve. Most of those companies were named as
  **launch partners** in Groq's remote-MCP beta changelog, so their pages came
  out of a coordinated launch rather than a community submission.
- Box is the counterexample worth knowing: it has a merged tutorial at
  `tutorials/03-mcp/mcp-box`, but `console.groq.com/docs/box` returns 404. A
  merged tutorial on its own does not produce a catalog page.

So the sequence is: merge the tutorial first, then ask, using the merged
tutorial as evidence the integration works. The only contact surface published
on the docs pages is [groq.com/contact](https://groq.com/contact); there is no
public partner application form. Ask for a page at
`console.groq.com/docs/webz` and a card in the **MCP Integration** section of
the catalog. That page would be the Groq-side equivalent of
[`console.groq.com/docs/tavily`](https://console.groq.com/docs/tavily); the
Webz-side copy already exists in
[`docs/groq_integration_doc.md`](../../../docs/groq_integration_doc.md).

Unrelated to Groq but worth doing in parallel: publishing the server to the
official MCP registry at `registry.modelcontextprotocol.io` gets it ingested by
PulseMCP, Smithery, and client-side directories automatically.
