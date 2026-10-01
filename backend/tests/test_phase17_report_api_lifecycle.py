from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import reports
from app.db.session import get_db
from app.main import app


client = TestClient(app)


class FakeDB:
    def __init__(self, record=None):
        self.record = record
        self.deleted = None
        self.committed = False

    async def get(self, model, report_id):
        return self.record

    async def rollback(self):
        return None

    async def delete(self, record):
        self.deleted = record

    async def commit(self):
        self.committed = True


def _record(
    *,
    status="success",
    content=b"%PDF-test",
    filename="report.pdf",
    content_type="application/pdf",
    error=None,
):
    return SimpleNamespace(
        id=123,
        company_id=2,
        report_type="custom",
        report_template="detailed",
        report_scope="standard",
        scope_metadata={},
        file_format="pdf",
        filename=filename,
        content_type=content_type,
        period_start=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        period_end=datetime(
            2026,
            9,
            2,
            tzinfo=timezone.utc,
        ),
        status=status,
        generated_at=(
            datetime(
                2026,
                9,
                2,
                tzinfo=timezone.utc,
            )
            if status == "success"
            else None
        ),
        error=error,
        content=content,
    )


def test_delete_report_removes_record(monkeypatch):
    record = _record()
    database = FakeDB(record)

    async def override_db():
        yield database

    app.dependency_overrides[get_db] = override_db
    try:
        response = client.delete("/api/v1/reports/123")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert database.deleted is record
    assert database.committed is True


