# SPDX-FileCopyrightText: 2026-present Webz.io <support@webz.io>
#
# SPDX-License-Identifier: MIT

from haystack import Pipeline

from haystack_integrations.components.websearch.webz import WebzWebSearch

pipeline = Pipeline()
pipeline.add_component(
    "news",
    WebzWebSearch(top_k=5, days=7, language=["english"]),
)
result = pipeline.run({"news": {"query": "recent developments on EU AI regulation"}})

for document in result["news"]["documents"]:
    print(document.meta.get("title"))
    print(document.meta.get("url"))
    print(document.content)
