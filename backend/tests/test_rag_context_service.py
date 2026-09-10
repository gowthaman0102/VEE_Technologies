from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.rag_context_service import (
    build_rag_query,
    retrieve_rag_context,
)
from app.services.semantic_search_service import (
    SemanticSearchResult,
)


def make_article():
    return SimpleNamespace(
        id=8,
        title="PayU receives RBI approval",
    )


def make_result(
    article_id: int,
    title: str,
    similarity: float,
):
    return SemanticSearchResult(
        article_id=article_id,
        title=title,
        source_name="test-source",
        url=f"https://example.com/{article_id}",
        published_at=None,
        distance=1.0 - similarity,
        similarity=similarity,
    )


def test_build_rag_query():
    article = make_article()

    query = build_rag_query(
        article,
        company_name="PayU",
    )

    assert query == (
        "PayU: PayU receives RBI approval"
    )


def test_build_rag_query_rejects_empty_title():
    article = SimpleNamespace(
        id=8,
        title="   ",
    )

    with pytest.raises(
        ValueError,
        match="Article title is required",
    ):
        build_rag_query(
            article,
            company_name="PayU",
        )


@pytest.mark.asyncio
async def test_retrieve_rag_context_excludes_current_article(
    monkeypatch,
):
    article = make_article()

    results = [
        make_result(
            8,
            "Current article",
            0.95,
        ),
        make_result(
            5,
            "Related article one",
            0.80,
        ),
        make_result(
            3,
            "Related article two",
            0.70,
        ),
        make_result(
            7,
            "Related article three",
            0.60,
        ),
    ]

    search_mock = AsyncMock(
        return_value=results
    )

    monkeypatch.setattr(
        "app.services.rag_context_service."
        "semantic_search",
        search_mock,
    )

    context = await retrieve_rag_context(
        AsyncMock(),
        article,
        company_name="PayU",
        limit=3,
    )

    assert context.query == (
        "PayU: PayU receives RBI approval"
    )

    assert [
        item.article_id
        for item in context.related_articles
    ] == [5, 3, 7]

    search_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_retrieve_rag_context_respects_limit(
    monkeypatch,
):
    article = make_article()

    results = [
        make_result(5, "One", 0.80),
        make_result(3, "Two", 0.70),
        make_result(7, "Three", 0.60),
    ]

    monkeypatch.setattr(
        "app.services.rag_context_service."
        "semantic_search",
        AsyncMock(return_value=results),
    )

    context = await retrieve_rag_context(
        AsyncMock(),
        article,
        company_name="PayU",
        limit=2,
    )

    assert len(context.related_articles) == 2


@pytest.mark.asyncio
async def test_retrieve_rag_context_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="RAG retrieval limit must be at least 1",
    ):
        await retrieve_rag_context(
            AsyncMock(),
            make_article(),
            company_name="PayU",
            limit=0,
        )
