from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.analytics_service import (
    get_business_impact_distribution,
)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_business_impact_counts_all_categories():
    now = datetime.now(timezone.utc)

    timestamp = now - timedelta(hours=1)
    start = now - timedelta(days=30)
    end = now

    rows = [
        SimpleNamespace(
            primary_category="financial",
            categories=[
                "financial",
                "reputation",
            ],
            article_time=timestamp,
        ),
        SimpleNamespace(
            primary_category="financial",
            categories=[
                "financial",
                "customer",
                "reputation",
            ],
            article_time=timestamp,
        ),
    ]

    db = AsyncMock()
    db.execute.return_value = FakeResult(rows)

    result = await get_business_impact_distribution(
        db,
        company_id=2,
        start=start,
        end=end,
    )

    assert result["primary_distribution"]["financial"] == 2

    assert result["category_distribution"]["financial"] == 2
    assert result["category_distribution"]["reputation"] == 2
    assert result["category_distribution"]["customer"] == 1

    assert result["primary_distribution"]["reputation"] == 0


@pytest.mark.asyncio
async def test_business_impact_deduplicates_category_per_article():
    now = datetime.now(timezone.utc)

    timestamp = now - timedelta(hours=1)
    start = now - timedelta(days=30)
    end = now

    rows = [
        SimpleNamespace(
            primary_category="reputation",
            categories=[
                "reputation",
                "reputation",
                "customer",
            ],
            article_time=timestamp,
        ),
    ]

    db = AsyncMock()
    db.execute.return_value = FakeResult(rows)

    result = await get_business_impact_distribution(
        db,
        company_id=2,
        start=start,
        end=end,
    )

    assert result["category_distribution"]["reputation"] == 1
    assert result["category_distribution"]["customer"] == 1
