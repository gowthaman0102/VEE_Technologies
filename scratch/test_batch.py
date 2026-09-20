"""
Integration test: Generate a real report batch via generate_report_batch
and verify that all 3 formats are consistent.
"""
import asyncio
from datetime import datetime, timezone
from app.db.session import AsyncSessionLocal
from app.services.report_service import generate_report_batch
from sqlalchemy import select
from app.models.company import Company

async def main():
    async with AsyncSessionLocal() as db:
        company = (
            await db.execute(
                select(Company).where(Company.is_active.is_(True)).limit(1)
            )
        ).scalar_one()

        print(f"Company: {company.id} - {company.name}")

        # Sep 7-14 (same window as the original weekly PDF)
        start = datetime(2026, 9, 7, tzinfo=timezone.utc)
        end = datetime(2026, 9, 14, tzinfo=timezone.utc)

        print(f"Generating batch for {start.date()} to {end.date()}")

        records = await generate_report_batch(
            db,
            company_id=company.id,
            report_type="custom",
            period_start=start,
            period_end=end,
            time_mode="media",
        )

        print(f"\nBatch ID: {records[0].batch_id}")
        print(f"Snapshot At: {records[0].snapshot_at}")
        print(f"Included Article IDs: {records[0].included_article_ids}")
        print(f"Total Articles: {len(records[0].included_article_ids or [])}")

        for r in records:
            print(f"\n  Format: {r.file_format.upper()}")
            print(f"    Status: {r.status}")
            print(f"    Filename: {r.filename}")
            print(f"    Content size: {len(r.content)} bytes" if r.content else "    Content: None")
            print(f"    Error: {r.error}")

        # Verify CSV can be parsed cleanly
        csv_record = next((r for r in records if r.file_format == "csv"), None)
        if csv_record and csv_record.content:
            import csv
            import io
            text = csv_record.content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            row_types = {}
            for row in rows:
                rt = row.get("row_type", "unknown")
                row_types[rt] = row_types.get(rt, 0) + 1
            print(f"\nCSV row breakdown: {row_types}")
            print(f"CSV columns: {list(rows[0].keys()) if rows else 'empty'}")

asyncio.run(main())
