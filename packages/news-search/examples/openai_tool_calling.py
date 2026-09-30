"""
use the News Search API as a function tool with the OpenAI chat completions API.

usage:
  pip install webzio-news-search openai
  export WEBZ_API_TOKEN="your-token"
  export OPENAI_API_KEY="your-key"
  python examples/openai_tool_calling.py
"""

from __future__ import annotations

import json
import sys

from openai import OpenAI

from webzio_news_search import TOOL_NAME, WebzNewsSearch

MODEL = "gpt-4.1-mini"
PROMPT = "Find recent news about renewable energy investments in Germany and summarize with sources."


def main() -> None:
    openai_client = OpenAI()
    tools = [WebzNewsSearch.openai_tool_definition()]
    messages: list[dict] = [{"role": "user", "content": PROMPT}]

    with WebzNewsSearch() as news:
        for _ in range(4):
            completion = openai_client.chat.completions.create(
                model=MODEL, messages=messages, tools=tools
            )
            message = completion.choices[0].message
            if not message.tool_calls:
                print(message.content)
                return
            messages.append(message)
            for call in message.tool_calls:
                if call.function.name != TOOL_NAME:
                    continue
                print("tool call:", call.function.arguments)
                result = news.run_tool(call.function.arguments)
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": result}
                )
    print("model did not finish within the tool-call budget", file=sys.stderr)


if __name__ == "__main__":
    main()
