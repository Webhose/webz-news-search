from __future__ import annotations

import os

import pytest

from ag2_webzio import WebzioNewsSearchToolkit
from ag2_webzio.consts import PREFERRED_TOOL_NAME

pytestmark = pytest.mark.skipif(
    not os.getenv("WEBZ_API_TOKEN"),
    reason="WEBZ_API_TOKEN is not set",
)


@pytest.mark.asyncio
async def test_live_toolkit_discovers_news_search_tool() -> None:
    toolkit = WebzioNewsSearchToolkit()
    schemas = await toolkit.schemas(context=None)  # type: ignore[arg-type]
    names = [schema.function.name for schema in schemas]
    assert PREFERRED_TOOL_NAME in names