def test_delete_report_returns_not_found():
    database = FakeDB()

    async def override_db():
        yield database

    app.dependency_overrides[get_db] = override_db
    try:
        response = client.delete("/api/v1/reports/404")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_analytics_snapshot_is_stored_with_range_metadata():
    class SnapshotDB:
        saved_report = None

        async def get(self, model, company_id):
            return SimpleNamespace(id=company_id)

        def add(self, report):
            self.saved_report = report

        async def commit(self):
            return None

        async def refresh(self, report):
            report.id = 456

    database = SnapshotDB()

    async def override_db():
        yield database

    app.dependency_overrides[get_db] = override_db
    try:
        response = client.post(
            "/api/v1/reports/analytics-snapshot",
            data={
                "company_id": "2",
                "period_start": "2026-09-01T00:00:00+00:00",
                "period_end": "2026-09-02T00:00:00+00:00",
                "time_mode": "media",
                "preset": "90d",
            },
            files={
                "snapshot": (
                    "analytics.png",
                    b"\x89PNG\r\n\x1a\nimage-bytes",
                    "image/png",
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert database.saved_report.report_scope == "analytics_snapshot"
    assert database.saved_report.file_format == "png"
    assert database.saved_report.content_type == "image/png"
    assert database.saved_report.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert database.saved_report.scope_metadata["preset"] == "90d"
    assert response.json()["filename"] == database.saved_report.filename


def test_generate_report_returns_lifecycle_state(
    monkeypatch,
):
    generated = _record()

    generation_mock = AsyncMock(
        return_value=generated
    )

    monkeypatch.setattr(
        reports,
        "generate_report_record",
        generation_mock,
    )

    response = client.post(
        "/api/v1/reports/generate",
        json={
            "company_id": 2,
            "report_type": "custom",
            "start_date": (
                "2026-09-01T00:00:00+00:00"
            ),
            "end_date": (
                "2026-09-02T00:00:00+00:00"
            ),
            "format": "pdf",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["report_id"] == 123
    assert data["status"] == "success"
    assert data["filename"] == "report.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["error"] is None


def test_generate_report_exposes_failed_state(
    monkeypatch,
):
    generated = _record(
        status="failed",
        content=None,
        filename=None,
        content_type=None,
        error="Generation failed",
    )

    monkeypatch.setattr(
        reports,
        "generate_report_record",
        AsyncMock(return_value=generated),
    )

    response = client.post(
        "/api/v1/reports/generate",
        json={
            "company_id": 2,
            "report_type": "custom",
            "start_date": (
                "2026-09-01T00:00:00+00:00"
            ),
            "end_date": (
                "2026-09-02T00:00:00+00:00"
            ),
            "format": "pdf",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["filename"] is None
    assert data["content_type"] is None
    assert data["error"] == "Generation failed"


def test_export_report_uses_lifecycle_record(
    monkeypatch,
):
    generated = _record()

    monkeypatch.setattr(
        reports,
        "generate_report_record",
        AsyncMock(return_value=generated),
    )

    response = client.post(
        "/api/v1/reports/export",
        json={
            "company_id": 2,
            "report_type": "custom",
            "start_date": (
                "2026-09-01T00:00:00+00:00"
            ),
            "end_date": (
                "2026-09-02T00:00:00+00:00"
            ),
            "format": "pdf",
        },
    )

    assert response.status_code == 200
    assert response.content == b"%PDF-test"
    assert response.headers["x-report-id"] == "123"
    assert (
        response.headers["content-type"]
        == "application/pdf"
    )


def test_export_rejects_non_success_record(
    monkeypatch,
):
    generated = _record(
        status="processing",
        content=None,
        filename=None,
        content_type=None,
    )

    monkeypatch.setattr(
        reports,
        "generate_report_record",
        AsyncMock(return_value=generated),
    )

    response = client.post(
        "/api/v1/reports/export",
        json={
            "company_id": 2,
            "report_type": "custom",
            "start_date": (
                "2026-09-01T00:00:00+00:00"
            ),
            "end_date": (
                "2026-09-02T00:00:00+00:00"
            ),
            "format": "pdf",
        },
    )

    assert response.status_code == 409


def test_download_returns_404_for_missing_report():
    async def override_db():
        yield FakeDB(record=None)

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/999/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Report not found."
    )


def test_download_rejects_processing_report():
    async def override_db():
        yield FakeDB(
            record=_record(
                status="processing",
                content=None,
                filename=None,
                content_type=None,
            )
        )

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/123/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Report is not ready for download."
    )


def test_download_rejects_incomplete_success_report():
    async def override_db():
        yield FakeDB(
            record=_record(
                status="success",
                content=None,
            )
        )

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/123/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Report file is incomplete "
        "and cannot be downloaded."
    )


def test_download_success_returns_file():
    async def override_db():
        yield FakeDB(
            record=_record()
        )

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/123/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 200
    assert response.content == b"%PDF-test"
    assert (
        response.headers["content-type"]
        == "application/pdf"
    )

def test_download_rejects_pending_report():
    async def override_db():
        yield FakeDB(
            record=_record(
                status="pending",
                content=None,
                filename=None,
                content_type=None,
            )
        )

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/123/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Report is not ready for download."
    )


def test_download_rejects_failed_report():
    async def override_db():
        yield FakeDB(
            record=_record(
                status="failed",
                content=None,
                filename=None,
                content_type=None,
                error="Generation failed",
            )
        )

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/123/download"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Report is not ready for download."
    )

def test_report_history_exposes_status_and_error():
    from unittest.mock import MagicMock

    success_record = _record(
        status="success",
    )
    success_record.created_at = datetime(
        2026,
        9,
        2,
        10,
        0,
        tzinfo=timezone.utc,
    )

    failed_record = _record(
        status="failed",
        content=None,
        filename=None,
        content_type=None,
        error="Renderer failed",
    )
    failed_record.id = 124
    failed_record.created_at = datetime(
        2026,
        9,
        2,
        11,
        0,
        tzinfo=timezone.utc,
    )

    result = MagicMock()

    result.scalars.return_value.all.return_value = [
        failed_record,
        success_record,
    ]

    class HistoryDB:
        async def execute(self, statement):
            return result

    async def override_db():
        yield HistoryDB()

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get(
            "/api/v1/reports/history",
            params={
                "company_id": 2,
                "limit": 10,
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2

    assert data["items"][0]["id"] == 124
    assert data["items"][0]["status"] == "failed"
    assert data["items"][0]["error"] == (
        "Renderer failed"
    )

    assert data["items"][1]["id"] == 123
    assert data["items"][1]["status"] == "success"
    assert data["items"][1]["error"] is None
