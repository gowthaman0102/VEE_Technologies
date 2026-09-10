from typing import Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "regulatory_action",
    "fraud_security",
    "service_outage",
    "leadership_change",
    "product_launch",
    "financial_performance",
    "market_competition",
    "other",
]

Urgency = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class ArticleTriageResult(BaseModel):
    company_name: str

    event_type: EventType

    summary: str = Field(
        min_length=1,
        max_length=1000,
    )

    why_it_matters: str = Field(
        min_length=1,
        max_length=1500,
    )

    evidence: list[str] = Field(
        min_length=1,
    )

    potential_impact: str = Field(
        min_length=1,
        max_length=1500,
    )

    urgency: Urgency

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
