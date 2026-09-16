from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.tasks import processing_tasks


FAKE_DB = object()


class FakeSession:
    async def __aenter__(self):
        return FAKE_DB

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


@pytest.mark.asyncio
async def test_successful_embedding_queues_intelligence(
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

    embedding_mock = AsyncMock(
        return_value=SimpleNamespace(
            article_id=601,
            status="success",
            model="test-embedding-model",
            dimensions=384,
            error=None,
        )
    )

    monkeypatch.setattr(
        processing_tasks,
        "embed_article_by_id",
        embedding_mock,
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
    assert result["embedding_status"] == "success"
    assert (
        result["embedding_model"]
        == "test-embedding-model"
    )
    assert result["embedding_error"] is None
    assert result["intelligence_queued"] is True

    embedding_mock.assert_awaited_once_with(
        FAKE_DB,
        article_id=601,
    )

    send_task_mock.assert_called_once_with(
        "intelligence.process_article",
        args=[
            601,
            2,
        ],
    )


@pytest.mark.asyncio
async def test_embedding_failure_does_not_queue_intelligence(
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
                article_id=602,
                status="success",
                duplicate_of_id=None,
                content_hash="def456",
                error=None,
            )
        ),
    )

    monkeypatch.setattr(
        processing_tasks,
        "embed_article_by_id",
        AsyncMock(
            return_value=SimpleNamespace(
                article_id=602,
                status="failed",
                model=None,
                dimensions=None,
                error="Embedding failed",
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

    assert result["status"] == "success"
    assert result["embedding_status"] == "failed"
    assert result["embedding_model"] is None
    assert result["embedding_error"] == (
        "Embedding failed"
    )
    assert result["intelligence_queued"] is False

    send_task_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        "skipped",
        "failed",
    ],
)
async def test_non_success_does_not_run_embedding_or_intelligence(
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
                article_id=603,
                status=status,
                duplicate_of_id=10,
                content_hash=None,
                error="test",
            )
        ),
    )

    embedding_mock = AsyncMock()

    monkeypatch.setattr(
        processing_tasks,
        "embed_article_by_id",
        embedding_mock,
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
            article_id=603,
            company_id=2,
        )
    )

    assert result["status"] == status
    assert result["embedding_status"] == "not_run"
    assert result["intelligence_queued"] is False

    embedding_mock.assert_not_awaited()
    send_task_mock.assert_not_called()


@pytest.mark.asyncio
async def test_not_found_does_not_run_embedding_or_intelligence(
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

    embedding_mock = AsyncMock()

    monkeypatch.setattr(
        processing_tasks,
        "embed_article_by_id",
        embedding_mock,
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
    assert result["embedding_status"] == "not_run"
    assert result["intelligence_queued"] is False

    embedding_mock.assert_not_awaited()
    send_task_mock.assert_not_called()
