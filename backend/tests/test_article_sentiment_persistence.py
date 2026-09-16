from unittest.mock import AsyncMock, Mock

import pytest

from app.models.article_sentiment import ArticleSentiment
from app.schemas.article_sentiment import (
    ArticleSentimentResult,
)
from app.services import (
    article_sentiment_persistence_service,
)


@pytest.mark.asyncio
async def test_upsert_article_sentiment_inserts_new(
    monkeypatch,
):
    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_sentiment_persistence_service,
        "get_article_sentiment",
        AsyncMock(return_value=None),
    )

    result = ArticleSentimentResult(
        label="positive",
        score=0.91,
        reason="Positive business development.",
        model="test-model",
    )

    created = await (
        article_sentiment_persistence_service
        .upsert_article_sentiment(
            db,
            article_id=10,
            company_id=2,
            result=result,
        )
    )

    assert isinstance(
        created,
        ArticleSentiment,
    )

    assert created.article_id == 10
    assert created.company_id == 2
    assert created.label == "positive"
    assert created.score == 0.91
    assert created.reason == (
        "Positive business development."
    )
    assert created.model == "test-model"

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        created
    )


@pytest.mark.asyncio
async def test_upsert_article_sentiment_updates_existing(
    monkeypatch,
):
    existing = ArticleSentiment(
        article_id=10,
        company_id=2,
        label="neutral",
        score=0.55,
        reason="Initial assessment.",
        model="old-model",
    )

    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        article_sentiment_persistence_service,
        "get_article_sentiment",
        AsyncMock(
            return_value=existing
        ),
    )

    result = ArticleSentimentResult(
        label="negative",
        score=0.88,
        reason="Negative impact detected.",
        model="new-model",
    )

    updated = await (
        article_sentiment_persistence_service
        .upsert_article_sentiment(
            db,
            article_id=10,
            company_id=2,
            result=result,
        )
    )

    assert updated is existing

    assert existing.label == "negative"
    assert existing.score == 0.88
    assert existing.reason == (
        "Negative impact detected."
    )
    assert existing.model == "new-model"

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        existing
    )
