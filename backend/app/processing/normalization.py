import hashlib
import re
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(
    url: str,
) -> str:
    value = url.strip()

    if not value:
        return ""

    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    if not parsed.scheme or not parsed.netloc:
        return value

    scheme = parsed.scheme.lower()

    hostname = (
        parsed.hostname.lower()
        if parsed.hostname
        else ""
    )

    port = parsed.port

    if (
        port is not None
        and not (
            scheme == "http"
            and port == 80
        )
        and not (
            scheme == "https"
            and port == 443
        )
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    if parsed.username:
        user_info = parsed.username

        if parsed.password:
            user_info += (
                f":{parsed.password}"
            )

        netloc = (
            f"{user_info}@{netloc}"
        )

    query_pairs = parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    filtered_query = []

    for key, value in query_pairs:
        key_lower = key.lower()

        if key_lower.startswith("utm_"):
            continue

        if key_lower in TRACKING_PARAMETERS:
            continue

        filtered_query.append(
            (key, value)
        )

    query = urlencode(
        filtered_query,
        doseq=True,
    )

    path = parsed.path or "/"

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            "",
        )
    )


def clean_text(
    text: str | None,
) -> str:
    if not text:
        return ""

    value = text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    lines = []

    for raw_line in value.split("\n"):
        line = re.sub(
            r"[ \t]+",
            " ",
            raw_line,
        ).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def content_hash(
    text: str | None,
) -> str | None:
    cleaned = clean_text(text)

    if not cleaned:
        return None

    return hashlib.sha256(
        cleaned.encode("utf-8")
    ).hexdigest()
