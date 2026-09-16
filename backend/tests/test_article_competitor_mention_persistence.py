from unittest.mock import AsyncMock, Mock

import pytest

from app.models.article_competitor_mention import (
    ArticleCompetitorMention,
)
from app.services import (
    article_competitor_mention_persistence_service,
)


@pytest.mark.asyncio
async def test_upsert_competitor_mentions_inserts_new(
    monkeypatch,
):
    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_competitor_mention_persistence_service,
        "get_article_competitor_mentions",
        AsyncMock(return_value=None),
    )

    created = await (
        article_competitor_mention_persistence_service
        .upsert_article_competitor_mentions(
            db,
            article_id=10,
            company_id=2,
            competitors=[
                "Competitor One",
                "Competitor Two",
            ],
        )
    )

    assert isinstance(
        created,
        ArticleCompetitorMention,
    )

    assert created.article_id == 10
    assert created.company_id == 2
    assert created.competitors == [
        "Competitor One",
        "Competitor Two",
    ]

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        created
    )


@pytest.mark.asyncio
async def test_upsert_competitor_mentions_updates_existing(
    monkeypatch,
):
    existing = ArticleCompetitorMention(
        article_id=10,
        company_id=2,
        competitors=[
            "Competitor One",
        ],
    )

    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_competitor_mention_persistence_service,
        "get_article_competitor_mentions",
        AsyncMock(
            return_value=existing
        ),
    )

    updated = await (
        article_competitor_mention_persistence_service
        .upsert_article_competitor_mentions(
            db,
            article_id=10,
            company_id=2,
            competitors=[
                "Competitor Two",
            ],
        )
    )

    assert updated is existing
    assert existing.competitors == [
        "Competitor Two",
    ]

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        existing
    )
