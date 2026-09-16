from unittest.mock import AsyncMock

import pytest

from app.models.article import Article
from app.services.article_competitor_analysis_service import (
    CompetitorArticleNotFoundError,
    analyze_article_competitors,
)
from app.services.competitor_profile_service import (
    CompetitorProfile,
)


def make_article(
    *,
    title: str,
    content: str | None = None,
) -> Article:
    return Article(
        id=901,
        source_name="Test Source",
        source_type="manual",
        title=title,
        url="https://example.com/test",
        cleaned_content=content,
        extraction_status="success",
        embedding_status="pending",
    )


@pytest.mark.asyncio
async def test_detected_competitor_is_persisted(
    monkeypatch,
):
    article = make_article(
        title="Competitor One launches new service",
        content="Competitor One expands operations.",
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_competitor_profile",
        AsyncMock(
            return_value=CompetitorProfile(
                company_id=2,
                competitors=[
                    "Competitor One",
                    "Competitor Two",
                ],
            )
        ),
    )

    persist_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "upsert_article_competitor_mentions",
        persist_mock,
    )

    result = await analyze_article_competitors(
        db=None,
        article_id=901,
        company_id=2,
    )

    assert result.article_id == 901
    assert result.company_id == 2
    assert result.competitors == [
        "Competitor One",
    ]

    persist_mock.assert_awaited_once_with(
        None,
        article_id=901,
        company_id=2,
        competitors=[
            "Competitor One",
        ],
    )


@pytest.mark.asyncio
async def test_unmentioned_competitor_stores_empty_list(
    monkeypatch,
):
    article = make_article(
        title="Vee Technologies expands",
        content="No configured competitor is mentioned.",
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_competitor_profile",
        AsyncMock(
            return_value=CompetitorProfile(
                company_id=2,
                competitors=[
                    "Competitor One",
                ],
            )
        ),
    )

    persist_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "upsert_article_competitor_mentions",
        persist_mock,
    )

    result = await analyze_article_competitors(
        db=None,
        article_id=901,
        company_id=2,
    )

    assert result.competitors == []

    persist_mock.assert_awaited_once_with(
        None,
        article_id=901,
        company_id=2,
        competitors=[],
    )


@pytest.mark.asyncio
async def test_empty_competitor_configuration_is_safe(
    monkeypatch,
):
    article = make_article(
        title="Vee Technologies update",
        content="General company news.",
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_competitor_profile",
        AsyncMock(
            return_value=CompetitorProfile(
                company_id=2,
                competitors=[],
            )
        ),
    )

    persist_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "upsert_article_competitor_mentions",
        persist_mock,
    )

    result = await analyze_article_competitors(
        db=None,
        article_id=901,
        company_id=2,
    )

    assert result.competitors == []

    persist_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_article_raises_error(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.article_competitor_analysis_service."
        "get_article",
        AsyncMock(return_value=None),
    )

    with pytest.raises(
        CompetitorArticleNotFoundError,
    ):
        await analyze_article_competitors(
            db=None,
            article_id=999,
            company_id=2,
        )
