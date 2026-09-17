from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.embeddings import EmbeddingResult
from app.services.semantic_search_service import (
    semantic_search,
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
async def test_semantic_search_returns_ranked_results():
    provider = make_provider()

    rows = [
        SimpleNamespace(
            id=1,
            title="PayU faces RBI regulatory review",
            source_name="source-a",
            url="https://example.com/1",
            published_at=datetime(
                2026,
                9,
                9,
                tzinfo=timezone.utc,
            ),
            distance=0.10,
        ),
        SimpleNamespace(
            id=2,
            title="Digital payments expand in India",
            source_name="source-b",
            url="https://example.com/2",
            published_at=None,
            distance=0.25,
        ),
    ]

    db = AsyncMock()

    db.execute.return_value = (
        SimpleNamespace(
            all=lambda: rows
        )
    )

    result = await semantic_search(
        db,
        "PayU RBI regulation",
        limit=5,
        provider=provider,
    )

    assert len(result) == 2

    assert result[0].article_id == 1
    assert result[0].distance == pytest.approx(
        0.10
    )
    assert result[0].similarity == pytest.approx(
        0.90
    )

    assert result[1].article_id == 2
    assert result[1].similarity == pytest.approx(
        0.75
    )

    provider.embed_text.assert_awaited_once_with(
        "PayU RBI regulation"
    )

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_semantic_search_trims_query():
    provider = make_provider()

    db = AsyncMock()

    db.execute.return_value = (
        SimpleNamespace(
            all=lambda: []
        )
    )

    await semantic_search(
        db,
        "  PayU payments  ",
        provider=provider,
    )

    provider.embed_text.assert_awaited_once_with(
        "PayU payments"
    )


@pytest.mark.asyncio
async def test_semantic_search_filters_minimum_similarity():
    provider = make_provider()

    rows = [
        SimpleNamespace(
            id=1,
            title="Highly relevant",
            source_name="source-a",
            url="https://example.com/1",
            published_at=None,
            distance=0.10,
        ),
        SimpleNamespace(
            id=2,
            title="Weakly relevant",
            source_name="source-b",
            url="https://example.com/2",
            published_at=None,
            distance=0.60,
        ),
    ]

    db = AsyncMock()

    db.execute.return_value = (
        SimpleNamespace(
            all=lambda: rows
        )
    )

    result = await semantic_search(
        db,
        "PayU",
        minimum_similarity=0.70,
        provider=provider,
    )

    assert len(result) == 1
    assert result[0].article_id == 1
    assert result[0].similarity == pytest.approx(
        0.90
    )


@pytest.mark.asyncio
async def test_semantic_search_rejects_empty_query():
    db = AsyncMock()
    provider = make_provider()

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        await semantic_search(
            db,
            "   ",
            provider=provider,
        )

    provider.embed_text.assert_not_awaited()
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_semantic_search_rejects_invalid_limit():
    db = AsyncMock()
    provider = make_provider()

    with pytest.raises(
        ValueError,
        match="limit must be at least 1",
    ):
        await semantic_search(
            db,
            "PayU",
            limit=0,
            provider=provider,
        )

    provider.embed_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_semantic_search_rejects_invalid_similarity():
    db = AsyncMock()
    provider = make_provider()

    with pytest.raises(
        ValueError,
        match="between -1 and 1",
    ):
        await semantic_search(
            db,
            "PayU",
            minimum_similarity=1.5,
            provider=provider,
        )

    provider.embed_text.assert_not_awaited()

@pytest.mark.asyncio
async def test_semantic_search_returns_company_enrichment(
    monkeypatch,
):
    provider = make_provider()

    rows = [
        SimpleNamespace(
            id=10,
            title="RBI regulatory update",
            source_name="Reuters",
            url="https://example.com/10",
            published_at=None,
            distance=0.10,
        ),
    ]

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        all=lambda: rows,
    )

    enrichment_mock = AsyncMock(
        return_value={
            10: SimpleNamespace(
                event_type="regulatory_action",
                sentiment="negative",
                risk_level="high",
                risk_score=82.5,
                business_impact="regulatory",
                event_cluster_id=7,
            )
        }
    )

    monkeypatch.setattr(
        "app.services.semantic_search_service."
        "get_search_result_enrichments",
        enrichment_mock,
    )

    result = await semantic_search(
        db,
        "RBI regulation",
        company_id=2,
        provider=provider,
    )

    assert len(result) == 1

    item = result[0]

    assert item.article_id == 10
    assert item.similarity == pytest.approx(0.90)
    assert item.event_type == "regulatory_action"
    assert item.sentiment == "negative"
    assert item.risk_level == "high"
    assert item.risk_score == 82.5
    assert item.business_impact == "regulatory"
    assert item.event_cluster_id == 7

    enrichment_mock.assert_awaited_once_with(
        db,
        article_ids=[10],
        company_id=2,
    )


@pytest.mark.asyncio
async def test_semantic_search_allows_missing_company_enrichment(
    monkeypatch,
):
    provider = make_provider()

    rows = [
        SimpleNamespace(
            id=11,
            title="General payments update",
            source_name="Example",
            url="https://example.com/11",
            published_at=None,
            distance=0.20,
        ),
    ]

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        all=lambda: rows,
    )

    enrichment_mock = AsyncMock(
        return_value={},
    )

    monkeypatch.setattr(
        "app.services.semantic_search_service."
        "get_search_result_enrichments",
        enrichment_mock,
    )

    result = await semantic_search(
        db,
        "payments",
        company_id=2,
        provider=provider,
    )

    assert len(result) == 1

    item = result[0]

    assert item.article_id == 11
    assert item.similarity == pytest.approx(0.80)
    assert item.event_type is None
    assert item.sentiment is None
    assert item.risk_level is None
    assert item.risk_score is None
    assert item.business_impact is None
    assert item.event_cluster_id is None

    enrichment_mock.assert_awaited_once_with(
        db,
        article_ids=[11],
        company_id=2,
    )
