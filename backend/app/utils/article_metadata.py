import re
from urllib.parse import urlsplit


_GOOGLE_NEWS_PREFIX = "google news"
_GOOGLE_NEWS_HOST = "news.google.com"


def _is_google_news_url(url: str | None) -> bool:
    if not url:
        return True
    try:
        host = (urlsplit(url).hostname or "").lower()
        return host == _GOOGLE_NEWS_HOST
    except ValueError:
        return True


def resolve_publisher_url(
    url: str | None,
    canonical_url: str | None,
) -> str | None:
    """Return the best URL to use for embedding: canonical if available and not
    a Google News URL, otherwise the article URL if it is a direct publisher
    URL. Returns None when only a Google News URL is available."""
    # Prefer canonical_url if it resolves to a real publisher domain
    if canonical_url and not _is_google_news_url(canonical_url):
        return canonical_url
    # Fallback: article url if it is already a publisher URL
    if url and not _is_google_news_url(url):
        return url
    return None



def publisher_name(
    source_name: str,
    title: str,
    url: str,
    canonical_url: str | None = None,
) -> str:
    source = source_name.strip()
    candidate_url = canonical_url or url

    if not source.lower().startswith(_GOOGLE_NEWS_PREFIX):
        return _clean_source_name(source)

    host_publisher = _publisher_from_host(candidate_url)
    if host_publisher:
        return host_publisher

    title_publisher = _publisher_from_google_title(title)
    if title_publisher:
        return _clean_source_name(title_publisher)

    return _clean_source_name(source)


def _publisher_from_google_title(title: str) -> str | None:
    parts = re.split(r"\s(?:-|\|)\s", title.strip())
    if len(parts) < 2:
        return None

    candidate = parts[-1].strip()
    if not candidate or len(candidate) > 100:
        return None

    if "." in candidate:
        return _publisher_from_host(f"https://{candidate}")

    return candidate


def _publisher_from_host(url: str) -> str | None:
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return None

    if not host or host == "news.google.com":
        return None

    return _clean_host(host)


def _clean_source_name(value: str) -> str:
    cleaned = re.sub(r"^(?:Google News|NewsAPI)\s*-\s*", "", value, flags=re.I)
    cleaned = cleaned.replace(" Official News", "")
    cleaned = cleaned.strip() or value
    known_names = {
        "openai": "OpenAI",
        "cnbc": "CNBC",
        "reuters": "Reuters",
        "npr": "NPR",
        "techcrunch": "TechCrunch",
        "techrepublic": "TechRepublic",
        "the verge": "The Verge",
        "the guardian": "The Guardian",
        "the new york times": "The New York Times",
    }
    return known_names.get(cleaned.lower(), cleaned)


def _clean_host(host: str) -> str:
    host = host.removeprefix("www.")
    labels = host.split(".")
    if len(labels) > 1:
        host = labels[-2] if labels[-1] in {"com", "org", "net", "co", "io"} else host
    return host.replace("-", " ").title().replace(" ", "")
