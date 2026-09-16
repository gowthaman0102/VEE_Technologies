from unittest.mock import AsyncMock, Mock

import pytest

from app.models.article_business_impact import (
    ArticleBusinessImpact,
)
from app.schemas.article_business_impact import (
    ArticleBusinessImpactResult,
)
from app.services import (
    article_business_impact_persistence_service,
)


@pytest.mark.asyncio
async def test_upsert_business_impact_inserts_new(
    monkeypatch,
):
    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_business_impact_persistence_service,
        "get_article_business_impact",
        AsyncMock(return_value=None),
    )

    result = ArticleBusinessImpactResult(
        primary_category="market",
        categories=[
            "market",
            "competitive",
        ],
        impact_summary=(
            "The article indicates a market expansion "
            "opportunity for the company."
        ),
        evidence=[
            "The company announced expansion into "
            "a new market."
        ],
        model="test-model",
    )

    created = await (
        article_business_impact_persistence_service
        .upsert_article_business_impact(
            db,
            article_id=10,
            company_id=2,
            result=result,
        )
    )

    assert isinstance(
        created,
        ArticleBusinessImpact,
    )

    assert created.article_id == 10
    assert created.company_id == 2
    assert created.primary_category == "market"

    assert created.categories == [
        "market",
        "competitive",
    ]

    assert (
        created.impact_summary
        == result.impact_summary
    )

    assert created.evidence == result.evidence
    assert created.model == "test-model"

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        created
    )


@pytest.mark.asyncio
async def test_upsert_business_impact_updates_existing(
    monkeypatch,
):
    existing = ArticleBusinessImpact(
        article_id=10,
        company_id=2,
        primary_category="market",
        categories=[
            "market",
        ],
        impact_summary=(
            "Initial impact assessment."
        ),
        evidence=[
            "Initial evidence."
        ],
        model="old-model",
    )

    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_business_impact_persistence_service,
        "get_article_business_impact",
        AsyncMock(
            return_value=existing
        ),
    )

    result = ArticleBusinessImpactResult(
        primary_category="financial",
        categories=[
            "financial",
            "market",
        ],
        impact_summary=(
            "The updated assessment indicates "
            "financial and market impact."
        ),
        evidence=[
            "Revenue growth was reported.",
            "Market expansion was announced.",
        ],
        model="new-model",
    )

    updated = await (
        article_business_impact_persistence_service
        .upsert_article_business_impact(
            db,
            article_id=10,
            company_id=2,
            result=result,
        )
    )

    assert updated is existing

    assert (
        existing.primary_category
        == "financial"
    )

    assert existing.categories == [
        "financial",
        "market",
    ]

    assert (
        existing.impact_summary
        == result.impact_summary
    )

    assert existing.evidence == result.evidence
    assert existing.model == "new-model"

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        existing
    )
