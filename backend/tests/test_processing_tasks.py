from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.tasks import processing_tasks


class FakeSession:
    async def __aenter__(self):
        return object()

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


@pytest.mark.asyncio
async def test_success_queues_intelligence(
    monkeypatch,
):
    monkeypatch.setattr(
        processing_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    monkeypatch.setattr(
        processing_tasks,
        "process_article_by_id",
        AsyncMock(
            return_value=SimpleNamespace(
                article_id=601,
                status="success",
                duplicate_of_id=None,
                content_hash="abc123",
                error=None,
            )
        ),
    )

    send_task_mock = Mock()

    monkeypatch.setattr(
        processing_tasks.celery_app,
        "send_task",
        send_task_mock,
    )

    result = await (
        processing_tasks
        ._process_article_pipeline(
            article_id=601,
            company_id=2,
        )
    )

    assert result["status"] == "success"
    assert result["intelligence_queued"] is True

    send_task_mock.assert_called_once_with(
        "intelligence.process_article",
        args=[
            601,
            2,
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        "skipped",
        "failed",
    ],
)
async def test_non_success_does_not_queue_intelligence(
    monkeypatch,
    status,
):
    monkeypatch.setattr(
        processing_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    monkeypatch.setattr(
        processing_tasks,
        "process_article_by_id",
        AsyncMock(
            return_value=SimpleNamespace(
                article_id=602,
                status=status,
                duplicate_of_id=10,
                content_hash=None,
                error="test",
            )
        ),
    )

    send_task_mock = Mock()

    monkeypatch.setattr(
        processing_tasks.celery_app,
        "send_task",
        send_task_mock,
    )

    result = await (
        processing_tasks
        ._process_article_pipeline(
            article_id=602,
            company_id=2,
        )
    )

    assert result["status"] == status
    assert result["intelligence_queued"] is False

    send_task_mock.assert_not_called()


@pytest.mark.asyncio
async def test_not_found_does_not_queue_intelligence(
    monkeypatch,
):
    monkeypatch.setattr(
        processing_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    monkeypatch.setattr(
        processing_tasks,
        "process_article_by_id",
        AsyncMock(return_value=None),
    )

    send_task_mock = Mock()

    monkeypatch.setattr(
        processing_tasks.celery_app,
        "send_task",
        send_task_mock,
    )

    result = await (
        processing_tasks
        ._process_article_pipeline(
            article_id=999,
            company_id=2,
        )
    )

    assert result["status"] == "not_found"
    assert result["intelligence_queued"] is False

    send_task_mock.assert_not_called()
