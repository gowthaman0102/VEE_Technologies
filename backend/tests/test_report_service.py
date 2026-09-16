from datetime import datetime, timezone

from app.services.report_service import (
    export_report_csv,
    export_report_pdf,
    export_report_xlsx,
)


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
