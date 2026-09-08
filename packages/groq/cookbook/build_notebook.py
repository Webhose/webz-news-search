"""Generate the mcp-webz cookbook notebook for groq-api-cookbook."""

import json
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1])

cells = []


def md(text: str) -> None:
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")})


def code(text: str) -> None:
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": text.strip("\n"),
        }
    )


md("""
# Groq + Webz.io MCP: Real-Time News Search

This notebook is for Python developers who want Groq models to answer from **current news** instead of training data. Webz.io indexes news and current events from sources worldwide, and exposes semantic search over that index through a Model Context Protocol (MCP) server. Unlike open-web search, every result is a news article with structured metadata: publisher, publish date, sentiment, entities, tickers, and source political bias.

We will achieve this through three simple steps:
1. Set up the **Groq MCP client** for fast inference.
2. Set up the **Webz.io MCP server** for global news search.
3. Seamlessly **connect the client to the server** through the Responses API.

---
""")

code("""
# install dependencies
%pip install openai python-dotenv ipython
""")

md("""
## Getting Started

Follow these steps to set up:
1. **Sign up** for Groq at [console.groq.com](https://console.groq.com/keys) to get your free API key.
2. **Sign up** for Webz.io at [webz.io](https://webz.io) to get your API token.
3. **Copy your API keys** from your Groq and Webz.io account dashboards.
4. **Paste your API keys** into the cell below and run the cell.
""")

code("""
# To export your API keys into a .env file, run the following cell (replace with your actual keys):
!echo "GROQ_API_KEY=<your-groq-api-key>" >> .env
!echo "WEBZ_API_TOKEN=<your-webz-api-token>" >> .env
""")

code("""
import json
import os
import time

# Read the keys from Colab secrets when available, otherwise from .env
try:
    from google.colab import userdata

    GROQ_API_KEY = userdata.get("GROQ_API_KEY")
    WEBZ_API_TOKEN = userdata.get("WEBZ_API_TOKEN")
except ImportError:
    from dotenv import load_dotenv

    load_dotenv()

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEBZ_API_TOKEN = os.getenv("WEBZ_API_TOKEN")

# Check if API keys are set
if not GROQ_API_KEY:
    print("Please set your Groq API key")
else:
    print("Groq API key configured successfully!")
if not WEBZ_API_TOKEN:
    print("Please set your Webz.io API token")
else:
    print("Webz.io API token configured successfully!")
""")

md("""
Select the foundation model to power inference. Let's try OpenAI's flagship open-weight MoE model, [gpt-oss-120b](https://console.groq.com/docs/model/openai/gpt-oss-120b), available via Groq for fast inference.
""")

code("""
# Model configuration
MODEL = "openai/gpt-oss-120b"
""")

md("""
## Step 1: Set up the Groq client
""")

code("""
from openai import OpenAI

# set up Groq MCP client
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
""")

md("""
## Step 2: Set up Webz.io's remote MCP server

The server exposes a single tool, `news_search_by_webz`. Groq reads its schema from `tools/list` at request time, so every filter Webz.io supports is available to the model without changing this notebook.

Note the authentication: Webz.io takes the token in an `Authorization` header, **not** as a URL query parameter. Groq handles these headers securely and redacts them from logs.
""")

code("""
# set up Webz.io MCP server
tools = [
    {
        "type": "mcp",
        "server_label": "webzio-news-search",
        "server_url": "https://news-search-mcp.webz.io/mcp",
        "server_description": (
            "Webz.io contextual news search. Semantic search over a global news index. "
            "Use it for current events, company and market coverage, and anything that "
            "needs recent articles. Filter by language, country, days, sentiment, "
            "category, domain, topic, person, organization, location, and ticker."
        ),
        "headers": {"Authorization": f"Bearer {WEBZ_API_TOKEN}"},
        "require_approval": "never",
        "allowed_tools": ["news_search_by_webz"],
    }
]
""")

