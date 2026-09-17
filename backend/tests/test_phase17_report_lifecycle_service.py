from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import report_service


START = datetime(
    2026,
    8,
    1,
    tzinfo=timezone.utc,
)

END = datetime(
    2026,
    9,
    1,
    tzinfo=timezone.utc,
)


def _record(
    *,
    status="pending",
    error=None,
):
    return SimpleNamespace(
        id=101,
        company_id=2,
        report_type="monthly",
        file_format="pdf",
        period_start=datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        ),
        period_end=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        filename=None,
        content_type=None,
        content=None,
        status=status,
        generated_at=None,
        error=error,
    )


@pytest.mark.asyncio
async def test_create_pending_report_creates_pending_record(
    monkeypatch,
):
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    monkeypatch.setattr(
        report_service,
        "find_existing_report",
        AsyncMock(return_value=None),
    )

    record = await report_service.create_pending_report(
        db,
        company_id=2,
        report_type="monthly",
        file_format="pdf",
        period_start=datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        ),
        period_end=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert record.status == "pending"
    assert record.filename is None
    assert record.content_type is None
    assert record.content is None
    assert record.generated_at is None
    assert record.error is None

    db.add.assert_called_once_with(record)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(record)


@pytest.mark.asyncio
async def test_create_pending_report_returns_existing_duplicate(
    monkeypatch,
):
    db = AsyncMock()
    existing = _record(
        status="success"
    )

    find_mock = AsyncMock(
        return_value=existing
    )

    monkeypatch.setattr(
        report_service,
        "find_existing_report",
        find_mock,
    )

    result = await report_service.create_pending_report(
        db,
        company_id=2,
        report_type="monthly",
        file_format="pdf",
        period_start=existing.period_start,
        period_end=existing.period_end,
    )

    assert result is existing

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_report_processing_transition():
    db = AsyncMock()
    record = _record(
        status="pending",
        error="old error",
    )

    result = await report_service.mark_report_processing(
        db,
        record,
    )

    assert result is record
    assert record.status == "processing"
    assert record.error is None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(record)


@pytest.mark.asyncio
async def test_mark_report_success_transition():
    db = AsyncMock()
    record = _record(
        status="processing"
    )

    content = b"%PDF-lifecycle-test"

    result = await report_service.mark_report_success(
        db,
        record,
        content=content,
    )

    assert result is record
    assert record.status == "success"
    assert record.content == content
    assert record.content_type == "application/pdf"
    assert record.filename is not None
    assert record.filename.endswith(".pdf")
    assert record.generated_at is not None
    assert record.error is None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(record)


@pytest.mark.asyncio
async def test_mark_report_failed_transition():
    db = AsyncMock()
    record = _record(
        status="processing"
    )

    record.filename = "old.pdf"
    record.content_type = "application/pdf"
    record.content = b"old"
    record.generated_at = datetime.now(
        timezone.utc
    )

    result = await report_service.mark_report_failed(
        db,
        record,
        error="Renderer failed",
    )

    assert result is record
    assert record.status == "failed"
    assert record.error == "Renderer failed"
    assert record.filename is None
    assert record.content_type is None
    assert record.content is None
    assert record.generated_at is None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(record)

@pytest.mark.asyncio
async def test_generate_report_record_runs_full_success_lifecycle(
    monkeypatch,
):
    db = MagicMock()

    pending = _record(
        status="pending"
    )

    processing = _record(
        status="processing"
    )

    success = _record(
        status="success"
    )
    success.content = b"%PDF-real-render"
    success.filename = "report.pdf"
    success.content_type = "application/pdf"

    create_mock = AsyncMock(
        return_value=pending
    )
    async def mark_processing_side_effect(
        db_arg,
        record,
    ):
        record.status = "processing"
        record.error = None
        return record

    processing_mock = AsyncMock(
        side_effect=mark_processing_side_effect
    )
    success_mock = AsyncMock(
        return_value=success
    )

    build_mock = AsyncMock(
        return_value={
            "company_id": 2,
            "company_name": "VEE Technologies",
            "total_articles": 0,
        }
    )

    render_mock = MagicMock(
        return_value=b"%PDF-real-render"
    )

    monkeypatch.setattr(
        report_service,
        "create_pending_report",
        create_mock,
    )

    monkeypatch.setattr(
        report_service,
        "mark_report_processing",
        processing_mock,
    )

    monkeypatch.setattr(
        report_service,
        "build_company_report",
        build_mock,
    )

    monkeypatch.setattr(
        report_service,
        "render_report",
        render_mock,
    )

    monkeypatch.setattr(
        report_service,
        "mark_report_success",
        success_mock,
    )

    result = await report_service.generate_report_record(
        db,
        company_id=2,
        report_type="monthly",
        file_format="pdf",
        period_start=START,
        period_end=END,
    )

    assert result is success

    create_mock.assert_awaited_once()

    processing_mock.assert_awaited_once_with(
        db,
        pending,
    )

    build_mock.assert_awaited_once_with(
        db,
        company_id=2,
        start_date=START,
        end_date=END,
    )

    render_mock.assert_called_once()

    success_mock.assert_awaited_once()

    success_kwargs = (
        success_mock.await_args.kwargs
    )

    assert (
        success_kwargs["content"]
        == b"%PDF-real-render"
    )


@pytest.mark.asyncio
async def test_generate_report_record_marks_failed_on_error(
    monkeypatch,
):
    db = MagicMock()

    pending = _record(
        status="pending"
    )

    processing = _record(
        status="processing"
    )

    create_mock = AsyncMock(
        return_value=pending
    )

    async def mark_processing_side_effect(
        db_arg,
        record,
    ):
        record.status = "processing"
        record.error = None
        return record

    processing_mock = AsyncMock(
        side_effect=mark_processing_side_effect
    )

    failure_mock = AsyncMock(
        return_value=_record(
            status="failed",
            error="Renderer failed",
        )
    )

    monkeypatch.setattr(
        report_service,
        "create_pending_report",
        create_mock,
    )

    monkeypatch.setattr(
        report_service,
        "mark_report_processing",
        processing_mock,
    )

    monkeypatch.setattr(
        report_service,
        "build_company_report",
        AsyncMock(
            return_value={
                "company_id": 2,
            }
        ),
    )

    monkeypatch.setattr(
        report_service,
        "render_report",
        MagicMock(
            side_effect=RuntimeError(
                "Renderer failed"
            )
        ),
    )

    monkeypatch.setattr(
        report_service,
        "mark_report_failed",
        failure_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="Renderer failed",
    ):
        await report_service.generate_report_record(
            db,
            company_id=2,
            report_type="monthly",
            file_format="pdf",
            period_start=START,
            period_end=END,
        )

    failure_mock.assert_awaited_once()

    failed_args = (
        failure_mock.await_args.args
    )

    assert failed_args[0] is db
    assert failed_args[1] is pending

    failed_kwargs = (
        failure_mock.await_args.kwargs
    )

    assert failed_kwargs["error"] == (
        "Renderer failed"
    )
