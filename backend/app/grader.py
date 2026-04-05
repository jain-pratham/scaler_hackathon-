from __future__ import annotations

from typing import Optional

from .models import State, Task


CLOSE_CONFIRMATION_PHRASES = (
    "may i close",
    "can i close",
    "shall i close",
    "close this ticket",
    "close the ticket",
    "close this case",
    "close the case",
)


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _is_close_confirmation_message(state: State, normalized_message: str) -> bool:
    if not normalized_message:
        return False

    awaiting_close = bool(state.customer_ready_to_close) or state.status == "awaiting_close"
    if not awaiting_close:
        return False

    return any(phrase in normalized_message for phrase in CLOSE_CONFIRMATION_PHRASES)


class SupportTicketGrader:
    def evaluate_classification(self, task: Task, category: Optional[str]) -> tuple[float, bool]:
        normalized_category = _normalize_text(category)
        is_correct = normalized_category == _normalize_text(task.expected_category)
        return (1.0 if is_correct else 0.0, is_correct)

    def evaluate_response(
        self,
        task: Task,
        state: State,
        message: Optional[str],
    ) -> tuple[float, bool, list[str]]:
        normalized_message = _normalize_text(message)
        if _is_close_confirmation_message(state, normalized_message):
            return 1.0, True, ["Closure confirmation was shared with the customer."]

        positive_keywords = [keyword.lower() for keyword in task.reply_guidance.positive_keywords if keyword.strip()]
        negative_keywords = [keyword.lower() for keyword in task.reply_guidance.negative_keywords if keyword.strip()]
        positive_matches = [keyword for keyword in positive_keywords if keyword in normalized_message]
        matched_negative = [keyword for keyword in negative_keywords if keyword in normalized_message]
        feedback: list[str] = []

        keyword_score = len(positive_matches) / len(positive_keywords) if positive_keywords else 1.0
        length_score = 1.0 if len(normalized_message) >= 30 else min(1.0, len(normalized_message) / 30.0)
        score = (keyword_score * 0.8) + (length_score * 0.2)

        if matched_negative:
            score -= 0.3 * (len(matched_negative) / max(1, len(negative_keywords)))
            feedback.append("Response includes off-policy phrasing: " + ", ".join(matched_negative[:3]))

        if task.resolution.needs_escalation and "escalat" not in normalized_message:
            score -= 0.25
            feedback.append("Response should set escalation expectations for this ticket.")

        if state.progress.classification == "incorrect":
            score -= 0.15
            feedback.append("The ticket is currently misclassified, which weakens the response.")

        missing_positive = [keyword for keyword in positive_keywords if keyword not in normalized_message]
        if missing_positive:
            feedback.append("Response is missing expected policy cues: " + ", ".join(missing_positive[:3]))

        final_score = clamp_score(score)
        return final_score, final_score >= 0.7, feedback

    def evaluate_escalation(self, task: Task, state: State) -> tuple[float, bool, str]:
        needs_escalation = task.resolution.needs_escalation
        response_sent = state.progress.reply in {"completed", "incorrect"}

        if needs_escalation and response_sent:
            return 1.0, True, "Escalation was appropriate for this ticket."
        if needs_escalation:
            return 0.6, True, "Escalation was needed, but the customer should have been informed first."
        return 0.0, False, "Escalation was not required for this ticket."

    def evaluate_closure(self, task: Task, state: State) -> tuple[float, bool, list[str]]:
        reasons: list[str] = []
        ready_to_close = True

        if state.progress.classification != "correct":
            ready_to_close = False
            reasons.append("Ticket must be correctly classified before closing.")

        if state.progress.reply != "completed":
            ready_to_close = False
            reasons.append("A helpful customer reply is still pending.")

        if task.resolution.needs_escalation and state.progress.escalation != "completed":
            ready_to_close = False
            reasons.append("Escalation is required before the ticket can be closed.")

        if not task.resolution.can_close_after_response and not state.customer_ready_to_close:
            ready_to_close = False
            reasons.append("The customer has not confirmed resolution yet.")

        if not ready_to_close:
            return 0.0, False, reasons

        score = 1.0 if state.steps_taken <= len(task.expected_flow) else 0.8
        return clamp_score(score), True, ["Ticket was closed at the right time."]
