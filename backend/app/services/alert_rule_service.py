from dataclasses import dataclass


@dataclass(frozen=True)
class AlertDecision:
    should_create_alert: bool
    alert_type: str | None
    severity: str | None
    requires_immediate_delivery: bool


def decide_alert(
    *,
    escalation_action: str,
) -> AlertDecision:
    action = escalation_action.strip().lower()

    if action == "ignore":
        return AlertDecision(
            should_create_alert=False,
            alert_type=None,
            severity=None,
            requires_immediate_delivery=False,
        )

    if action == "monitor":
        return AlertDecision(
            should_create_alert=False,
            alert_type=None,
            severity=None,
            requires_immediate_delivery=False,
        )

    if action == "review":
        return AlertDecision(
            should_create_alert=True,
            alert_type="review",
            severity="high",
            requires_immediate_delivery=False,
        )

    if action == "escalate":
        return AlertDecision(
            should_create_alert=True,
            alert_type="urgent",
            severity="critical",
            requires_immediate_delivery=True,
        )

    raise ValueError(
        f"Unsupported escalation action: {escalation_action}"
    )
