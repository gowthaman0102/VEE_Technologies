from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ingestion.runner import run_collector
from app.ingestion.types import CollectedArticle
from app.services.active_company_profile_service import (
    ActiveCompanyProfile,
)
from app.services.pre_ingestion_validation_service import (
    PreIngestionValidationResult,
)


class FakeCollector:
    async def collect(self):
        now = datetime.now(timezone.utc)

        return [
            CollectedArticle(
                source_name="Test",
                source_type="rss",
                external_id="1",
                title="Vee Technologies expands",
                url="https://example.com/1",
                published_at=now,
            ),
            CollectedArticle(
                source_name="Test",
                source_type="rss",
                external_id="2",
                title="Unrelated article",
                url="https://example.com/2",
                published_at=now,
            ),
        ]


@pytest.mark.asyncio
async def test_runner_saves_only_accepted_articles(
    monkeypatch,
):
    profile = ActiveCompanyProfile(
        company_id=2,
        company_name="VEE Technologies",
        aliases=[
            "VEE Technologies",
        ],
    )

    async def fake_get_profile(db):
        return profile

    async def fake_validator(
        article,
        company_profile,
    ):
        accepted = (
            "Vee Technologies"
            in article.title
        )

        return PreIngestionValidationResult(
            accepted=accepted,
            reason=(
                "accepted"
                if accepted
                else "not_relevant"
            ),
            resolved_url=article.url,
            extracted_content=None,
        )

    save_mock = AsyncMock(
        return_value=(
            SimpleNamespace(id=201),
            True,
        )
    )

    monkeypatch.setattr(
        "app.ingestion.runner."
        "get_active_company_profile",
        fake_get_profile,
    )

    monkeypatch.setattr(
        "app.ingestion.runner."
        "save_collected_article",
        save_mock,
    )

    result = await run_collector(
        db=None,
        collector=FakeCollector(),
        validator=fake_validator,
    )

    assert result.collected == 2
    assert result.inserted == 1
    assert result.skipped == 1
    assert result.inserted_article_ids == [201]

    assert save_mock.await_count == 1


@pytest.mark.asyncio
async def test_runner_duplicate_is_skipped_on_second_run(
    monkeypatch,
):
    profile = ActiveCompanyProfile(
        company_id=2,
        company_name="VEE Technologies",
        aliases=[
            "VEE Technologies",
        ],
    )

    class SingleArticleCollector:
        async def collect(self):
            return [
                CollectedArticle(
                    source_name="Test",
                    source_type="rss",
                    external_id="vee-live-001",
                    title=(
                        "Vee Technologies "
                        "opens new facility"
                    ),
                    url=(
                        "https://example.com/"
                        "vee-live-001"
                    ),
                    published_at=datetime.now(
                        timezone.utc
                    ),
                )
            ]

    async def fake_get_profile(db):
        return profile

    async def accept_validator(
        article,
        company_profile,
    ):
        return PreIngestionValidationResult(
            accepted=True,
            reason="accepted",
            resolved_url=article.url,
            extracted_content=(
                "Vee Technologies "
                "opened a new facility."
            ),
        )

    save_mock = AsyncMock(
        side_effect=[
            (SimpleNamespace(id=202), True),
            (SimpleNamespace(id=202), False),
        ]
    )

    monkeypatch.setattr(
        "app.ingestion.runner."
        "get_active_company_profile",
        fake_get_profile,
    )

    monkeypatch.setattr(
        "app.ingestion.runner."
        "save_collected_article",
        save_mock,
    )

    collector = SingleArticleCollector()

    first = await run_collector(
        db=None,
        collector=collector,
        validator=accept_validator,
    )

    second = await run_collector(
        db=None,
        collector=collector,
        validator=accept_validator,
    )

    assert first.collected == 1
    assert first.inserted == 1
    assert first.skipped == 0
    assert first.inserted_article_ids == [202]

    assert second.collected == 1
    assert second.inserted == 0
    assert second.skipped == 1
    assert second.inserted_article_ids == []

    assert save_mock.await_count == 2
