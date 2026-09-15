# Maintainer notes (not part of the Marketplace listing copy)

This is a Dify plugin, not a PyPI package. Users install it from
https://marketplace.dify.ai/ after a PR lands in langgenius/dify-plugins.

## Local checks

```bash
cd packages/dify
python -m pip install httpx pytest
PYTHONPATH=. python -m pytest tests -q
```

Live search (optional):

```bash
export WEBZ_API_TOKEN=...
PYTHONPATH=. python -m pytest tests/test_live.py -q
```

## Package

Install the Dify Plugin CLI, then from the directory above this plugin:

```bash
dify plugin package ./dify
```

That writes `dify.difypkg`. Rename it to `webz_news_search-0.1.0.difypkg`.

Validate if you have the marketplace toolkit:

```bash
python3 validator/validate-difypkg.py /path/to/webz_news_search-0.1.0.difypkg
```

## Marketplace PR

1. Fork https://github.com/langgenius/dify-plugins
2. Put a single file at `ori-webz/webz_news_search/webz_news_search-0.1.0.difypkg`
3. Open a PR to `main` in English, one package per PR
4. `author` in manifest.yaml must match the GitHub handle that opens the PR (`ori-webz`)
5. After merge, the plugin appears on marketplace.dify.ai automatically

Guide: https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-to-dify-marketplace

Risk level for the template: Medium (sends user queries to a third-party API).
Domains: `news-search-mcp.webz.io`
