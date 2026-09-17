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

    build_mock = AsyncMock(
        return_value={
            "company_id": 2,
            "start_date": None,
            "end_date": None,
        }
    )

    monkeypatch.setattr(
        report_tasks,
        "build_company_report",
        build_mock,
    )

    monkeypatch.setattr(
        report_tasks,
        "render_report",
        MagicMock(
            return_value=b"%PDF-test"
        ),
    )

    persist_mock = AsyncMock(
        return_value=SimpleNamespace(
            id=501
        )
    )

    monkeypatch.setattr(
        report_tasks,
        "persist_generated_report",
        persist_mock,
    )

    result = await report_tasks._generate_scheduled_reports(
        "daily"
    )

    compiled_sql = str(
        db.executed_statement
    ).lower()

    assert "is_active" in compiled_sql
    assert "true" in compiled_sql

    build_mock.assert_awaited_once()

    kwargs = build_mock.await_args.kwargs

    assert kwargs["company_id"] == 2

    persist_mock.assert_awaited_once()

    assert result == {
        "generated_report_ids": [501],
        "count": 1,
    }
