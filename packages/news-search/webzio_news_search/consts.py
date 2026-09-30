DEFAULT_API_URL = "https://api.webz.io/api/news/context"
TOKEN_ENV_NAME = "WEBZ_API_TOKEN"
API_URL_ENV_NAME = "WEBZ_NEWS_SEARCH_URL"
TOOL_NAME = "news_search_by_webz"
USER_AGENT = "webzio-news-search-python"

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_CONNECT_TIMEOUT_SECONDS = 15.0

MAX_QUERY_CHARS = 750
MAX_QUERY_WORDS = 100

# filters that the API reads as arrays of strings. a bare string is wrapped in a list.
LIST_FILTERS = (
    "language",
    "country",
    "category",
    "sentiment",
    "domain",
    "exclude_domain",
    "topic",
    "person",
    "organization",
    "location",
    "ticker",
    "political_bias",
)

# filters that the API reads as a single value.
SCALAR_FILTERS = (
    "published_from",
    "published_to",
    "trust_category",
    "source_type",
    "domain_rank_gte",
    "domain_rank_lte",
)

KNOWN_FILTERS = LIST_FILTERS + SCALAR_FILTERS
