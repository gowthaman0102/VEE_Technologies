import asyncio
from datetime import datetime, timezone
from app.db.session import AsyncSessionLocal
from app.services.report_service import build_company_report, export_report_csv

async def test():
    async with AsyncSessionLocal() as db:
        snapshot_at = datetime(2026, 9, 19, 5, 13, tzinfo=timezone.utc)
        start_date = datetime(2026, 9, 7, tzinfo=timezone.utc)
        end_date = datetime(2026, 9, 14, tzinfo=timezone.utc)
        
        from sqlalchemy import select
        from app.models.company import Company
        company = (await db.execute(select(Company).where(Company.is_active.is_(True)).limit(1))).scalar_one()
        
        print(f'Company: {company.id} {company.name}')
        
        report_data = await build_company_report(
            db,
            company_id=company.id,
            start_date=start_date,
            end_date=end_date,
            snapshot_at=snapshot_at,
            time_mode='media',
        )
        
        print(f'Total Articles: {report_data["total_articles"]}')
        print(f'Total Events: {report_data["total_events"]}')
        print(f'Snapshot At: {report_data["snapshot_at"]}')
        print(f'Time Mode: {report_data["time_mode"]}')
        
        csv_bytes = export_report_csv(report_data)
        csv_text = csv_bytes.decode('utf-8')
        lines = [l for l in csv_text.split('\n') if l.strip()]
        print(f'CSV header: {lines[0]}')
        print(f'First data row: {lines[1]}')
        print(f'Total CSV rows (incl header): {len(lines)}')
        
        # Count row types
        metric_rows = [l for l in lines[1:] if l.startswith('metric')]
        article_rows = [l for l in lines[1:] if l.startswith('article')]
        print(f'  Metric rows: {len(metric_rows)}')
        print(f'  Article rows: {len(article_rows)}')
        
        for metric in report_data.get('metrics', []):
            print(f'  Metric: {metric["label"]} = {metric["value"]}')

asyncio.run(test())
