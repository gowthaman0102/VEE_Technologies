from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.competitor_profile_service import (
    get_competitor_profile,
)


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return FakeScalars(self.values)


@pytest.mark.asyncio
async def test_competitor_profile_returns_only_query_results():
    db = AsyncMock()

    db.execute.return_value = FakeResult(
        [
            "Competitor One",
            "Competitor Two",
        ]
    )

    profile = await get_competitor_profile(
        db,
        company_id=2,
    )

    assert profile.company_id == 2
    assert profile.competitors == [
        "Competitor One",
        "Competitor Two",
    ]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_competitor_profile_cleans_blank_names():
    db = AsyncMock()

    db.execute.return_value = FakeResult(
        [
            " Competitor One ",
            "",
            "   ",
            None,
            "Competitor Two",
        ]
    )

    profile = await get_competitor_profile(
        db,
        company_id=2,
    )

    assert profile.competitors == [
        "Competitor One",
        "Competitor Two",
    ]


@pytest.mark.asyncio
async def test_competitor_profile_allows_empty_configuration():
    db = AsyncMock()

    db.execute.return_value = FakeResult([])

    profile = await get_competitor_profile(
        db,
        company_id=2,
    )

    assert profile.company_id == 2
    assert profile.competitors == []
