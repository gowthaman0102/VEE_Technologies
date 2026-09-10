from app.models.article_triage import ArticleTriage
from app.services.risk_assessment_service import (
    RiskAssessmentResult,
)


def build_risk_insight_prompt(
    *,
    triage: ArticleTriage,
    assessment: RiskAssessmentResult,
) -> str:
    return f"""
You are a media intelligence insight agent.

Your task is to explain an already-calculated business risk assessment.

IMPORTANT RULES:
- Do not recalculate the risk score.
- Do not change the risk level.
- Do not invent facts.
- Use only the supplied triage and risk information.
- The deterministic risk engine is the source of truth.
- Return JSON only.

COMPANY:
{assessment.company_name}

EVENT TYPE:
{assessment.event_type}

TRIAGE SUMMARY:
{triage.summary}

WHY IT MATTERS:
{triage.why_it_matters}

POTENTIAL IMPACT:
{triage.potential_impact}

EVIDENCE:
{triage.evidence}

URGENCY:
{assessment.urgency}

CONFIDENCE:
{assessment.confidence}

MONITORING TOPIC:
{assessment.monitoring_priority.monitoring_topic}

MONITORING PRIORITY:
{assessment.monitoring_priority.priority}

RISK SCORE:
{assessment.risk.risk_score}

RISK LEVEL:
{assessment.risk.risk_level}

ESCALATION ACTION:
{assessment.escalation.action}

HUMAN REVIEW REQUIRED:
{assessment.escalation.requires_human_review}

IMMEDIATE ALERT REQUIRED:
{assessment.escalation.requires_immediate_alert}

Generate:
- a concise headline
- an executive summary
- a recommended action
- 1 to 5 key reasons
- attention_level exactly matching the supplied risk level
""".strip()
