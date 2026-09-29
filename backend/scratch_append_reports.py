import os

with open(r'D:\VEE_Technologies\backend\app\api\v1\reports.py', 'a') as f:
    f.write('''
from fastapi import UploadFile, File, Form
import uuid

@router.post("/analytics-snapshot")
async def upload_analytics_snapshot(
    company_id: int = Form(...),
    period_start: str = Form(...),
    period_end: str = Form(...),
    time_mode: str = Form("media"),
    snapshot: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if snapshot.content_type != "image/png":
        raise HTTPException(400, "Only PNG snapshots are allowed")
        
    content = await snapshot.read()
    batch_id = str(uuid.uuid4())
    
    start_dt = datetime.fromisoformat(period_start)
    end_dt = datetime.fromisoformat(period_end)
    
    report = GeneratedReport(
        batch_id=batch_id,
        company_id=company_id,
        report_type="custom",
        report_template="snapshot",
        report_scope="analytics_snapshot",
        time_mode=time_mode,
        period_start=start_dt,
        period_end=end_dt,
        snapshot_at=datetime.now(timezone.utc),
        file_format="png",
        filename=f"analytics_snapshot_{company_id}_{int(datetime.now().timestamp())}.png",
        content_type="image/png",
        content=content,
        status="success",
        generated_at=datetime.now(timezone.utc),
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return {
        "batch_id": batch_id,
        "report_id": report.id,
        "filename": report.filename
    }


@router.post("/intelligence-export-summary")
async def generate_intelligence_export_summary(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload.report_scope = "intelligence_export"
    start_date, end_date = await _resolve_period_for_request(payload, db)
    records = await generate_report_batch(
        db,
        company_id=payload.company_id,
        report_type=payload.report_type,
        period_start=start_date,
        period_end=end_date,
        time_mode=payload.time_mode,
        report_scope="intelligence_export",
        article_ids=payload.article_ids,
        business_impact_category=payload.business_impact_category,
        include_details=payload.include_details,
        report_template=payload.report_template,
        search_query=payload.search_query,
        search_mode=payload.search_mode,
        search_filters=payload.search_filters,
    )
    return {
        "batch_id": records[0].batch_id if records else None,
        "status": "success"
    }
''')
