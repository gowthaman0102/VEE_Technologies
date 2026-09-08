from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AliasCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=200)


class GeographyCreate(BaseModel):
    geography: str = Field(min_length=1, max_length=200)


class RegulatorCreate(BaseModel):
    regulator: str = Field(min_length=1, max_length=200)


class RelationshipCreate(BaseModel):
    related_company_name: str = Field(min_length=1, max_length=200)

    relationship_type: Literal[
        "parent",
        "competitor",
        "subsidiary",
        "partner",
    ]


class MonitoringTopicCreate(BaseModel):
    topic: str = Field(min_length=1, max_length=200)

    priority: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = "medium"


class CompanyContextCreate(BaseModel):
    aliases: list[AliasCreate] = Field(default_factory=list)
    geographies: list[GeographyCreate] = Field(default_factory=list)
    regulators: list[RegulatorCreate] = Field(default_factory=list)
    relationships: list[RelationshipCreate] = Field(default_factory=list)
    monitoring_topics: list[MonitoringTopicCreate] = Field(default_factory=list)


class AliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    alias: str


class GeographyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    geography: str


class RegulatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    regulator: str


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    related_company_name: str
    relationship_type: str


class MonitoringTopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    topic: str
    priority: str
    is_active: bool


class CompanyContextResponse(BaseModel):
    company_id: int

    aliases: list[AliasResponse]
    geographies: list[GeographyResponse]
    regulators: list[RegulatorResponse]
    relationships: list[RelationshipResponse]
    monitoring_topics: list[MonitoringTopicResponse]
