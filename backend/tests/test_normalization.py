from app.processing.normalization import (
    canonicalize_url,
    clean_text,
    content_hash,
)


def test_canonicalize_url_removes_tracking():
    url = (
        "https://Example.COM/article"
        "?utm_source=newsletter"
        "&id=42"
        "&fbclid=tracking"
        "#comments"
    )

    assert canonicalize_url(url) == (
        "https://example.com/article?id=42"
    )


def test_canonicalize_url_removes_default_port():
    assert canonicalize_url(
        "https://Example.com:443/story"
    ) == "https://example.com/story"


def test_canonicalize_url_preserves_useful_query():
    assert canonicalize_url(
        "https://example.com/search"
        "?q=PayU&page=2"
    ) == (
        "https://example.com/search"
        "?q=PayU&page=2"
    )


def test_canonicalize_url_adds_root_path():
    assert canonicalize_url(
        "https://Example.com"
    ) == "https://example.com/"


def test_canonicalize_url_empty():
    assert canonicalize_url("") == ""


def test_clean_text_normalizes_whitespace():
    text = (
        "  First   paragraph.  \r\n"
        "\r\n"
        " Second\tparagraph. "
    )

    assert clean_text(text) == (
        "First paragraph.\n"
        "Second paragraph."
    )


def test_clean_text_handles_none():
    assert clean_text(None) == ""


def test_content_hash_is_deterministic():
    first = content_hash(
        "PayU   article\ncontent"
    )

    second = content_hash(
        "PayU article\ncontent"
    )

    assert first is not None
    assert first == second
    assert len(first) == 64


def test_content_hash_changes_with_content():
    assert content_hash(
        "Article A"
    ) != content_hash(
        "Article B"
    )


def test_content_hash_empty_returns_none():
    assert content_hash(
        "   \n\t "
    ) is None
