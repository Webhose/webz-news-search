"""News search for MovieClaw users, kept outside the MovieClaw repository."""

from movieclaw_webz.provider import (
    API_URL_ENV_NAME,
    DEFAULT_RESULTS,
    MAX_QUERY,
    MAX_RESULTS,
    NewsHit,
    WebzNewsError,
    WebzNewsSearchProvider,
    format_hits,
)

__all__ = [
    "API_URL_ENV_NAME",
    "DEFAULT_RESULTS",
    "MAX_QUERY",
    "MAX_RESULTS",
    "NewsHit",
    "WebzNewsError",
    "WebzNewsSearchProvider",
    "format_hits",
]
