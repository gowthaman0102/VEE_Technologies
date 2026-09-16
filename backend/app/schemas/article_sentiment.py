from typing import Literal

from pydantic import BaseModel, Field


SentimentLabel = Literal[
    "positive",
    "neutral",
    "negative",
]


class ArticleSentimentInference(BaseModel):
    label: SentimentLabel

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str = Field(
        min_length=1,
        max_length=1000,
    )


class ArticleSentimentResult(
    ArticleSentimentInference
):
    model: str = Field(
        min_length=1,
        max_length=100,
    )
