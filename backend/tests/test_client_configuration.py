import pytest
from pydantic import ValidationError

from app.ingestion.sources import get_sources_for_config
from app.services.report_service import _apply_report_configuration
from app.schemas.client_configuration import (
    ClientConfiguration,
    ReportConfiguration,
    RiskConfiguration,
)


def make_config(name: str, alias: str, topic: str, *, critical: int) -> ClientConfiguration:
    return ClientConfiguration(
        company_id=1,
        company_name=name,
        aliases=[name, alias],
        monitoring_topics=[topic],
        competitors=["Configured Competitor"],
        geographies=["United States"],
        regulators=["SEC"],
        sources={"official_sources": ["https://example.com/feed.xml"]},
        risk={"medium_threshold": 35, "high_threshold": 55, "critical_threshold": critical},
        alerts={},
        reports={},
        features={},
        branding={},
    )


def test_defaults_are_safe_and_validate_known_report_sections():
    config = make_config("Demo Client A", "Demo A", "regulation", critical=80)

    assert config.risk.medium_threshold == 35
    assert config.features.risk_enabled is True
    assert "risk" in config.reports.enabled_sections
    assert len(get_sources_for_config(config)) == 3


def test_different_clients_produce_different_source_queries():
    client_a = make_config("Demo Client A", "Alpha", "regulation", critical=80)
    client_b = make_config("Demo Client B", "Beta", "cybersecurity", critical=70)

    sources_a = get_sources_for_config(client_a)
    sources_b = get_sources_for_config(client_b)

    assert sources_a[0].url != sources_b[0].url
    assert "Alpha" in sources_a[0].url
    assert "Beta" in sources_b[0].url
    assert sources_a[1].query != sources_b[1].query


def test_risk_thresholds_require_strict_order():
    with pytest.raises(ValidationError):
        RiskConfiguration(medium_threshold=60, high_threshold=60, critical_threshold=80)


def test_report_sections_reject_unknown_keys():
    with pytest.raises(ValidationError):
        ReportConfiguration(enabled_sections=["unsupported"])


def test_report_renderer_input_honors_disabled_sections():
    report = {
        "articles": [{"article_id": 1}],
        "sentiment": {"negative": 1},
        "risk": {"high": 1},
        "metrics": [{"label": "Articles", "value": 1}],
        "executive_summary": "summary",
        "report_configuration": {
            "enabled_sections": ["executive_summary", "risk"],
        },
    }

    configured = _apply_report_configuration(report)

    assert configured["executive_summary"] == "summary"
    assert configured["risk"] == {"high": 1}
    assert configured["articles"] == []
    assert configured["sentiment"] == {}
    assert configured["metrics"] == []
