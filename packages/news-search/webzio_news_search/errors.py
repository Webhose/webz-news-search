from __future__ import annotations

STATUS_HINTS = {
    400: "the query is too long (max 750 characters and 100 words).",
    401: "the API token is missing, invalid, or lacks permission.",
    402: "the account has insufficient credits.",
    403: "the account is inactive, blocked, or its trial has ended.",
    422: "the request body is invalid (for example k above the allowed maximum).",
    429: "the token exceeded its request-rate limit. retry later.",
}


class WebzNewsSearchError(Exception):
    """base error for webzio-news-search."""


class WebzConfigError(WebzNewsSearchError, ValueError):
    """raised when the client is missing a token or given an invalid request."""


class WebzAPIError(WebzNewsSearchError):
    """raised when the News Search API returns an HTTP error."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        self.detail = detail
        hint = STATUS_HINTS.get(status_code)
        if hint is None and status_code >= 500:
            hint = "temporary server error. retry later."
        message = f"News Search API returned HTTP {status_code}"
        if hint:
            message = f"{message}: {hint}"
        if detail:
            message = f"{message} ({detail})"
        super().__init__(message)
