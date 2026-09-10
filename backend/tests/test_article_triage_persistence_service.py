from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.article_triage import ArticleTriage
from app.schemas.article_triage import ArticleTriageResult
from app.services.article_triage_persistence_service import (
    save_article_triage,
)


def make_triage():
    return ArticleTriageResult(
        company_name="PayU",
        event_type="regulatory_action",
        summary="PayU received RBI approval.",
        why_it_matters="This supports regulated operations.",
        evidence=[
            "RBI granted final approval."
        ],
        potential_impact="PayU can expand payment operations.",
        urgency="high",
        confidence=0.9,
    )


@pytest.mark.asyncio
async def test_save_article_triage_creates_new_record():
    db = AsyncMock()
    db.add = MagicMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    saved_record = ArticleTriage(
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type="regulatory_action",
        summary="PayU received RBI approval.",
        why_it_matters="This supports regulated operations.",
        evidence=[
            "RBI granted final approval."
        ],
        potential_impact="PayU can expand payment operations.",
        urgency="high",
        confidence=0.9,
        llm_model="test-model",
    )

    async def refresh_side_effect(record):
        record.id = 1

    db.refresh.side_effect = refresh_side_effect

    result = await save_article_triage(
        db,
        article_id=8,
        company_id=1,
        model="test-model",
        triage=make_triage(),
    )

    assert result.article_id == 8
    assert result.company_id == 1
    assert result.company_name == "PayU"
    assert result.event_type == "regulatory_action"
    assert result.llm_model == "test-model"

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_article_triage_updates_existing_record():
    existing = ArticleTriage(
        id=1,
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type="other",
        summary="Old summary",
        why_it_matters="Old reason",
        evidence=["Old evidence"],
        potential_impact="Old impact",
        urgency="low",
        confidence=0.2,
        llm_model="old-model",
    )

    db = AsyncMock()
    db.add = MagicMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing
    db.execute.return_value = execute_result

    result = await save_article_triage(
        db,
        article_id=8,
        company_id=1,
        model="test-model",
        triage=make_triage(),
    )

    assert result is existing
    assert result.event_type == "regulatory_action"
    assert result.summary == "PayU received RBI approval."
    assert result.urgency == "high"
    assert result.confidence == 0.9
    assert result.llm_model == "test-model"

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
