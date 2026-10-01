from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.tasks import report_tasks


class FakeScalars:
    def all(self):
        return [
            SimpleNamespace(
                id=2,
                name="VEE Technologies",
                is_active=True,
            )
        ]


class FakeResult:
    def scalars(self):
        return FakeScalars()


class FakeDB:
    def __init__(self):
        self.executed_statement = None

    async def execute(self, statement):
        self.executed_statement = statement
        return FakeResult()

    async def rollback(self):
        return None


class FakeSessionContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


@pytest.mark.asyncio
async def test_scheduled_reports_query_active_companies_only(
    monkeypatch,
):
    db = FakeDB()

    monkeypatch.setattr(
        report_tasks,
        "CeleryAsyncSessionLocal",
        lambda: FakeSessionContext(db),
    )

    generate_batch_mock = AsyncMock(
        return_value=[SimpleNamespace(batch_id="test-batch")]
    )

    monkeypatch.setattr(
        report_tasks,
        "generate_report_batch",
        generate_batch_mock,
    )

    result = await report_tasks._generate_scheduled_reports(
        "daily"
    )

    compiled_sql = str(
        db.executed_statement
    ).lower()

    assert "is_active" in compiled_sql
    assert "true" in compiled_sql

    generate_batch_mock.assert_awaited_once()

    kwargs = generate_batch_mock.await_args.kwargs

    assert kwargs["company_id"] == 2

    assert result == {
        "generated_batch_ids": ["test-batch"],
        "count": 1,
    }
