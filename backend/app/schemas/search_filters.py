from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class SearchFilters(BaseModel):
    start: datetime | None = None
    end: datetime | None = None

    source_name: str | None = Field(
        default=None,
        max_length=200,
    )

    sentiment: str | None = Field(
        default=None,
        max_length=20,
    )

    risk_level: str | None = Field(
        default=None,
        max_length=20,
    )

    business_impact: str | None = Field(
        default=None,
        max_length=30,
    )

    event_type: str | None = Field(
        default=None,
        max_length=50,
    )

    event_cluster_id: int | None = Field(
        default=None,
        ge=1,
    )

    @field_validator(
        "source_name",
        "sentiment",
        "risk_level",
        "business_impact",
        "event_type",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: object,
    ) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()

        return normalized or None

    @model_validator(mode="after")
    def validate_time_window(self) -> "SearchFilters":
        if (
            self.start is not None
            and self.end is not None
            and self.start >= self.end
        ):
            raise ValueError(
                "start must be earlier than end"
            )

        return self
