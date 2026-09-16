from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.tasks import ingestion_tasks


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
async def test_run_live_ingestion_queues_processing(
    monkeypatch,
):
    fake_sources = [
        SimpleNamespace(key="source-a"),
        SimpleNamespace(key="source-b"),
    ]

    fake_results = [
        SimpleNamespace(
            source_key="source-a",
            source_name="Source A",
            collected=4,
            inserted=2,
            skipped=2,
            inserted_article_ids=[
                501,
                502,
            ],
            error=None,
        ),
        SimpleNamespace(
            source_key="source-b",
            source_name="Source B",
            collected=3,
            inserted=1,
            skipped=2,
            inserted_article_ids=[
                503,
            ],
            error=None,
        ),
    ]

    monkeypatch.setattr(
        ingestion_tasks,
        "get_enabled_sources",
        lambda: fake_sources,
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "get_active_company_profile",
        AsyncMock(
            return_value=SimpleNamespace(
                company_id=2,
                company_name="VEE Technologies",
            )
        ),
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "run_sources",
        AsyncMock(
            return_value=fake_results
        ),
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    send_task_mock = Mock()

    monkeypatch.setattr(
        ingestion_tasks.celery_app,
        "send_task",
        send_task_mock,
    )

    result = await (
        ingestion_tasks
        ._run_live_ingestion()
    )

    assert result["total_collected"] == 7
    assert result["total_inserted"] == 3
    assert result["total_skipped"] == 4

    assert result[
        "inserted_article_ids"
    ] == [
        501,
        502,
        503,
    ]

    assert result[
        "processing_tasks_queued"
    ] == 3

    assert send_task_mock.call_count == 3

    send_task_mock.assert_any_call(
        "processing.process_article",
        args=[
            501,
            2,
        ],
    )

    send_task_mock.assert_any_call(
        "processing.process_article",
        args=[
            502,
            2,
        ],
    )

    send_task_mock.assert_any_call(
        "processing.process_article",
        args=[
            503,
            2,
        ],
    )


@pytest.mark.asyncio
async def test_run_live_ingestion_with_no_new_articles(
    monkeypatch,
):
    fake_results = [
        SimpleNamespace(
            source_key="source-a",
            source_name="Source A",
            collected=2,
            inserted=0,
            skipped=2,
            inserted_article_ids=[],
            error=None,
        ),
    ]

    monkeypatch.setattr(
        ingestion_tasks,
        "get_enabled_sources",
        lambda: [
            SimpleNamespace(
                key="source-a"
            )
        ],
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "get_active_company_profile",
        AsyncMock(
            return_value=SimpleNamespace(
                company_id=2,
                company_name="VEE Technologies",
            )
        ),
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "run_sources",
        AsyncMock(
            return_value=fake_results
        ),
    )

    monkeypatch.setattr(
        ingestion_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    send_task_mock = Mock()

    monkeypatch.setattr(
        ingestion_tasks.celery_app,
        "send_task",
        send_task_mock,
    )

    result = await (
        ingestion_tasks
        ._run_live_ingestion()
    )

    assert result["total_inserted"] == 0
    assert result["inserted_article_ids"] == []
    assert result["processing_tasks_queued"] == 0

    send_task_mock.assert_not_called()
