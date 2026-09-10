from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.monitoring_priority_service import (
    MonitoringPriorityResult,
)
from app.services.risk_assessment_service import (
    RiskAssessmentResult,
)
from app.services.risk_escalation_service import (
    EscalationDecision,
)
from app.services.risk_rule_service import (
    RiskCalculation,
)


client = TestClient(app)


def make_assessment():
    return RiskAssessmentResult(
        triage_id=1,
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type="regulatory_action",
        urgency="high",
        confidence=0.9,
        monitoring_priority=MonitoringPriorityResult(
            company_id=1,
            event_type="regulatory_action",
            monitoring_topic="Regulatory Action",
            priority="high",
            source="configured",
        ),
        risk=RiskCalculation(
            event_type="regulatory_action",
            monitoring_topic="Regulatory Action",
            topic_priority="high",
            urgency="high",
            confidence=0.9,
            priority_score=80.0,
            urgency_score=75.0,
            confidence_score=90.0,
            risk_score=80.0,
            risk_level="high",
        ),
        escalation=EscalationDecision(
            risk_level="high",
            action="review",
            requires_human_review=True,
            requires_immediate_alert=False,
        ),
    )


def make_stored_record():
    return SimpleNamespace(
        id=1,
        triage_id=1,
        article_id=8,
        company_id=1,
        event_type="regulatory_action",
        monitoring_topic="Regulatory Action",
        topic_priority="high",
        priority_source="configured",
        urgency="high",
        confidence=0.9,
        risk_score=80.0,
        risk_level="high",
        escalation_action="review",
        requires_human_review=True,
        requires_immediate_alert=False,
        created_at="2026-09-10T15:48:37+00:00",
        updated_at="2026-09-10T15:48:37+00:00",
    )


def test_post_risk_assessment(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.risk.assess_article_risk",
        AsyncMock(
            return_value=make_assessment()
        ),
    )

    response = client.post(
        "/api/v1/risk/articles/8",
        json={
            "company_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["article_id"] == 8
    assert data["company_id"] == 1
    assert data["company_name"] == "PayU"
    assert data["event_type"] == "regulatory_action"

    assert (
        data["monitoring_priority"]["priority"]
        == "high"
    )

    assert data["risk"]["risk_score"] == 80.0
    assert data["risk"]["risk_level"] == "high"

    assert (
        data["escalation"]["action"]
        == "review"
    )


def test_get_risk_assessment(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.risk.get_risk_assessment",
        AsyncMock(
            return_value=make_stored_record()
        ),
    )

    response = client.get(
        "/api/v1/risk/articles/8",
        params={
            "company_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["article_id"] == 8
    assert data["company_id"] == 1
    assert data["risk_score"] == 80.0
    assert data["risk_level"] == "high"
    assert data["escalation_action"] == "review"


def test_get_risk_assessment_not_found(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.risk.get_risk_assessment",
        AsyncMock(
            return_value=None
        ),
    )

    response = client.get(
        "/api/v1/risk/articles/999",
        params={
            "company_id": 1,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Stored risk assessment not found."
    )
