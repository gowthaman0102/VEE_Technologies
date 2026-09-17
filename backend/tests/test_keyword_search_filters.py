from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.search_filters import SearchFilters
from app.services.discovery_service import keyword_search


def make_db():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [],
        ),
    )

    return db


@pytest.mark.asyncio
async def test_keyword_search_without_filters_keeps_basic_query():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "article_triages" in sql
    assert "article_sentiments" not in sql
    assert "risk_assessments" not in sql
    assert "article_business_impacts" not in sql
    assert "event_cluster_memberships" not in sql


@pytest.mark.asyncio
async def test_keyword_search_applies_time_and_source_filters():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
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

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "articles.published_at >=" in sql
    assert "articles.published_at <=" in sql
    assert "lower(articles.source_name)" in sql


@pytest.mark.asyncio
async def test_keyword_search_applies_event_type_filter():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            event_type="regulatory",
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "lower(article_triages.event_type)" in sql


@pytest.mark.asyncio
async def test_keyword_search_joins_sentiment_only_when_requested():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            sentiment="negative",
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "JOIN article_sentiments" in sql
    assert "article_sentiments.company_id" in sql
    assert "lower(article_sentiments.label)" in sql


@pytest.mark.asyncio
async def test_keyword_search_joins_risk_only_when_requested():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            risk_level="high",
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "JOIN risk_assessments" in sql
    assert "risk_assessments.company_id" in sql
    assert "lower(risk_assessments.risk_level)" in sql


@pytest.mark.asyncio
async def test_keyword_search_joins_business_impact_when_requested():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            business_impact="regulatory",
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "JOIN article_business_impacts" in sql
    assert "article_business_impacts.company_id" in sql
    assert (
        "lower(article_business_impacts.primary_category)"
        in sql
    )


@pytest.mark.asyncio
async def test_keyword_search_joins_event_cluster_when_requested():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            event_cluster_id=7,
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "JOIN event_cluster_memberships" in sql
    assert "event_cluster_memberships.company_id" in sql
    assert "event_cluster_memberships.cluster_id" in sql


@pytest.mark.asyncio
async def test_keyword_search_supports_combined_filters():
    db = make_db()

    await keyword_search(
        db,
        query="regulatory",
        company_id=2,
        filters=SearchFilters(
            sentiment="negative",
            risk_level="high",
            business_impact="regulatory",
            event_type="regulatory",
            event_cluster_id=7,
        ),
    )

    stmt = db.execute.await_args_list[0].args[0]
    sql = str(stmt)

    assert "JOIN article_sentiments" in sql
    assert "JOIN risk_assessments" in sql
    assert "JOIN article_business_impacts" in sql
    assert "JOIN event_cluster_memberships" in sql


@pytest.mark.asyncio
async def test_keyword_search_rejects_blank_query_before_database():
    db = make_db()

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        await keyword_search(
            db,
            query="   ",
            company_id=2,
        )

    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_keyword_search_returns_enriched_results(
    monkeypatch,
):
    article = SimpleNamespace(
        id=10,
        title="RBI regulatory update",
        source_name="Reuters",
        url="https://example.com/10",
        published_at=None,
    )

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [article],
        ),
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
        "app.services.discovery_service."
        "get_search_result_enrichments",
        enrichment_mock,
    )

    results = await keyword_search(
        db,
        query="regulatory",
        company_id=2,
    )

    assert len(results) == 1

    item = results[0]

    assert item.article_id == 10
    assert item.title == "RBI regulatory update"
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
async def test_keyword_search_allows_missing_enrichment(
    monkeypatch,
):
    article = SimpleNamespace(
        id=11,
        title="General update",
        source_name="Example",
        url="https://example.com/11",
        published_at=None,
    )

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [article],
        ),
    )

    enrichment_mock = AsyncMock(
        return_value={},
    )

    monkeypatch.setattr(
        "app.services.discovery_service."
        "get_search_result_enrichments",
        enrichment_mock,
    )

    results = await keyword_search(
        db,
        query="update",
        company_id=2,
    )

    assert len(results) == 1

    item = results[0]

    assert item.article_id == 11
    assert item.event_type is None
    assert item.sentiment is None
    assert item.risk_level is None
    assert item.risk_score is None
    assert item.business_impact is None
    assert item.event_cluster_id is None
