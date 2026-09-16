from pathlib import Path

DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "dify_integration_doc.md"

REQUIRED_SNIPPETS = (
    "https://marketplace.dify.ai/plugin/ori-webz/webz_news_search",
    "https://marketplace.dify.ai/",
    "https://news-search-mcp.webz.io/mcp",
    "webz-news-search",
    "Do not prefix `Bearer`",
    "Use Dynamic Client Registration",
)

FORBIDDEN_SNIPPETS = (
    "After review",
    "Plugin not on Marketplace yet",
)


def test_dify_docs_page_is_live_and_complete() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    assert DOC_PATH.is_file(), f"missing {DOC_PATH}"
    for snippet in REQUIRED_SNIPPETS:
        assert snippet in text, f"docs missing {snippet!r}"
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in text, f"docs still has stale {snippet!r}"
