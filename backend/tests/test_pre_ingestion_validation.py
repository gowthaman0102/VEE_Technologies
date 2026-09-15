from datetime import datetime, timedelta, timezone

import pytest

from app.ingestion.types import CollectedArticle
from app.processing.extractor import ExtractionResult
from app.services.active_company_profile_service import (
    ActiveCompanyProfile,
)
from app.services.pre_ingestion_validation_service import (
    validate_article_for_company,
)


PROFILE = ActiveCompanyProfile(
    company_id=2,
    company_name="VEE Technologies",
    aliases=[
        "VEE Technologies",
        "Vee Technologies",
    ],
)


class FakeExtractor:
    def __init__(
        self,
        content: str | None,
        success: bool = True,
    ):
        self.content = content
        self.success = success

    async def extract_from_url(
        self,
        url: str,
    ) -> ExtractionResult:
        return ExtractionResult(
            success=self.success,
            content=self.content,
            error=(
                None
                if self.success
                else "Extraction failed"
            ),
            final_url=url,
        )


@pytest.mark.asyncio
async def test_rejects_stale_article():
    article = CollectedArticle(
        source_name="Test",
        source_type="rss",
        title="Vee Technologies expands",
        url="https://example.com/stale",
        published_at=(
            datetime.now(timezone.utc)
            - timedelta(days=45)
        ),
    )

    result = await validate_article_for_company(
        article,
        PROFILE,
        max_age_days=30,
        extractor=FakeExtractor(
            "Vee Technologies article"
        ),
    )

    assert result.accepted is False
    assert result.reason == "stale"


@pytest.mark.asyncio
async def test_accepts_recent_relevant_article():
    article = CollectedArticle(
        source_name="Test",
        source_type="rss",
        title="Vee Technologies expands",
        url="https://example.com/relevant",
        published_at=datetime.now(
            timezone.utc
        ),
    )

    result = await validate_article_for_company(
        article,
        PROFILE,
        max_age_days=30,
        extractor=FakeExtractor(
            "Vee Technologies opened "
            "a new facility."
        ),
    )

    assert result.accepted is True
    assert result.reason == "accepted"


@pytest.mark.asyncio
async def test_rejects_recent_irrelevant_article():
    article = CollectedArticle(
        source_name="Test",
        source_type="newsapi",
        title="Global technology market grows",
        url="https://example.com/irrelevant",
        published_at=datetime.now(
            timezone.utc
        ),
    )

    result = await validate_article_for_company(
        article,
        PROFILE,
        max_age_days=30,
        extractor=FakeExtractor(
            "This article discusses unrelated "
            "technology companies."
        ),
    )

    assert result.accepted is False
    assert result.reason == "not_relevant"