md("""
## Step 3: Connect Groq to the Webz.io MCP through Groq's OpenAI-compatible Responses API
""")

code('''
def connect_groq_to_webz(client, tools, query):
    """
    Connect Groq client to the Webz.io MCP server through the Responses API.

    This function demonstrates the speed and accuracy of combining:
    - Groq's fast LLM inference
    - Webz.io's MCP server for global news retrieval
    """

    start_time = time.time()

    # Call Groq with Webz.io MCP integration using the responses API
    response = client.responses.create(
        model=MODEL,
        input=query,
        tools=tools,
        stream=False,
        temperature=0.1,
        top_p=0.4,
    )

    total_time = time.time() - start_time

    # Get response content from responses API
    content = (
        response.output_text if hasattr(response, "output_text") else str(response)
    )

    # collect executed tools (MCP tool calls) and the tools Groq discovered
    executed_tools = []
    discovered_tools = []

    if hasattr(response, "output") and response.output:
        for output_item in response.output:
            item_type = getattr(output_item, "type", "")
            if item_type == "mcp_call":
                executed_tools.append(
                    {
                        "type": "mcp",
                        "name": getattr(output_item, "name", ""),
                        "server_label": getattr(output_item, "server_label", ""),
                        "arguments": getattr(output_item, "arguments", "{}"),
                        "output": getattr(output_item, "output", ""),
                        "error": getattr(output_item, "error", None),
                    }
                )
            elif item_type == "mcp_list_tools":
                discovered_tools = [
                    getattr(tool, "name", "")
                    for tool in getattr(output_item, "tools", [])
                ]

    print(f"Response time: {total_time:.2f}s")

    return {
        "content": content,
        "mcp_calls_performed": executed_tools,
        "tools_discovered": discovered_tools,
        "response_time": total_time,
    }
''')

md("""
Let's implement a helper function to display MCP tool calls and their results. News search is only useful if it actually ran, so this also shows which filters the model chose — `days`, `sentiment`, `ticker`, `country`, and the rest.
""")

code('''
def print_mcp_calls(result, max_articles=5):
    if result["tools_discovered"]:
        print(f"TOOLS DISCOVERED: {', '.join(result['tools_discovered'])}")

    executed_tools = result["mcp_calls_performed"]
    if not executed_tools:
        print("\\nNo MCP tool calls. The model answered without searching.")
        return

    print(f"\\nWEBZ.IO MCP CALLS: Found {len(executed_tools)} tool call(s):")
    print("-" * 50)
    for i, tool in enumerate(executed_tools, 1):
        print(f"\\nTool Call #{i}")
        print(f"   Type: {tool['type']}")
        print(f"   Tool Name: {tool['name']}")
        print(f"   Server: {tool['server_label']}")

        if tool["error"]:
            print(f"   Error: {tool['error']}")
            continue

        if tool["arguments"]:
            args = (
                json.loads(tool["arguments"])
                if isinstance(tool["arguments"], str)
                else tool["arguments"]
            )
            print(f"   Filters chosen by the model: {args}")

        # Print the retrieved articles for transparency
        if tool["output"]:
            output = tool["output"]
            print(f"   Output: {output[:500]}")
            if len(output) > 500:
                print(f"   ... ({len(output)} characters total)")
''')

md("""
# Examples

**Note:** Some queries may consume more tokens than others depending on the amount of tool calls the model makes. Please be aware of various rate limits that are tied to your API keys if you happen to run into any rate limit errors.

---
""")

md("""
## Demo 1: Breaking news research

A plain-language question with no filters. The model writes the query and picks the lookback window itself.
""")

code('''
from IPython.display import Markdown

ai_regulation_news = connect_groq_to_webz(
    client,
    tools,
    "What happened with EU AI regulation in the past month? "
    "Run a single news_search_by_webz search, then summarize the main "
    "developments and cite the article titles and URLs you used.",
)
''')

