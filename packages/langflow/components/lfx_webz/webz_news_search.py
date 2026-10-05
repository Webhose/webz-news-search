"""Webz.io News Search component for Langflow.

Calls POST https://api.webz.io/api/news/context. The API has no ``days``
field; a positive Days value is sent as ``filters.published_from``. Coverage
is the last 30 days. The endpoint is https only, and the token is never
hardcoded.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx
from langchain_core.tools import tool
from lfx.custom.custom_component.component import Component
from lfx.field_typing import Tool
from lfx.io import DropdownInput, IntInput, MessageTextInput, Output, SecretStrInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame

API_URL = "https://api.webz.io/api/news/context"
TOKEN_ENV_NAME = "WEBZ_API_TOKEN"
USER_AGENT = "lfx-webz"
DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_QUERY_CHARS = 750
MAX_QUERY_WORDS = 100

# Article categories accepted by the News Search API.
CATEGORIES = (
    "Arts, Culture and Entertainment",
    "Crime, Law and Justice",
    "Disaster and Accident",
    "Economy, Business and Finance",
    "Education",
    "Environment",
    "Health",
    "Human Interest",
    "Labor",
    "Lifestyle and Leisure",
    "Politics",
    "Religion and Belief",
    "Science and Technology",
    "Social Issue",
    "Sport",
    "War, Conflict and Unrest",
    "Weather",
)

SENTIMENTS = ("positive", "negative", "neutral")
_DOCS = "https://docs.webz.io/docs/webz/news-search-api"


class WebzConfigError(ValueError):
    """Raised when the component is missing a token or a valid query."""


class WebzAPIError(ValueError):
    """Raised when the News Search API returns an error or cannot be reached."""


def require_https(url: str) -> str:
    """Reject any endpoint that is not an absolute https URL before a token is sent."""
    parsed = urlsplit((url or "").strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise WebzConfigError(
            f"The Webz.io News Search endpoint must be an absolute https:// URL, got {url!r}."
        )
    return url


def resolve_api_token(api_key: Any | None = None) -> str:
    """Use the component secret when it is set, otherwise WEBZ_API_TOKEN."""
    if hasattr(api_key, "get_secret_value"):
        api_key = api_key.get_secret_value()
    token = str(api_key or "").strip() or (os.getenv(TOKEN_ENV_NAME) or "").strip()
    if not token:
        raise WebzConfigError(
            "Webz API key is required. Set the Webz API Key input on the component "
            f"or export {TOKEN_ENV_NAME}."
        )
    return token


def normalize_query(query: str) -> str:
    text = (query or "").strip()
    if not text:
        raise WebzConfigError("query is required.")
    if len(text) > MAX_QUERY_CHARS:
        raise WebzConfigError(
            f"query is too long: {len(text)} characters (max {MAX_QUERY_CHARS})."
        )
    words = len(text.split())
    if words > MAX_QUERY_WORDS:
        raise WebzConfigError(f"query is too long: {words} words (max {MAX_QUERY_WORDS}).")
    return text


def published_from_for_days(days: int, now: datetime | None = None) -> str:
    """UTC calendar date of today minus ``days``, as YYYY-MM-DD."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise WebzConfigError("days must be a non-negative integer.")
    current = now or datetime.now(timezone.utc)
    return (current - timedelta(days=days)).date().isoformat()


