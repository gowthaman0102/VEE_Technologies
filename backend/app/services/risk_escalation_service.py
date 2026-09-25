from dataclasses import dataclass

from app.schemas.client_configuration import AlertConfiguration

ESCALATION_ACTIONS: dict[str, str] = {
    "low": "ignore",
    "medium": "monitor",
    "high": "review",
    "critical": "escalate",
}


@dataclass(frozen=True)
class EscalationDecision:
    risk_level: str
    action: str
    requires_human_review: bool
    requires_immediate_alert: bool


def decide_escalation(
    *,
    risk_level: str,
    configuration: AlertConfiguration | None = None,
) -> EscalationDecision:
    normalized_level = risk_level.strip().lower()

    if normalized_level not in ESCALATION_ACTIONS:
        raise ValueError(
            f"Unsupported risk level: {risk_level}"
        )

    action = ESCALATION_ACTIONS[
        normalized_level
    ]
    alert_config = configuration or AlertConfiguration()
    severity = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }

    return EscalationDecision(
        risk_level=normalized_level,
        action=action,
        requires_human_review=(
            alert_config.enabled
            and severity[normalized_level]
            >= severity[alert_config.minimum_risk_level]
        ),
        requires_immediate_alert=(
            alert_config.enabled
            and severity[normalized_level]
            >= severity[alert_config.immediate_alert_level]
        ),
    )
