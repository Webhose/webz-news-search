# Upstream contribution to crewAIInc/crewAI

`WebzioNewsSearchTool` has been submitted to the official tool catalog:

- Issue: [crewAIInc/crewAI#7308](https://github.com/crewAIInc/crewAI/issues/7308)
- Pull request: [crewAIInc/crewAI#7309](https://github.com/crewAIInc/crewAI/pull/7309)
- Branch: [`ShakedDegani/crewAI:feat/webzio-news-search-tool`](https://github.com/ShakedDegani/crewAI/tree/feat/webzio-news-search-tool)

This directory is a record of exactly what was submitted, so the upstream tool
and the standalone [`crewai-webzio`](https://pypi.org/project/crewai-webzio/)
package can be kept in sync.

## Contents

New files, at their upstream paths:

```
lib/crewai-tools/src/crewai_tools/tools/webzio_tools/webzio_news_search_tool.py
lib/crewai-tools/tests/tools/webzio_news_search_tool_test.py
docs/edge/{en,ar,ko,pt-BR}/tools/search-research/webzionewssearchtool.mdx
```

`existing-files.patch` holds the edits to files that already existed upstream:
the two `__init__.py` export lists, the four Search & Research `overview.mdx`
card groups, the `docs.json` nav entries, and the regenerated
`tool.specs.json` entry.

## Differences from the standalone package

The upstream tool is not a copy of `packages/crewai/crewai_webzio/tool.py`.
The differences were driven by upstream conventions and CI:

- `MCPServerAdapter` is imported from `crewai_tools.adapters.mcp_adapter`
  rather than from `crewai_tools`.
- `api_token`, `mcp_url` and `connect_timeout` are Pydantic fields with
  env-var default factories, not init-only arguments. `ToolSpecExtractor`
  reads `model_json_schema`, so only real fields reach
  `tool.specs.json`'s `init_params_schema`.
- The agent-facing `name` is `"Webzio News Search"`, matching the catalog
  convention ("Brave News Search", "Tavily Search"), rather than the
  MCP-native `news_search_by_webz`.
- Construction never raises on a connection failure. It falls back to the
  `query`-only schema and retries on the first search. The repo runs pytest
  with `--block-network`, and tools are commonly built at import time, so an
  eager `RuntimeError` from `MCPServerAdapter.__init__` was not acceptable.
- The class-level `description` is kept as authored instead of adopting the
  live MCP tool's description, because `CrewAIToolAdapter` rewrites that into
  a `Tool Name: ... / Tool Arguments: ... / Tool Description: ...` composite.
  Only `args_schema` is adopted from the server; `BaseTool.formatted_description`
  recombines it for the LLM at prompt time.
- `_connect()` and `stop()` share a `threading.Lock`; setup uses a local
  `MCPServerAdapter` and closes it on handshake failure so concurrent searches
  cannot leak duplicate MCP sessions.
- The MCP endpoint must be an absolute `https://` URL so the Bearer token is
  not sent in cleartext.

## CodeRabbit review fixes (commit `0cdbbe4`)

Addressed the three actionable review comments on [#7309](https://github.com/crewAIInc/crewAI/pull/7309):

- Serialized the MCP lifecycle with a lock and local adapter setup.
- Rejected non-HTTPS MCP endpoints before sending the token.
- Rewrote the docs examples in all four locales to use the context manager for
  exception-safe cleanup.
- Added test docstrings and two new tests (concurrency, cleartext endpoint).

## Checks run before opening the PR

```bash
uv run pytest lib/crewai-tools/tests/tools/webzio_news_search_tool_test.py   # 17 passed
uv run ruff check lib/                                                       # All checks passed
uv run ruff format --check lib/                                              # 919 files already formatted
uv run mypy lib/crewai-tools/src/crewai_tools/tools/webzio_tools/            # Success
cd lib/crewai-tools && uv run python src/crewai_tools/generate_tool_specs.py
```

`tool.specs.json` is regenerated and committed by hand because
`generate-tool-specs.yml` is gated on
`head.repo.full_name == github.repository` and does not run for fork PRs.

A live check against the production MCP server adopted 26 filter fields and
returned results.
