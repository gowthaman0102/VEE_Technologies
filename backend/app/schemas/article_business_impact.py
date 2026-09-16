from typing import Literal

from pydantic import BaseModel, Field


BusinessImpactCategory = Literal[
    "financial",
    "operational",
    "legal",
    "regulatory",
    "cybersecurity",
    "reputation",
    "customer",
    "product",
    "market",
    "competitive",
]


class ArticleBusinessImpactInference(BaseModel):
    primary_category: BusinessImpactCategory

    categories: list[
        BusinessImpactCategory
    ] = Field(
        min_length=1,
        max_length=10,
    )

    impact_summary: str = Field(
        min_length=1,
        max_length=1500,
    )

    evidence: list[str] = Field(
        min_length=1,
        max_length=5,
    )


class ArticleBusinessImpactResult(
    ArticleBusinessImpactInference
):
    model: str = Field(
        min_length=1,
        max_length=100,
    )
