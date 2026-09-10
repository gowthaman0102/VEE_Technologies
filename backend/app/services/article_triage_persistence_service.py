from sqlalchemy import select

from app.models.article_triage import ArticleTriage
from app.schemas.article_triage import ArticleTriageResult


async def save_article_triage(
    db,
    *,
    article_id: int,
    company_id: int,
    model: str,
    triage: ArticleTriageResult,
) -> ArticleTriage:
    result = await db.execute(
        select(ArticleTriage).where(
            ArticleTriage.article_id == article_id,
            ArticleTriage.company_id == company_id,
        )
    )

    record = result.scalar_one_or_none()

    if record is None:
        record = ArticleTriage(
            article_id=article_id,
            company_id=company_id,
            company_name=triage.company_name,
            event_type=triage.event_type,
            summary=triage.summary,
            why_it_matters=triage.why_it_matters,
            evidence=triage.evidence,
            potential_impact=triage.potential_impact,
            urgency=triage.urgency,
            confidence=triage.confidence,
            llm_model=model,
        )

        db.add(record)
    else:
        record.company_name = triage.company_name
        record.event_type = triage.event_type
        record.summary = triage.summary
        record.why_it_matters = triage.why_it_matters
        record.evidence = triage.evidence
        record.potential_impact = triage.potential_impact
        record.urgency = triage.urgency
        record.confidence = triage.confidence
        record.llm_model = model

    await db.commit()
    await db.refresh(record)

    return record
