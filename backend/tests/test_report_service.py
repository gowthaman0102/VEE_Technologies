from datetime import datetime, timezone

from app.services.report_service import (
    export_report_csv,
    export_report_pdf,
    export_report_xlsx,
    render_report,
)
from app.services.report_schedule_service import calculate_next_run_at
from app.schemas.report_management import ReportRecipientsUpdate, ReportSchedulePayload
from pydantic import ValidationError
import pytest


REPORT = {
    "company_id": 1,
    "start_date": datetime(2026, 1, 1, tzinfo=timezone.utc),
    "end_date": datetime(2026, 1, 31, tzinfo=timezone.utc),
    "total_articles": 3,
    "total_events": 1,
    "high_risk_count": 1,
    "medium_risk_count": 1,
    "low_risk_count": 1,
    "sentiment_balance": {"positive": 1, "neutral": 1, "negative": 1},
    "metrics": [{"label": "Average risk score", "value": 55.0}],
}


def test_report_renderers_produce_real_files():
    csv_content = export_report_csv(REPORT)
    xlsx_content = export_report_xlsx(REPORT)
    pdf_content = export_report_pdf(REPORT)

    assert csv_content.startswith(b"metric,value")
    assert xlsx_content.startswith(b"PK")
    assert pdf_content.startswith(b"%PDF")


def test_summary_template_omits_article_details_but_keeps_aggregates():
    report_data = {
        **REPORT,
        "articles": [{"article_id": 17, "title": "Detailed article title"}],
        "highest_risk_stories": [{"article_id": 17, "title": "Detailed article title"}],
        "alerts": [{"id": 3, "title": "Detailed alert"}],
        "competitors": [{"name": "Detailed competitor"}],
    }

    detailed = render_report(report_data, "csv", include_details=True)
    summary = render_report(report_data, "csv", include_details=False)

    assert b"Detailed article title" in detailed
    assert b"Detailed article title" not in summary
    assert b"total_articles,3" in summary
    assert report_data["articles"][0]["article_id"] == 17


def test_report_schedule_next_run_uses_utc_cadence_fields():
    now = datetime(2026, 9, 28, 10, tzinfo=timezone.utc)

    assert calculate_next_run_at(
        report_type="daily", run_time_utc="09:00", now=now
    ) == datetime(2026, 9, 29, 9, tzinfo=timezone.utc)
    assert calculate_next_run_at(
        report_type="weekly", run_time_utc="11:00", day_of_week=0, now=now
    ) == datetime(2026, 9, 28, 11, tzinfo=timezone.utc)
    assert calculate_next_run_at(
        report_type="monthly", run_time_utc="09:00", day_of_month=1, now=now
    ) == datetime(2026, 10, 1, 9, tzinfo=timezone.utc)


def test_report_management_schemas_validate_live_inputs():
    recipients = ReportRecipientsUpdate(emails=["Person@Example.com", " person@example.com "])
    assert recipients.emails == ["person@example.com"]

    with pytest.raises(ValidationError):
        ReportRecipientsUpdate(emails=["not-an-email"])
    with pytest.raises(ValidationError):
        ReportSchedulePayload(name="Impact", report_type="daily", report_scope="business_impact")
