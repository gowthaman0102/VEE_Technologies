from typing import Literal

from pydantic import BaseModel, Field


class RiskInsightResult(BaseModel):
    headline: str = Field(
        min_length=1,
        max_length=300,
    )

    executive_summary: str = Field(
        min_length=1,
        max_length=1200,
    )

    recommended_action: str = Field(
        min_length=1,
        max_length=800,
    )

    key_reasons: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    attention_level: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]
