from dataclasses import dataclass


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
) -> EscalationDecision:
    normalized_level = risk_level.strip().lower()

    if normalized_level not in ESCALATION_ACTIONS:
        raise ValueError(
            f"Unsupported risk level: {risk_level}"
        )

    action = ESCALATION_ACTIONS[
        normalized_level
    ]

    return EscalationDecision(
        risk_level=normalized_level,
        action=action,
        requires_human_review=(
            normalized_level in {
                "high",
                "critical",
            }
        ),
        requires_immediate_alert=(
            normalized_level == "critical"
        ),
    )
