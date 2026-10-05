# lfx-webz

**Search global news with [Webz.io](https://webz.io) inside [Langflow](https://langflow.org).**

[Webz.io News Search](https://docs.webz.io/docs/webz/news-search-api) covers news from the last 30 days. Ask in plain language and get article titles, URLs, publish dates, source metadata, and the excerpt that matched.

This package is a Langflow Extension. Langflow discovers it at startup. Webz.io maintains it separately from Langflow core.

## Install

```bash
pip install lfx-webz
```

Langflow must already be installed (`pip install langflow`). Restart Langflow after installing the extension. The **Webz.io News Search** component appears under the **Webz.io** bundle.

```bash
export WEBZ_API_TOKEN="your-webz-api-token"
langflow run
```

Get a token from your [Webz.io dashboard](https://webz.io). The same token is used by the News Search API.

You can leave the component's **Webz API Key** input empty when `WEBZ_API_TOKEN` is set in the environment Langflow runs in. Otherwise paste the token into that secret field. The token is not hardcoded.

## Use it in a flow

1. Add **Webz.io News Search** to the canvas.
2. Set **Query** to a natural-language question, for example `recent developments on EU AI regulation`.
3. Set **Number of results**. Optional filters (advanced): days, language, country, site/domain, sentiment, and category.
4. Connect **Data** or **DataFrame** to the next component.

**Days** is a shortcut. The API has no `days` field. A value greater than 0 is sent as `filters.published_from` (UTC date of today minus that many days). `0` leaves the date filter off, which uses the API's 30-day window. Coverage does not go further back than 30 days.

To let an Agent call the search, either:

- Connect the component's **Tools** output to the Agent, or
- Enable tool mode on the component. **Query** and the filters are tool-mode inputs.

## Direct call

```python
import os

from components.lfx_webz.webz_news_search import WebzNewsSearchComponent

component = WebzNewsSearchComponent()
component.api_key = os.environ["WEBZ_API_TOKEN"]
component.query = "recent developments on EU AI regulation"
component.k = 5
component.days = 7
component.language = "english"

for item in component.fetch_content():
    print(item.data["title"], item.data["url"])
```

## Filters

| Input | API field |
| --- | --- |
| Number of results | `k` |
| Days | `filters.published_from` (derived; `days` is not sent) |
| Language | `filters.language` |
| Country | `filters.country` |
| Site / domain | `filters.domain` |
| Sentiment | `filters.sentiment` (`positive`, `negative`, `neutral`) |
| Category | `filters.category` (one of the 17 article categories) |

Full request reference: [News Search API](https://docs.webz.io/docs/webz/news-search-api).

## Develop

From this directory, with `lfx` installed:

```bash
lfx extension validate .
pytest
```

`lfx extension dev .` starts a Langflow server with this extension loaded.