def split_csv(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _as_int(value: Any, name: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise WebzConfigError(f"{name} must be an integer.")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = int(text)
        except ValueError as exc:
            raise WebzConfigError(f"{name} must be an integer.") from exc
        return number
    if isinstance(value, float):
        if not value.is_integer():
            raise WebzConfigError(f"{name} must be an integer.")
        return int(value)
    return int(value)


def build_request_body(
    query: str,
    *,
    k: Any = None,
    days: Any = None,
    language: Any = None,
    country: Any = None,
    domain: Any = None,
    sentiment: Any = None,
    category: Any = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the JSON body for POST /api/news/context.

    ``days`` is never sent. A positive ``days`` value becomes ``filters.published_from``.
    Zero or empty ``days`` leaves the date filter off so the API's 30-day window applies.
    """
    body: dict[str, Any] = {"query": normalize_query(query)}
    result_count = 10 if k is None or k == "" else _as_int(k, "k")
    if result_count is None or result_count < 1:
        raise WebzConfigError("k must be a positive integer.")
    body["k"] = result_count

    filters: dict[str, Any] = {}
    day_count = 0 if days is None or days == "" else _as_int(days, "days")
    if day_count is None or day_count < 0:
        raise WebzConfigError("days must be a non-negative integer.")
    if day_count > 0:
        filters["published_from"] = published_from_for_days(day_count, now=now)

    for key, value in (
        ("language", language),
        ("country", country),
        ("domain", domain),
    ):
        items = split_csv(value)
        if items:
            filters[key] = items

    sentiment_text = str(sentiment or "").strip()
    if sentiment_text:
        if sentiment_text not in SENTIMENTS:
            raise WebzConfigError("sentiment must be positive, negative, or neutral.")
        filters["sentiment"] = [sentiment_text]

    category_text = str(category or "").strip()
    if category_text:
        if category_text not in CATEGORIES:
            raise WebzConfigError("category must be one of the News Search article categories.")
        filters["category"] = [category_text]

    if filters:
        body["filters"] = filters
    return body


def request_headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def _error_detail(response: httpx.Response) -> str:
    text = (response.text or "").strip()
    if not text:
        return ""
    try:
        payload = response.json()
    except ValueError:
        return text[:500]
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or payload.get("error")
        if isinstance(detail, str):
            return detail
        if detail is not None:
            return json.dumps(detail)[:500]
    return text[:500]


def article_row(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten one API result into the fields the component returns."""
    article = item.get("article") if isinstance(item.get("article"), dict) else {}
    chunk = item.get("chunk") if isinstance(item.get("chunk"), dict) else {}
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    category = metadata.get("category") or ""
    if isinstance(category, list):
        category = " | ".join(str(part) for part in category if str(part).strip())
    score = item.get("score")
    return {
        "title": str(article.get("title") or ""),
        "url": str(article.get("url") or ""),
        "published_at": str(article.get("published_at") or ""),
        "score": float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else None,
        "excerpt": str(chunk.get("text") or ""),
        "summary": str(article.get("summary") or ""),
        "domain": str(metadata.get("domain") or ""),
        "language": str(metadata.get("language") or ""),
        "country": str(metadata.get("country") or ""),
        "sentiment": str(metadata.get("sentiment") or ""),
        "category": str(category or ""),
    }


def parse_results(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise WebzAPIError("News Search response was not a JSON object.")
    items = payload.get("results") or []
    if not isinstance(items, list):
        raise WebzAPIError("News Search response results was not a list.")
    return [article_row(item) for item in items if isinstance(item, dict)]


def results_to_text(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No matching articles."
    blocks: list[str] = []
    for index, row in enumerate(rows, start=1):
        title = row.get("title") or row.get("url") or "(untitled)"
        lines = [f"{index}. {title}"]
        if row.get("url"):
            lines.append(f"   URL: {row['url']}")
        if row.get("published_at"):
            lines.append(f"   Published: {row['published_at']}")
        if row.get("domain"):
            lines.append(f"   Source: {row['domain']}")
        if row.get("excerpt"):
            lines.append(f"   Excerpt: {str(row['excerpt']).strip()}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def search(
    query: str,
    *,
    api_key: Any | None = None,
    k: Any = None,
    days: Any = None,
    language: Any = None,
    country: Any = None,
    domain: Any = None,
    sentiment: Any = None,
    category: Any = None,
    client: httpx.Client | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Run one News Search request and return flat article rows."""
    url = require_https(API_URL)
    token = resolve_api_token(api_key)
    body = build_request_body(
        query,
        k=k,
        days=days,
        language=language,
        country=country,
        domain=domain,
        sentiment=sentiment,
        category=category,
        now=now,
    )
    owns_client = client is None
    http = client or httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS)
    try:
        response = http.post(url, headers=request_headers(token), json=body)
    except httpx.HTTPError as exc:
        raise WebzAPIError(f"Could not reach the Webz.io News Search API: {exc}") from exc
    finally:
        if owns_client:
            http.close()
    if response.status_code >= 400:
        detail = _error_detail(response)
        message = f"Webz.io News Search failed ({response.status_code})"
        if detail:
            message = f"{message}: {detail}"
        raise WebzAPIError(message)
    try:
        payload = response.json()
    except ValueError as exc:
        raise WebzAPIError("News Search response was not valid JSON.") from exc
    return parse_results(payload)


class WebzNewsSearchComponent(Component):
    display_name = "Webz.io News Search"
    description = (
        "Search global news from the last 30 days. "
        "Returns article titles, URLs, dates, and the matching excerpt."
    )
    documentation = _DOCS
    icon = "Search"
    name = "WebzNewsSearch"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="Webz API Key",
            info=(
                "Webz.io API token. Leave empty to read WEBZ_API_TOKEN from the environment. "
                "Get a token from the Webz.io dashboard."
            ),
            required=False,
        ),
        MessageTextInput(
            name="query",
            display_name="Query",
            info="Natural-language news query.",
            tool_mode=True,
            required=True,
        ),
        IntInput(
            name="k",
            display_name="Number of results",
            value=10,
            info="How many articles to return.",
            tool_mode=True,
        ),
        IntInput(
            name="days",
            display_name="Days",
            value=0,
            advanced=True,
            info=(
                "Only articles published in the last N days. "
                "0 keeps the API default, which is the last 30 days. "
                "This is sent as filters.published_from. The API has no days field."
            ),
            tool_mode=True,
        ),
        MessageTextInput(
            name="language",
            display_name="Language",
            value="",
            advanced=True,
            info='Comma-separated languages, for example "english".',
            tool_mode=True,
        ),
        MessageTextInput(
            name="country",
            display_name="Country",
            value="",
            advanced=True,
            info='Comma-separated ISO-2 country codes, for example "US, GB".',
            tool_mode=True,
        ),
        MessageTextInput(
            name="domain",
            display_name="Site / domain",
            value="",
            advanced=True,
            info='Comma-separated source domains, for example "cnn.com".',
            tool_mode=True,
        ),
        DropdownInput(
            name="sentiment",
            display_name="Sentiment",
            options=["", *SENTIMENTS],
            value="",
            advanced=True,
            info="Leave empty for any sentiment.",
            tool_mode=True,
        ),
        DropdownInput(
            name="category",
            display_name="Category",
            options=["", *CATEGORIES],
            value="",
            advanced=True,
            info="One News Search article category. Leave empty for any category.",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="fetch_content"),
        Output(display_name="DataFrame", name="dataframe", method="fetch_content_dataframe"),
        Output(display_name="Tools", name="tools", method="build_tools"),
    ]

    def _text(self, name: str) -> str:
        value = getattr(self, name, "")
        if hasattr(value, "text"):
            value = value.text
        return str(value or "").strip()

    def _search_rows(self, query: str | None = None) -> list[dict[str, Any]]:
        return search(
            self._text("query") if query is None else query,
            api_key=getattr(self, "api_key", None),
            k=getattr(self, "k", 10),
            days=getattr(self, "days", 0),
            language=self._text("language"),
            country=self._text("country"),
            domain=self._text("domain"),
            sentiment=self._text("sentiment"),
            category=self._text("category"),
        )

    def _to_data(self, rows: list[dict[str, Any]]) -> list[Data]:
        items: list[Data] = []
        for row in rows:
            text = row.get("excerpt") or row.get("title") or row.get("url") or ""
            items.append(Data(text=text, data={**row, "text": text}))
        return items

    def fetch_content(self) -> list[Data]:
        results = self._to_data(self._search_rows())
        self.status = results
        return results

    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)

    def run_model(self) -> list[Data]:
        return self.fetch_content()

    def build_tools(self) -> list[Tool]:
        component = self

        @tool
        def news_search(query: str) -> str:
            """Search global news from the last 30 days with Webz.io."""
            return results_to_text(component._search_rows(query=query))

        return [news_search]
