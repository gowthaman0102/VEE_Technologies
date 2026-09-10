import pytest

from app.services.risk_escalation_service import (
    decide_escalation,
)


def test_low_risk_is_ignored():
    result = decide_escalation(
        risk_level="low",
    )

    assert result.action == "ignore"
    assert result.requires_human_review is False
    assert result.requires_immediate_alert is False


def test_medium_risk_is_monitored():
    result = decide_escalation(
        risk_level="medium",
    )

    assert result.action == "monitor"
    assert result.requires_human_review is False
    assert result.requires_immediate_alert is False


def test_high_risk_requires_review():
    result = decide_escalation(
        risk_level="high",
    )

    assert result.action == "review"
    assert result.requires_human_review is True
    assert result.requires_immediate_alert is False


def test_critical_risk_is_escalated():
    result = decide_escalation(
        risk_level="critical",
    )

    assert result.action == "escalate"
    assert result.requires_human_review is True
    assert result.requires_immediate_alert is True


def test_escalation_normalizes_case():
    result = decide_escalation(
        risk_level=" HIGH ",
    )

    assert result.risk_level == "high"
    assert result.action == "review"


def test_escalation_rejects_invalid_level():
    with pytest.raises(
        ValueError,
        match="Unsupported risk level",
    ):
        decide_escalation(
            risk_level="severe",
        )
