from dataclasses import dataclass

from app.schemas.article_triage import (
    EventType,
    Urgency,
)


EVENT_TOPIC_MAP: dict[str, str] = {
    "regulatory_action": "Regulatory Action",
    "fraud_security": "Fraud and Security",
    "service_outage": "Service Outage",
    "leadership_change": "Leadership Change",
    "product_launch": "Product Launch",
}


PRIORITY_SCORES: dict[str, float] = {
    "low": 20.0,
    "medium": 50.0,
    "high": 80.0,
}


URGENCY_SCORES: dict[str, float] = {
    "low": 25.0,
    "medium": 50.0,
    "high": 75.0,
    "critical": 100.0,
}


@dataclass(frozen=True)
class RiskCalculation:
    event_type: str
    monitoring_topic: str | None
    topic_priority: str
    urgency: str
    confidence: float
    priority_score: float
    urgency_score: float
    confidence_score: float
    risk_score: float
    risk_level: str


def event_type_to_monitoring_topic(
    event_type: EventType,
) -> str | None:
    return EVENT_TOPIC_MAP.get(event_type)


def risk_level_from_score(
    score: float,
) -> str:
    if score >= 85.0:
        return "critical"

    if score >= 60.0:
        return "high"

    if score >= 40.0:
        return "medium"

    return "low"


def calculate_risk(
    *,
    event_type: EventType,
    topic_priority: str,
    urgency: Urgency,
    confidence: float,
) -> RiskCalculation:
    normalized_priority = (
        topic_priority.strip().lower()
    )

    if normalized_priority not in PRIORITY_SCORES:
        raise ValueError(
            f"Unsupported monitoring priority: "
            f"{topic_priority}"
        )

    if urgency not in URGENCY_SCORES:
        raise ValueError(
            f"Unsupported urgency: {urgency}"
        )

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "Confidence must be between 0.0 and 1.0."
        )

    priority_score = PRIORITY_SCORES[
        normalized_priority
    ]

    urgency_score = URGENCY_SCORES[
        urgency
    ]

    confidence_score = confidence * 100.0

    risk_score = (
        priority_score * 0.40
        + urgency_score * 0.40
        + confidence_score * 0.20
    )

    risk_score = round(
        risk_score,
        2,
    )

    return RiskCalculation(
        event_type=event_type,
        monitoring_topic=(
            event_type_to_monitoring_topic(
                event_type
            )
        ),
        topic_priority=normalized_priority,
        urgency=urgency,
        confidence=confidence,
        priority_score=priority_score,
        urgency_score=urgency_score,
        confidence_score=confidence_score,
        risk_score=risk_score,
        risk_level=risk_level_from_score(
            risk_score
        ),
    )