md("""
Let's display the agent's response in markdown format.
""")

code("""
Markdown(ai_regulation_news["content"])
""")

md("""
Let's examine the agent's intermediate steps, including how it calls the tool and configures arguments such as `query`, `days`, and `k`.
""")

code("""
print_mcp_calls(ai_regulation_news)
""")

md("""
## Demo 2: Sentiment and ticker filters

Webz.io enriches every article with sentiment, entities, and stock tickers. Naming those filters in the prompt is enough — Groq passes them straight through to the MCP server.
""")

code('''
nvidia_sentiment = connect_groq_to_webz(
    client,
    tools,
    "Find negative coverage of Nvidia from the last 7 days. "
    "Use news_search_by_webz with ticker NVDA, sentiment negative, days 7, "
    "language english, and k 10. "
    "List the headline, publisher, date, and URL for each, then explain the common themes.",
)
''')

md("""
Let's display the agent's response in markdown format.
""")

code("""
Markdown(nvidia_sentiment["content"])
""")

md("""
Let's examine the agent's intermediate steps.
""")

code("""
print_mcp_calls(nvidia_sentiment)
""")

md("""
## Demo 3: Regional media comparison

Two searches in one turn, split by country, to compare how different regions cover the same story.
""")

code('''
regional_comparison = connect_groq_to_webz(
    client,
    tools,
    "Compare how European and American media are covering AI chip export controls. "
    "Make exactly two news_search_by_webz searches: one with country DE and FR, "
    "one with country US. Use days 30 and k 5 for both. "
    "Then contrast the framing and cite sources from each region.",
)
''')

code("""
Markdown(regional_comparison["content"])
""")

code("""
print_mcp_calls(regional_comparison)
""")

md("""
## Demo 4: Try it Yourself

Now it's your turn! Replace the query with the news topic you want to track.

Filters available on `news_search_by_webz`: `query`, `k`, `days`, `allow_all_dates`, `language`, `country`, `sentiment`, `category`, `domain`, `exclude_domain`, `topic`, `person`, `organization`, `location`, `ticker`, `political_bias`, `domain_rank_gte`, `domain_rank_lte`, `score_gte`, `score_lte`. Full reference: [Webz.io MCP tool reference](https://docs.webz.io/docs/webz/news-search-api-mcp#tool-reference).
""")

code("""
your_query = "Your Query Here"  # Change this!

custom_response = connect_groq_to_webz(client, tools, your_query)
""")

code("""
Markdown(custom_response["content"])
""")

code("""
print_mcp_calls(custom_response)
""")

md("""
## Troubleshooting

- **`424 Failed Dependency`** — Groq reached the MCP server but authentication failed. Check `WEBZ_API_TOKEN`, and make sure it is in `headers`, not in the server URL.
- **No MCP calls in the output** — the model answered from memory. Name `news_search_by_webz` in the prompt and keep `temperature` low.
- **Validation error on `topic`** — `topic` takes topic tags, not the search subject. Put the subject in `query`.

**Challenge:** Build a market intelligence agent that tracks a ticker every morning, filters for negative sentiment, compares coverage across regions, and posts a digest with sources.

## Additional Resources

- [Webz.io News Search MCP server](https://docs.webz.io/docs/webz/news-search-api-mcp)
- [Webz.io News Search filters](https://docs.webz.io/docs/webz/news-search-api-filters)
- [Groq remote MCP documentation](https://console.groq.com/docs/tool-use/remote-mcp)
- [Groq Responses API](https://console.groq.com/docs/responses-api)
""")

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": ".venv",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11.6",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}

# nbformat stores source as a list of lines with trailing newlines
for cell in notebook["cells"]:
    cell["source"] = [line + "\n" for line in cell["source"].split("\n")]
    cell["source"][-1] = cell["source"][-1].rstrip("\n")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {OUT} with {len(cells)} cells")
