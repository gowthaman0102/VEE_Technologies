from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.article_recovery_service import (
    queue_incomplete_active_articles,
)


@pytest.mark.asyncio
async def test_recovery_queues_processing_and_intelligence_only_for_incomplete_articles():
    db = AsyncMock()
    articles = [
        SimpleNamespace(
            id=1,
            extraction_status="pending",
            embedding_status="pending",
        ),
        SimpleNamespace(
            id=2,
            extraction_status="success",
            embedding_status="success",
        ),
        SimpleNamespace(
            id=3,
            extraction_status="success",
            embedding_status="success",
        ),
        SimpleNamespace(
            id=4,
            extraction_status="skipped",
            embedding_status="pending",
        ),
    ]
    profile = SimpleNamespace(company_id=42)

    def result_for(article_ids):
        result = MagicMock()
        result.scalars.return_value.all.return_value = article_ids
        return result

    db.execute.side_effect = [
        MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    all=MagicMock(return_value=articles)
                )
            )
        ),
        result_for([2, 3]),
        result_for([2, 3]),
        result_for([2, 3]),
        result_for([2, 3]),
        result_for([2, 3]),
        result_for([2, 3]),
        result_for([3]),
    ]

    with patch(
        "app.services.article_recovery_service.get_active_company_profile",
        new=AsyncMock(return_value=profile),
    ), patch(
        "app.services.article_recovery_service.celery_app.send_task",
    ) as send_task:
        result = await queue_incomplete_active_articles(db)

    assert result.requested == 4
    assert result.queued_processing == 1
    assert result.queued_intelligence == 1
    assert result.already_complete == 2
    assert send_task.call_count == 2
    assert send_task.call_args_list[0].args[0] == "processing.process_article"
    assert send_task.call_args_list[1].args[0] == "intelligence.process_article"