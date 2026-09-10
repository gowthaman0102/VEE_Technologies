import json
from dataclasses import dataclass

from app.llm.factory import get_llm_provider
from app.schemas.risk_insight import RiskInsightResult
from app.services.article_triage_read_service import (
    get_article_triage,
)
from app.services.risk_assessment_service import (
    RiskAssessmentResult,
    StoredTriageNotFoundError,
    assess_article_risk,
)
from app.services.risk_insight_prompt_service import (
    build_risk_insight_prompt,
)
from app.services.risk_insight_persistence_service import (
    save_risk_insight,
)


@dataclass(frozen=True)
class RiskInsightServiceResult:
    article_id: int
    company_id: int
    model: str
    assessment: RiskAssessmentResult
    insight: RiskInsightResult


async def generate_risk_insight(
    db,
    *,
    article_id: int,
    company_id: int,
    provider=None,
) -> RiskInsightServiceResult:
    triage = await get_article_triage(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if triage is None:
        raise StoredTriageNotFoundError(
            "Stored triage result not found for "
            f"article {article_id} and company {company_id}."
        )

    assessment = await assess_article_risk(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    prompt = build_risk_insight_prompt(
        triage=triage,
        assessment=assessment,
    )

    llm = provider or get_llm_provider()

    result = await llm.generate(
        prompt,
        response_format=(
            RiskInsightResult.model_json_schema()
        ),
    )

    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Insight agent returned invalid JSON."
        ) from exc

    insight = RiskInsightResult.model_validate(
        payload
    )

    if (
        insight.attention_level
        != assessment.risk.risk_level
    ):
        raise ValueError(
            "Insight attention level does not match "
            "the deterministic risk level."
        )

    service_result = RiskInsightServiceResult(
        article_id=article_id,
        company_id=company_id,
        model=result.model,
        assessment=assessment,
        insight=insight,
    )

    await save_risk_insight(
        db,
        result=service_result,
    )

    return service_result
