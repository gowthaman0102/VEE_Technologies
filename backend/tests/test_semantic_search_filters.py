from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.embeddings import EmbeddingResult
from app.schemas.search_filters import SearchFilters
from app.services.semantic_search_service import semantic_search


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


def make_db():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [],
    )

    return db


@pytest.mark.asyncio
async def test_semantic_search_filters_time_and_source():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        provider=provider,
        filters=SearchFilters(
            start=datetime(
                2026,
                9,
                1,
                tzinfo=timezone.utc,
            ),
            end=datetime(
                2026,
                9,
                17,
                tzinfo=timezone.utc,
            ),
            source_name="Reuters",
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "articles.published_at >=" in sql
    assert "articles.published_at <=" in sql
    assert "lower(articles.source_name)" in sql


@pytest.mark.asyncio
async def test_semantic_search_company_filter_uses_triage():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN article_triages" in sql
    assert "article_triages.company_id" in sql


@pytest.mark.asyncio
async def test_semantic_search_filters_event_type():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            event_type="enforcement",
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "lower(article_triages.event_type)" in sql


@pytest.mark.asyncio
async def test_semantic_search_filters_sentiment():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            sentiment="negative",
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN article_sentiments" in sql
    assert "article_sentiments.company_id" in sql
    assert "lower(article_sentiments.label)" in sql


@pytest.mark.asyncio
async def test_semantic_search_filters_risk():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            risk_level="high",
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN risk_assessments" in sql
    assert "risk_assessments.company_id" in sql
    assert "lower(risk_assessments.risk_level)" in sql


@pytest.mark.asyncio
async def test_semantic_search_filters_business_impact():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            business_impact="regulatory",
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN article_business_impacts" in sql
    assert "article_business_impacts.company_id" in sql
    assert (
        "lower(article_business_impacts.primary_category)"
        in sql
    )


@pytest.mark.asyncio
async def test_semantic_search_filters_event_cluster():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            event_cluster_id=7,
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN event_cluster_memberships" in sql
    assert "event_cluster_memberships.company_id" in sql
    assert "event_cluster_memberships.cluster_id" in sql


@pytest.mark.asyncio
async def test_semantic_search_supports_combined_filters():
    db = make_db()
    provider = make_provider()

    await semantic_search(
        db,
        "regulatory risk",
        company_id=2,
        provider=provider,
        filters=SearchFilters(
            sentiment="negative",
            risk_level="high",
            business_impact="regulatory",
            event_type="enforcement",
            event_cluster_id=7,
        ),
    )

    stmt = db.execute.await_args.args[0]
    sql = str(stmt)

    assert "JOIN article_triages" in sql
    assert "JOIN article_sentiments" in sql
    assert "JOIN risk_assessments" in sql
    assert "JOIN article_business_impacts" in sql
    assert "JOIN event_cluster_memberships" in sql


@pytest.mark.asyncio
async def test_company_scoped_semantic_filter_requires_company():
    db = make_db()
    provider = make_provider()

    with pytest.raises(
        ValueError,
        match="company_id is required",
    ):
        await semantic_search(
            db,
            "regulatory risk",
            provider=provider,
            filters=SearchFilters(
                risk_level="high",
            ),
        )

    provider.embed_text.assert_not_awaited()
    db.execute.assert_not_awaited()
