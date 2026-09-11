import pytest

from app.services.alert_rule_service import (
    decide_alert,
)


def test_ignore_does_not_create_alert():
    result = decide_alert(
        escalation_action="ignore",
    )

    assert result.should_create_alert is False
    assert result.alert_type is None
    assert result.severity is None
    assert result.requires_immediate_delivery is False


def test_monitor_does_not_create_alert():
    result = decide_alert(
        escalation_action="monitor",
    )

    assert result.should_create_alert is False
    assert result.alert_type is None
    assert result.severity is None
    assert result.requires_immediate_delivery is False


def test_review_creates_high_alert():
    result = decide_alert(
        escalation_action="review",
    )

    assert result.should_create_alert is True
    assert result.alert_type == "review"
    assert result.severity == "high"
    assert result.requires_immediate_delivery is False


def test_escalate_creates_critical_alert():
    result = decide_alert(
        escalation_action="escalate",
    )

    assert result.should_create_alert is True
    assert result.alert_type == "urgent"
    assert result.severity == "critical"
    assert result.requires_immediate_delivery is True


def test_alert_rule_normalizes_input():
    result = decide_alert(
        escalation_action=" REVIEW ",
    )

    assert result.should_create_alert is True
    assert result.alert_type == "review"
    assert result.severity == "high"


def test_alert_rule_rejects_invalid_action():
    with pytest.raises(
        ValueError,
        match="Unsupported escalation action",
    ):
        decide_alert(
            escalation_action="panic",
        )
