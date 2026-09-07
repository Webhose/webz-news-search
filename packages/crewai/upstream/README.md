# Upstream contribution to crewAIInc/crewAI

This directory contains files ready to copy into a PR against [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI).

## PR checklist

1. Copy `lib/crewai-tools/src/crewai_tools/tools/webzio_tools/webzio_news_search_tool.py` into the fork.
2. Add to `lib/crewai-tools/src/crewai_tools/tools/__init__.py`:
   ```python
   from crewai_tools.tools.webzio_tools.webzio_news_search_tool import (
       WebzioNewsSearchTool,
   )
   ```
   and add `"WebzioNewsSearchTool"` to `__all__`.
3. Add to `lib/crewai-tools/src/crewai_tools/__init__.py` the same import and export.
4. Copy `lib/crewai-tools/tests/tools/webzio_news_search_tool_test.py`.
5. Copy `docs/en/tools/search-research/webzionewssearchtool.mdx`.
6. Add a card to `docs/en/tools/search-research/overview.mdx` (Search & Research section).
7. Register the page in the docs nav (`docs.json` or equivalent Mintlify config).
8. Regenerate tool specs:
   ```bash
   cd lib/crewai-tools
   python -m crewai_tools.generate_tool_specs
   ```
9. Run tests:
   ```bash
   pytest lib/crewai-tools/tests/tools/webzio_news_search_tool_test.py
   ```

No new vendor SDK dependency is required — the tool uses the existing `mcp` extra via `MCPServerAdapter`.

## Suggested PR title

`feat(tools): add WebzioNewsSearchTool for Webz.io news search via MCP`

## Suggested PR description

- Adds `WebzioNewsSearchTool` wrapping the hosted Webz News Search MCP server
- Filter schema loaded live from MCP `tools/list` (not hardcoded)
- Auth via `WEBZ_API_TOKEN` (Bearer) and optional `WEBZ_MCP_URL`
- Docs page under Search & Research, modeled on ExaSearchTool
- Unit tests mock `MCPServerAdapter` (no live token in CI)

Maintained by Webz.io. Standalone PyPI package: [crewai-webzio](https://pypi.org/project/crewai-webzio/).
