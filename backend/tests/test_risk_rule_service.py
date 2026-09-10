import pytest

from app.services.risk_rule_service import (
    calculate_risk,
    event_type_to_monitoring_topic,
    risk_level_from_score,
)


def test_event_type_mapping():
    assert (
        event_type_to_monitoring_topic(
            "regulatory_action"
        )
        == "Regulatory Action"
    )

    assert (
        event_type_to_monitoring_topic(
            "fraud_security"
        )
        == "Fraud and Security"
    )

    assert (
        event_type_to_monitoring_topic(
            "service_outage"
        )
        == "Service Outage"
    )

    assert (
        event_type_to_monitoring_topic(
            "leadership_change"
        )
        == "Leadership Change"
    )

    assert (
        event_type_to_monitoring_topic(
            "product_launch"
        )
        == "Product Launch"
    )


def test_event_type_without_mapping():
    assert (
        event_type_to_monitoring_topic(
            "financial_performance"
        )
        is None
    )


def test_risk_level_boundaries():
    assert risk_level_from_score(0.0) == "low"
    assert risk_level_from_score(39.99) == "low"

    assert risk_level_from_score(40.0) == "medium"
    assert risk_level_from_score(59.99) == "medium"

    assert risk_level_from_score(60.0) == "high"
    assert risk_level_from_score(84.99) == "high"

    assert risk_level_from_score(85.0) == "critical"
    assert risk_level_from_score(100.0) == "critical"


def test_high_priority_high_urgency_risk():
    result = calculate_risk(
        event_type="regulatory_action",
        topic_priority="high",
        urgency="high",
        confidence=0.9,
    )

    assert result.priority_score == 80.0
    assert result.urgency_score == 75.0
    assert result.confidence_score == 90.0
    assert result.risk_score == 80.0
    assert result.risk_level == "high"


def test_low_priority_low_urgency_risk():
    result = calculate_risk(
        event_type="product_launch",
        topic_priority="low",
        urgency="low",
        confidence=0.5,
    )

    assert result.risk_score == 28.0
    assert result.risk_level == "low"


def test_critical_urgency_can_raise_risk():
    result = calculate_risk(
        event_type="service_outage",
        topic_priority="high",
        urgency="critical",
        confidence=1.0,
    )

    assert result.risk_score == 92.0
    assert result.risk_level == "critical"


def test_rejects_invalid_priority():
    with pytest.raises(
        ValueError,
        match="Unsupported monitoring priority",
    ):
        calculate_risk(
            event_type="regulatory_action",
            topic_priority="urgent",
            urgency="high",
            confidence=0.9,
        )


def test_rejects_invalid_confidence():
    with pytest.raises(
        ValueError,
        match="Confidence must be between",
    ):
        calculate_risk(
            event_type="regulatory_action",
            topic_priority="high",
            urgency="high",
            confidence=1.5,
        )
