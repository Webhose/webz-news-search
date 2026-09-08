"""
Filter-steered Webz news research on Groq.

usage:
  export WEBZ_API_TOKEN="your-webz-token"
  export GROQ_API_KEY="your-groq-key"
  python examples/run_research_agent.py

Groq reads the live filter schema from MCP tools/list, so the prompt can name
filters directly (days, sentiment, ticker, language, country) and the model
passes them through to news_search_by_webz.
"""

from __future__ import annotations

import os
import sys
import time

from openai import OpenAI

from webz_groq import (
    DEFAULT_MODEL,
    GROQ_BASE_URL,
    GROQ_TOKEN_ENV_NAME,
    PREFERRED_TOOL_NAME,
    build_webz_mcp_tool,
    extract_mcp_calls,
    format_mcp_calls,
)

SYSTEM_PROMPT = (
    "You are a news research assistant. "
    f"Always call {PREFERRED_TOOL_NAME} before answering. "
    "Answer only from tool output, and cite each claim with the article title and URL."
)

DEMOS = {
    "negative coverage, last 7 days": (
        "Find negative coverage about Boeing from the last 7 days. "
        f"Call {PREFERRED_TOOL_NAME} with sentiment negative, days 7, "
        "language english, k 10. List headline, publisher, date, and URL."
    ),
    "ticker research": (
        "What are analysts saying about Nvidia earnings? "
        f"Call {PREFERRED_TOOL_NAME} with ticker NVDA, days 7, k 5. "
        "Summarize the consensus and cite sources."
    ),
    "regional comparison": (
        "Compare EU and US coverage of AI regulation over the past 30 days. "
        f"Call {PREFERRED_TOOL_NAME} twice: once with country DE and FR, "
        "once with country US, both with days 30 and k 5. "
        "Contrast the framing in each region."
    ),
}


def run_demo(client: OpenAI, tools: list[dict], title: str, prompt: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    started = time.time()
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        tools=tools,
        temperature=0.1,
        top_p=0.4,
    )
    calls = extract_mcp_calls(response)
    print(f"took {time.time() - started:.1f}s")
    print(format_mcp_calls(calls, output_chars=200))
    print("--- answer ---")
    print(response.output_text)


def main() -> None:
    groq_key = os.getenv(GROQ_TOKEN_ENV_NAME)
    if not groq_key:
        raise SystemExit(f"set {GROQ_TOKEN_ENV_NAME} (https://console.groq.com/keys)")

    client = OpenAI(base_url=GROQ_BASE_URL, api_key=groq_key)
    tools = [build_webz_mcp_tool()]

    for title, prompt in DEMOS.items():
        run_demo(client, tools, title, prompt)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"research agent failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
