from unittest.mock import AsyncMock

import httpx
import pytest

from app.processing.extractor import (
    ArticleExtractor,
)


SAMPLE_HTML = """
<html>
    <head>
        <title>PayU News</title>
    </head>
    <body>
        <nav>Navigation</nav>

        <article>
            <h1>PayU regulatory update</h1>

            <p>
                The Reserve Bank of India
                announced a regulatory update
                affecting digital payments.
            </p>

            <p>
                PayU said it is reviewing
                the requirements.
            </p>
        </article>

        <footer>Footer links</footer>
    </body>
</html>
"""


def test_extract_from_html():
    content = (
        ArticleExtractor.extract_from_html(
            SAMPLE_HTML
        )
    )

    assert "PayU regulatory update" in content

    assert (
        "Reserve Bank of India"
        in content
    )

    assert (
        "reviewing the requirements"
        in content
    )


def test_extract_from_empty_html():
    assert (
        ArticleExtractor.extract_from_html(
            "   "
        )
        == ""
    )


def test_invalid_timeout():
    with pytest.raises(ValueError):
        ArticleExtractor(
            timeout=0
        )


@pytest.mark.asyncio
async def test_extract_from_url_success(
    monkeypatch,
):
    extractor = ArticleExtractor()

    monkeypatch.setattr(
        extractor,
        "_fetch",
        AsyncMock(
            return_value=(
                SAMPLE_HTML,
                "https://example.com/article",
            )
        ),
    )

    result = await extractor.extract_from_url(
        "https://example.com/article"
    )

    assert result.success is True
    assert result.content is not None
    assert "Reserve Bank of India" in (
        result.content
    )
    assert result.error is None
    assert result.final_url == (
        "https://example.com/article"
    )


@pytest.mark.asyncio
async def test_extract_from_url_empty_url():
    extractor = ArticleExtractor()

    result = await extractor.extract_from_url(
        ""
    )

    assert result.success is False
    assert result.content is None
    assert result.error == (
        "Article URL is required"
    )


@pytest.mark.asyncio
async def test_extract_from_url_timeout(
    monkeypatch,
):
    extractor = ArticleExtractor()

    monkeypatch.setattr(
        extractor,
        "_fetch",
        AsyncMock(
            side_effect=httpx.TimeoutException(
                "timeout"
            )
        ),
    )

    result = await extractor.extract_from_url(
        "https://example.com/article"
    )

    assert result.success is False
    assert result.content is None
    assert result.error == (
        "Article fetch timed out"
    )


@pytest.mark.asyncio
async def test_extract_from_url_http_error(
    monkeypatch,
):
    extractor = ArticleExtractor()

    request = httpx.Request(
        "GET",
        "https://example.com/article",
    )

    response = httpx.Response(
        403,
        request=request,
    )

    monkeypatch.setattr(
        extractor,
        "_fetch",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "forbidden",
                request=request,
                response=response,
            )
        ),
    )

    result = await extractor.extract_from_url(
        "https://example.com/article"
    )

    assert result.success is False
    assert result.content is None
    assert result.error == (
        "Article fetch failed with HTTP 403"
    )


@pytest.mark.asyncio
async def test_extract_from_url_request_error(
    monkeypatch,
):
    extractor = ArticleExtractor()

    request = httpx.Request(
        "GET",
        "https://example.com/article",
    )

    monkeypatch.setattr(
        extractor,
        "_fetch",
        AsyncMock(
            side_effect=httpx.ConnectError(
                "connection failed",
                request=request,
            )
        ),
    )

    result = await extractor.extract_from_url(
        "https://example.com/article"
    )

    assert result.success is False
    assert result.content is None
    assert (
        "ConnectError"
        in result.error
    )


@pytest.mark.asyncio
async def test_extract_from_url_no_content(
    monkeypatch,
):
    extractor = ArticleExtractor()

    monkeypatch.setattr(
        extractor,
        "_fetch",
        AsyncMock(
            return_value=(
                "<html><body></body></html>",
                "https://example.com/article",
            )
        ),
    )

    result = await extractor.extract_from_url(
        "https://example.com/article"
    )

    assert result.success is False
    assert result.content is None
    assert result.error == (
        "No article content extracted"
    )
