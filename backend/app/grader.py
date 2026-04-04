from __future__ import annotations

from typing import Any, Optional


CLOSE_CONFIRMATION_PHRASES = (
    "may i close",
    "can i close",
    "shall i close",
    "close this ticket",
    "close the ticket",
    "close this case",
    "close the case",
)


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _is_close_confirmation_message(state: dict[str, Any], normalized_message: str) -> bool:
    if not normalized_message:
        return False

    awaiting_close = bool(state.get("customer_ready_to_close")) or state.get("status") == "awaiting_close"
    if not awaiting_close:
        return False

    return any(phrase in normalized_message for phrase in CLOSE_CONFIRMATION_PHRASES)


class SupportTicketGrader:
    def evaluate_classification(self, task: dict[str, Any], category: Optional[str]) -> tuple[float, bool]:
        normalized_category = _normalize_text(category)
        is_correct = normalized_category == _normalize_text(task["expected_category"])
        return (0.2 if is_correct else -0.2, is_correct)

    def evaluate_response(
        self,
        task: dict[str, Any],
        state: dict[str, Any],
        message: Optional[str],
    ) -> tuple[float, bool, list[str]]:
        normalized_message = _normalize_text(message)
        if _is_close_confirmation_message(state, normalized_message):
            return 0.2, True, ["Closure confirmation was shared with the customer."]

        guidance = task.get("reply_guidance", {})
        positive_keywords = [
            keyword.lower()
            for keyword in guidance.get("positive_keywords", [])
            if keyword.strip()
        ]
        negative_keywords = [
            keyword.lower()
            for keyword in guidance.get("negative_keywords", [])
            if keyword.strip()
        ]

        missing_positive = [
            keyword for keyword in positive_keywords if keyword not in normalized_message
        ]
        matched_negative = [
            keyword for keyword in negative_keywords if keyword in normalized_message
        ]

        helpful = not missing_positive and not matched_negative and len(normalized_message) >= 30
        feedback: list[str] = []

        if missing_positive:
            feedback.append(
                "Response is missing expected policy cues: "
                + ", ".join(missing_positive[:3])
            )
        if matched_negative:
            feedback.append(
                "Response includes off-policy phrasing: "
                + ", ".join(matched_negative[:3])
            )

        if task["resolution"].get("needs_escalation") and "escalat" not in normalized_message:
            helpful = False
            feedback.append("Response should set escalation expectations for this ticket.")

        if state["progress"]["classification"] == "incorrect":
            helpful = False
            feedback.append("The ticket is currently misclassified, which weakens the response.")

        reward = 0.2 if helpful else -0.2
        return reward, helpful, feedback

    def evaluate_escalation(
        self,
        task: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[float, bool, str]:
        needs_escalation = bool(task["resolution"].get("needs_escalation"))
        response_sent = state["progress"]["reply"] in {"completed", "incorrect"}

        if needs_escalation and response_sent:
            return 0.3, True, "Escalation was appropriate for this ticket."
        if needs_escalation:
            return 0.1, True, "Escalation was needed, but the customer should have been informed first."
        return -0.1, False, "Escalation was not required for this ticket."

    def evaluate_closure(
        self,
        task: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[float, bool, list[str]]:
        reasons: list[str] = []
        ready_to_close = True

        if state["progress"]["classification"] != "correct":
            ready_to_close = False
            reasons.append("Ticket must be correctly classified before closing.")

        if state["progress"]["reply"] != "completed":
            ready_to_close = False
            reasons.append("A helpful customer reply is still pending.")

        if task["resolution"].get("needs_escalation") and state["progress"]["escalation"] != "completed":
            ready_to_close = False
            reasons.append("Escalation is required before the ticket can be closed.")

        if not task["resolution"].get("can_close_after_response") and not state["customer_ready_to_close"]:
            ready_to_close = False
            reasons.append("The customer has not confirmed resolution yet.")

        if not ready_to_close:
            return -0.3, False, reasons

        reward = 0.3
        if state["steps_taken"] <= len(task["expected_flow"]):
            reward += 0.2
        return reward, True, ["Ticket was closed at the right time."]
