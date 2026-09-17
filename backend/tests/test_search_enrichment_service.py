from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.search_enrichment_service import (
    SearchResultEnrichment,
    get_search_result_enrichments,
)


@pytest.mark.asyncio
async def test_empty_article_ids_skip_database():
    db = AsyncMock()

    result = await get_search_result_enrichments(
        db,
        article_ids=[],
        company_id=2,
    )

    assert result == {}
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_enrichment_maps_stored_fields():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                article_id=10,
                event_type="regulatory_action",
                sentiment="negative",
                risk_level="high",
                risk_score=82.5,
                business_impact="regulatory",
                event_cluster_id=7,
            ),
        ],
    )

    result = await get_search_result_enrichments(
        db,
        article_ids=[10],
        company_id=2,
    )

    assert result == {
        10: SearchResultEnrichment(
            event_type="regulatory_action",
            sentiment="negative",
            risk_level="high",
            risk_score=82.5,
            business_impact="regulatory",
            event_cluster_id=7,
        )
    }


@pytest.mark.asyncio
async def test_search_enrichment_allows_missing_analysis():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                article_id=11,
                event_type="other",
                sentiment=None,
                risk_level=None,
                risk_score=None,
                business_impact=None,
                event_cluster_id=None,
            ),
        ],
    )

    result = await get_search_result_enrichments(
        db,
        article_ids=[11],
        company_id=2,
    )

    item = result[11]

    assert item.event_type == "other"
    assert item.sentiment is None
    assert item.risk_level is None
    assert item.risk_score is None
    assert item.business_impact is None
    assert item.event_cluster_id is None


@pytest.mark.asyncio
async def test_search_enrichment_query_is_company_scoped():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [],
    )

    await get_search_result_enrichments(
        db,
        article_ids=[10, 11],
        company_id=2,
    )

    statement = db.execute.await_args.args[0]
    sql = str(statement)

    assert "article_triages.company_id" in sql
    assert "article_sentiments.company_id" in sql
    assert "risk_assessments.company_id" in sql
    assert "article_business_impacts.company_id" in sql
    assert "event_cluster_memberships.company_id" in sql


@pytest.mark.asyncio
async def test_search_enrichment_uses_outer_joins_for_optional_data():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [],
    )

    await get_search_result_enrichments(
        db,
        article_ids=[10],
        company_id=2,
    )

    statement = db.execute.await_args.args[0]
    sql = str(statement)

    assert "LEFT OUTER JOIN article_sentiments" in sql
    assert "LEFT OUTER JOIN risk_assessments" in sql
    assert "LEFT OUTER JOIN article_business_impacts" in sql
    assert "LEFT OUTER JOIN event_cluster_memberships" in sql
