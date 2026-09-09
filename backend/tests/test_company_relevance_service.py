from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.embeddings import EmbeddingResult
from app.services.company_relevance_service import (
    score_company_article_relevance,
)
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)


def make_provider():
    return SimpleNamespace(
        embed_text=AsyncMock(
            return_value=EmbeddingResult(
                vector=[0.1, 0.2, 0.3],
                model="test-model",
                dimensions=3,
            )
        )
    )


@pytest.mark.asyncio
async def test_company_relevance_scores_articles(
    monkeypatch,
):
    context = CompanySemanticContext(
        company_id=1,
        company_name="PayU",
        text="Company: PayU\nRegulators: RBI",
    )

    context_mock = AsyncMock(
        return_value=context
    )

    monkeypatch.setattr(
        "app.services.company_relevance_service."
        "build_company_semantic_context",
        context_mock,
    )

    rows = [
        SimpleNamespace(
            id=10,
            title="PayU faces RBI review",
            source_name="source-a",
            url="https://example.com/10",
            published_at=None,
            distance=0.10,
        ),
        SimpleNamespace(
            id=11,
            title="Unrelated technology news",
            source_name="source-b",
            url="https://example.com/11",
            published_at=None,
            distance=0.55,
        ),
    ]

    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: rows
    )

    provider = make_provider()

    result = await score_company_article_relevance(
        db,
        company_id=1,
        threshold=0.65,
        provider=provider,
    )

    assert result is not None
    assert result.company_id == 1
    assert result.company_name == "PayU"
    assert result.threshold == 0.65
    assert len(result.results) == 2

    assert result.results[0].similarity == (
        pytest.approx(0.90)
    )
    assert result.results[0].is_relevant is True

    assert result.results[1].similarity == (
        pytest.approx(0.45)
    )
    assert result.results[1].is_relevant is False

    provider.embed_text.assert_awaited_once_with(
        context.text
    )

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_company_relevance_missing_company(
    monkeypatch,
):
    context_mock = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.services.company_relevance_service."
        "build_company_semantic_context",
        context_mock,
    )

    provider = make_provider()
    db = AsyncMock()

    result = await score_company_article_relevance(
        db,
        company_id=999,
        provider=provider,
    )

    assert result is None
    provider.embed_text.assert_not_awaited()
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_company_relevance_uses_default_threshold(
    monkeypatch,
):
    context = CompanySemanticContext(
        company_id=1,
        company_name="PayU",
        text="Company: PayU",
    )

    monkeypatch.setattr(
        "app.services.company_relevance_service."
        "build_company_semantic_context",
        AsyncMock(
            return_value=context
        ),
    )

    monkeypatch.setattr(
        "app.services.company_relevance_service."
        "settings.semantic_relevance_threshold",
        0.70,
    )

    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: []
    )

    result = await score_company_article_relevance(
        db,
        company_id=1,
        provider=make_provider(),
    )

    assert result is not None
    assert result.threshold == 0.70


@pytest.mark.asyncio
async def test_company_relevance_rejects_invalid_limit():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="limit must be at least 1",
    ):
        await score_company_article_relevance(
            db,
            company_id=1,
            limit=0,
            provider=make_provider(),
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_company_relevance_rejects_invalid_threshold():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="between -1 and 1",
    ):
        await score_company_article_relevance(
            db,
            company_id=1,
            threshold=1.5,
            provider=make_provider(),
        )

    db.execute.assert_not_awaited()
