from urllib.parse import urlsplit

from googlenewsdecoder import new_decoderv1


def is_google_news_url(
    url: str,
) -> bool:
    try:
        host = (
            urlsplit(url)
            .hostname
            or ""
        ).lower()
    except ValueError:
        return False

    return host == "news.google.com"


def resolve_article_url(
    url: str,
) -> str:
    if not is_google_news_url(url):
        return url

    try:
        result = new_decoderv1(url)
    except Exception:
        return url

    if not isinstance(result, dict):
        return url

    if not result.get("status"):
        return url

    decoded_url = result.get(
        "decoded_url"
    )

    if not isinstance(
        decoded_url,
        str,
    ):
        return url

    decoded_url = decoded_url.strip()

    if not decoded_url:
        return url

    return decoded_url
