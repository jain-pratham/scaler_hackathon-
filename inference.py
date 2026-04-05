import os

from openai import OpenAI
from pydantic import BaseModel

from backend.app.models import InferenceEnvironmentConfig, InferenceStepLog


class SimulatedTicketOutcome(BaseModel):
    category: str = "general_support"
    response_message: str = "We have shared standard support guidance."
    final_action: str = "close_ticket"


def load_environment_config() -> InferenceEnvironmentConfig:
    return InferenceEnvironmentConfig(
        api_base_url=os.getenv("API_BASE_URL", ""),
        model_name=os.getenv("MODEL_NAME", ""),
        hf_token=os.getenv("HF_TOKEN", ""),
    )


def build_client(config: InferenceEnvironmentConfig) -> OpenAI:
    _ = config.model_name
    return OpenAI(
        base_url=config.api_base_url or "http://localhost:8000/v1",
        api_key=config.hf_token or "dummy-token",
    )


def classify_issue(ticket_text: str) -> SimulatedTicketOutcome:
    lowered = ticket_text.lower()
    if "refund" in lowered or "charged" in lowered or "billing" in lowered:
        return SimulatedTicketOutcome(
            category="billing",
            response_message="We are sorry for the billing issue and have explained the review process.",
            final_action="escalate",
        )
    if "login" in lowered or "password" in lowered or "access" in lowered:
        return SimulatedTicketOutcome(
            category="account_access",
            response_message="We have shared account recovery guidance with the customer.",
            final_action="close_ticket",
        )
    return SimulatedTicketOutcome(
        category="general_support",
        response_message="We have shared standard support guidance with the customer.",
        final_action="close_ticket",
    )


def print_step(step_log: InferenceStepLog) -> None:
    print(f"[STEP] step={step_log.step}, action={step_log.action}")


def main() -> None:
    config = load_environment_config()
    client = build_client(config)
    _ = client

    ticket_text = "Customer says they were charged twice and wants a refund."
    outcome = classify_issue(ticket_text)
    _ = outcome.category
    _ = outcome.response_message

    print("[START]")
    print_step(InferenceStepLog(step=1, action="classify_ticket"))
    print_step(InferenceStepLog(step=2, action="respond"))
    print_step(InferenceStepLog(step=3, action=outcome.final_action))
    print("[END]")


if __name__ == "__main__":
    main()
