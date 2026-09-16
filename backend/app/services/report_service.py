from __future__ import annotations

import csv
import io
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_triage import ArticleTriage
from app.models.generated_report import GeneratedReport
from app.services.analytics_service import (
    get_business_impact_distribution,
    get_event_summary,
    get_risk_summary,
    get_sentiment_distribution,
    validate_time_window,
)


async def build_company_report(
    db: AsyncSession,
    *,
    company_id: int,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    start_date, end_date = validate_time_window(start_date, end_date)
    article_count_stmt = (
        select(func.count(func.distinct(Article.id)))
        .join(ArticleTriage, ArticleTriage.article_id == Article.id)
        .where(
            ArticleTriage.company_id == company_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date,
        )
    )
    total_articles = int((await db.scalar(article_count_stmt)) or 0)

    sentiment = await get_sentiment_distribution(
        db, company_id=company_id, start=start_date, end=end_date
    )
    risk = await get_risk_summary(
        db, company_id=company_id, start=start_date, end=end_date
    )
    business = await get_business_impact_distribution(
        db, company_id=company_id, start=start_date, end=end_date
    )
    events = await get_event_summary(
        db, company_id=company_id, start=start_date, end=end_date
    )

    metrics = [
        {"label": "Average risk score", "value": risk["average_risk_score"]},
        {"label": "Highest risk score", "value": risk["highest_risk_score"]},
        {"label": "High risk count", "value": risk["high_risk_count"]},
        {"label": "Medium risk count", "value": risk["medium_risk_count"]},
        {"label": "Low risk count", "value": risk["low_risk_count"]},
        {"label": "Positive sentiment", "value": sentiment.get("positive", 0)},
        {"label": "Neutral sentiment", "value": sentiment.get("neutral", 0)},
        {"label": "Negative sentiment", "value": sentiment.get("negative", 0)},
    ]

    return {
        "company_id": company_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": total_articles,
        "total_events": events.get("total_events", 0),
        "high_risk_count": risk["high_risk_count"],
        "medium_risk_count": risk["medium_risk_count"],
        "low_risk_count": risk["low_risk_count"],
        "sentiment_balance": {
            "positive": sentiment.get("positive", 0),
            "neutral": sentiment.get("neutral", 0),
            "negative": sentiment.get("negative", 0),
        },
        "metrics": metrics,
    }


def report_rows(report_data: dict) -> list[tuple[str, str]]:
    rows = [
        ("company_id", str(report_data["company_id"])),
        ("start_date", report_data["start_date"].isoformat()),
        ("end_date", report_data["end_date"].isoformat()),
        ("total_articles", str(report_data["total_articles"])),
        ("total_events", str(report_data["total_events"])),
        ("high_risk_count", str(report_data["high_risk_count"])),
        ("medium_risk_count", str(report_data["medium_risk_count"])),
        ("low_risk_count", str(report_data["low_risk_count"])),
        ("positive_sentiment", str(report_data["sentiment_balance"]["positive"])),
        ("neutral_sentiment", str(report_data["sentiment_balance"]["neutral"])),
        ("negative_sentiment", str(report_data["sentiment_balance"]["negative"])),
    ]
    rows.extend((item["label"], str(item["value"])) for item in report_data["metrics"])
    return rows


def export_report_csv(report_data: dict) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("metric", "value"))
    writer.writerows(report_rows(report_data))
    return output.getvalue().encode("utf-8")


def export_report_xlsx(report_data: dict) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Media Intelligence"
    sheet.append(("Metric", "Value"))
    for row in report_rows(report_data):
        sheet.append(row)
    sheet.column_dimensions["A"].width = 28
    sheet.column_dimensions["B"].width = 42
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def export_report_pdf(report_data: dict) -> bytes:
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=letter)
    width, height = letter
    y = height - 54
    canvas.setTitle("VEE Technologies Media Intelligence Report")
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(54, y, "VEE Technologies Media Intelligence Report")
    y -= 30
    canvas.setFont("Helvetica", 10)
    for metric, value in report_rows(report_data):
        if y < 54:
            canvas.showPage()
            y = height - 54
            canvas.setFont("Helvetica", 10)
        canvas.drawString(54, y, f"{metric}: {value}")
        y -= 16
    canvas.save()
    return output.getvalue()


async def persist_generated_report(
    db: AsyncSession,
    *,
    report_data: dict,
    file_format: str,
    content: bytes,
) -> GeneratedReport:
    extensions = {"pdf": "pdf", "xlsx": "xlsx", "csv": "csv"}
    content_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
    }
    record = GeneratedReport(
        company_id=report_data["company_id"],
        report_type="company_intelligence",
        file_format=file_format,
        filename=f"company-{report_data['company_id']}-report.{extensions[file_format]}",
        content_type=content_types[file_format],
        period_start=report_data["start_date"],
        period_end=report_data["end_date"],
        content=content,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def render_report(report_data: dict, file_format: str) -> bytes:
    exporters = {
        "pdf": export_report_pdf,
        "xlsx": export_report_xlsx,
        "csv": export_report_csv,
    }
    return exporters[file_format](report_data)
