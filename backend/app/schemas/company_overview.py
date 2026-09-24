from pydantic import BaseModel


class CompanyOverviewProfile(BaseModel):
    id: int
    name: str
    industry: str | None
    website: str | None
    is_active: bool
    aliases: list[str]
    geographies: list[str]


class CompanyOverviewSentiment(BaseModel):
    positive: int
    neutral: int
    negative: int


class CompanyOverviewHealth(BaseModel):
    total_articles: int
    processed_articles: int
    sentiment: CompanyOverviewSentiment
    high_risk_count: int
    critical_risk_count: int
    active_alerts: int


class CompanyLocationResponse(BaseModel):
    id: int
    label: str
    location_type: str
    city: str
    region: str | None
    country: str
    latitude: float
    longitude: float


class CompanyLocationCountry(BaseModel):
    country: str
    locations: list[CompanyLocationResponse]


class CompanyOverviewResponse(BaseModel):
    company: CompanyOverviewProfile
    health: CompanyOverviewHealth
    official_locations: list[CompanyLocationCountry]
    headquarters: list[CompanyLocationResponse]
    official_location_count: int
    location_country_count: int
