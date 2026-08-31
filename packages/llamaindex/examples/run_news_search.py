"""
three LlamaIndex News Search examples.

usage:
  export WEBZ_API_TOKEN="your-token"
  export OPENROUTER_API_KEY="your-openrouter-key"   # only for example 2
  python examples/run_news_search.py

examples:
  1. direct tool call from WEBZ_API_TOKEN in the environment
  2. OpenRouter agent that uses the live Webz tool and answers from results
  3. developer-style call with api_token= in code
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback

from llama_index.tools.webz import WebzNewsSearch, flatten_tool_result
from llama_index.tools.webz.client import tool_arg_names

OPENROUTER_ENV_NAME = "OPENROUTER_API_KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"

DIRECT_QUERY = "How many goals does Cristiano have and how many left to 1000?"
AGENT_QUESTION = (
    "Call news_search_by_webz first with this query:\n"
    f'"{DIRECT_QUERY}"\n'
    "Use k=5. Then answer only from the returned articles:\n"
    "1. How many career goals does Cristiano Ronaldo have?\n"
    "2. How many goals is he short of 1000?\n"
    "3. When was his last goal, where, and against whom?\n"
    "Cite article titles and URLs."
)
DEV_QUERY = "recent developments on EU AI regulation"


def run_direct_from_env() -> None:
    print("=== 1. direct tool call (env token) ===")
    tool = WebzNewsSearch()
    print("tool name:", tool.metadata.name)
    print("live args from MCP tools/list:", sorted(tool_arg_names(tool)))
    print("query:", DIRECT_QUERY)
    print("---")
    print(flatten_tool_result(tool.call(query=DIRECT_QUERY, k=3)))
    print()


def run_openrouter_agent() -> None:
    print("=== 2. OpenRouter agent + Webz tools ===")
    api_key = os.getenv(OPENROUTER_ENV_NAME, "").strip()
    if not api_key:
        print(f"skip: set {OPENROUTER_ENV_NAME} to run the agent example.\n")
        return

    from llama_index.core.agent.workflow import FunctionAgent
    from llama_index.llms.openai_like import OpenAILike

    tool = WebzNewsSearch()
    llm = OpenAILike(
        model=OPENROUTER_MODEL,
        api_key=api_key,
        api_base=OPENROUTER_BASE_URL,
        is_chat_model=True,
        is_function_calling_model=True,
        context_window=131072,
        temperature=0.1,
    )
    agent = FunctionAgent(
        tools=[tool],
        llm=llm,
        system_prompt=(
            "You are a news research assistant. "
            "Always call the news_search_by_webz tool before answering. "
            "Pass a plain-language query and k between 3 and 10. "
            "Do not invent facts. Answer only from tool output."
        ),
    )
    print("model:", OPENROUTER_MODEL)
    print("question:", AGENT_QUESTION)
    print("--- running agent (may take a minute) ---")

    async def run_agent() -> str:
        # FunctionAgent.run() needs a live loop; do not call it before asyncio.run
        result = agent.run(AGENT_QUESTION)
        if hasattr(result, "__await__"):
            result = await result
        return str(result)

    response = asyncio.run(run_agent())
    print("--- final answer ---")
    print(response)
    print()


def run_direct_with_token_in_code() -> None:
    print("=== 3. developer call (token in code) ===")
    # prefer env; replace the string below only for a local one-off script
    token = os.getenv("WEBZ_API_TOKEN") or "paste-token-here"
    tool = WebzNewsSearch(api_token=token)
    result = tool.call(
        query=DEV_QUERY,
        k=5,
        days=30,
        language=["english"],
    )
    print("query:", DEV_QUERY)
    print("---")
    print(flatten_tool_result(result))
    print()


def main() -> None:
    steps = (
        run_direct_from_env,
        run_openrouter_agent,
        run_direct_with_token_in_code,
    )
    failed = False
    for step in steps:
        try:
            step()
        except Exception as exc:
            failed = True
            print(f"search failed in {step.__name__}: {exc}", file=sys.stderr)
            traceback.print_exc()
            print()
    if failed:
        raise SystemExit(1)
    print("SUCCESS ! End of examples")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
