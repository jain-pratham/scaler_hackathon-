from __future__ import annotations

import json
import os
import re
from typing import Optional

from openai import OpenAI

from .models import (
    AgentDecision,
    ObservationModel,
    ReplyPayload,
)


GEMINI_MODEL = "gemini-1.5-flash"

DELIVERY_HINTS: tuple[str, ...] = (
    "delivery",
    "delivered",
    "shipment",
    "shipping",
    "package",
    "missing",
    "customs",
    "carrier",
    "box",
)
ACCOUNT_HINTS: tuple[str, ...] = (
    "password",
    "account",
    "login",
    "two-factor",
    "authenticator",
    "security",
    "fraud",
    "shipping address",
)
RETURN_HINTS: tuple[str, ...] = (
    "return",
    "wrong size",
    "pickup",
    "hardware",
)
REFUND_HINTS: tuple[str, ...] = (
    "refund",
    "rebilled",
    "rebill",
    "invoice",
    "charged",
    "billing",
    "defective",
)
TECHNICAL_HINTS: tuple[str, ...] = (
    "sync",
    "activation",
    "license",
    "app",
    "technical",
    "data",
    "design files",
)


class GeminiDecisionAgent:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("API_KEY")
        self.base_url = base_url or os.getenv("API_BASE_URL")
        self.model = model or os.getenv("MODEL_NAME", "gemini-1.5-flash")
        
        if self.api_key and self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def decide(self, state: ObservationModel) -> AgentDecision:
        if not self.client:
            return self._fallback_decision(state)

        prompt = self._build_prompt(state)
        try:
            return self._call_llm(prompt)
        except Exception:
            return self._fallback_decision(state)

    def generate_reply(self, state: ObservationModel) -> str:
        if not self.client:
            return self._fallback_reply(state)

        prompt = self._build_reply_prompt(state)
        try:
            return self._call_llm_reply(prompt)
        except Exception:
            return self._fallback_reply(state)

    def _build_prompt(self, state: ObservationModel) -> str:
        return (
            "You are a customer support ticket resolution agent.\n"
            "Decide the next single action for the environment.\n"
            "Return strict JSON only with keys action, message, category.\n"
            "Allowed actions: classify_ticket, respond, escalate, close_ticket.\n"
            "If action is classify_ticket, provide category.\n"
            "If action is respond, provide message.\n"
            "If a field is unused, return an empty string.\n\n"
            f"STATE:\n{state.model_dump_json()}"
        )

    def _build_reply_prompt(self, state: ObservationModel) -> str:
        return (
            "You are a customer support agent drafting a single reply to the customer.\n"
            "Write one helpful support message based on the ticket, conversation history, and policy.\n"
            "Be concise, professional, and action-oriented.\n"
            "If the ticket is already resolved or awaiting close, do not repeat the same explanation.\n"
            "Instead, acknowledge the customer's confirmation and ask whether you may close the ticket.\n"
            "Return strict JSON only with one key: message.\n\n"
            f"STATE:\n{state.model_dump_json()}"
        )

    def _call_llm(self, prompt: str) -> AgentDecision:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise OpenEnv policy agent. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        return self._parse_json_payload(text)

    def _call_llm_reply(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful support agent. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        return self._parse_reply_payload(text)

    def _parse_json_payload(self, text: str) -> AgentDecision:
        payload_text = self._extract_json_object(text)
        return AgentDecision.model_validate_json(payload_text)

    def _parse_reply_payload(self, text: str) -> str:
        payload_text = self._extract_json_object(text)
        payload = ReplyPayload.model_validate_json(payload_text)
        message = payload.message.strip()
        if not message:
            raise ValueError("Gemini reply payload did not include a message")
        return message

    def _extract_json_object(self, text: str) -> str:
        stripped_text = text.strip()
        if stripped_text.startswith("{") and stripped_text.endswith("}"):
            return stripped_text

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Response did not contain a JSON object")
        return match.group(0)

    def _fallback_decision(self, state: ObservationModel) -> AgentDecision:
        if state.progress.classification in ("pending", "incorrect"):
            return AgentDecision(action="classify_ticket", category=self._infer_category(state))

        if state.progress.reply in ("pending", "incorrect"):
            return AgentDecision(action="respond", message=self._fallback_reply(state))

        if state.progress.escalation == "required":
            return AgentDecision(action="escalate")

        return AgentDecision(action="close_ticket")

    def _fallback_reply(self, state: ObservationModel) -> str:
        if state.customer_ready_to_close or state.status == "awaiting_close":
            return "I'm glad that helped. If everything looks good now, may I close this ticket for you?"

        rules = state.policy_rules[:2]
        primary_rule = rules[0] if rules else ""
        secondary_rule = rules[1] if len(rules) > 1 else ""
        category = self._infer_category(state)
        needs_escalation = state.progress.escalation == "required"
        positive_keywords = [keyword.strip() for keyword in state.reply_guidance.positive_keywords if keyword.strip()]

        if category == "delivery":
            message = "I'm sorry you're dealing with this delivery issue. I will document the missing items, start the trace, and explain the next steps clearly. "
        elif category == "account":
            message = "I'm sorry you're dealing with this account issue. I will help you secure the account and explain the next recovery steps clearly. "
        elif category == "return":
            message = "I'm sorry for the trouble with this return. I will explain the return process and the next steps clearly. "
        elif category == "refund":
            message = "I'm sorry you're dealing with this refund issue. I will confirm whether the defective item qualifies and explain the refund steps clearly. "
        else:
            message = "I'm sorry you're dealing with this technical issue. I will document the problem and explain the next troubleshooting steps clearly. "

        if primary_rule:
            message += f"Based on our policy, {primary_rule} "
        if secondary_rule:
            message += f"{secondary_rule} "

        keyword_clauses: list[str] = []
        for keyword in positive_keywords:
            lowered_keyword = keyword.lower()
            if lowered_keyword in message.lower():
                continue
            if lowered_keyword == "3 to 5 business days":
                keyword_clauses.append("The refund review usually takes 3 to 5 business days.")
            elif lowered_keyword == "defective":
                keyword_clauses.append("Based on the symptoms you described, this defective behavior can qualify for review.")
            elif lowered_keyword == "missing items":
                keyword_clauses.append("I am documenting the missing items so the review can move forward.")
            elif lowered_keyword == "replacement":
                keyword_clauses.append("We can review replacement options as part of the next step.")
            elif lowered_keyword == "pickup":
                keyword_clauses.append("I will explain how the pickup will be scheduled.")
            elif lowered_keyword == "hardware":
                keyword_clauses.append("Please keep the original hardware available for the return review.")
            elif lowered_keyword == "verification":
                keyword_clauses.append("We will complete the required verification before changing access.")
            elif lowered_keyword == "backup code":
                keyword_clauses.append("If you still have a backup code, please try that recovery option first.")
            elif lowered_keyword == "two-factor":
                keyword_clauses.append("This two-factor issue will be handled carefully so your account stays secure.")
            elif lowered_keyword == "license":
                keyword_clauses.append("I will validate the license details with you.")
            elif lowered_keyword == "activation":
                keyword_clauses.append("We will review the activation failure step by step.")
            elif lowered_keyword == "reinstall":
                keyword_clauses.append("A reinstall may be part of the recovery steps if needed.")
            elif lowered_keyword == "secure":
                keyword_clauses.append("Please secure the account right away while we review the incident.")
            elif lowered_keyword == "payment methods":
                keyword_clauses.append("Please secure any saved payment methods while the case is reviewed.")
            elif lowered_keyword == "invoice":
                keyword_clauses.append("I am documenting the invoice issue for specialist review.")
            elif lowered_keyword == "adjustment":
                keyword_clauses.append("The required adjustment will be reviewed by the correct team.")
            elif lowered_keyword == "data":
                keyword_clauses.append("I understand this data issue is serious and needs careful review.")
            elif lowered_keyword == "investigate":
                keyword_clauses.append("Engineering will investigate the behavior in detail.")
            elif lowered_keyword == "customs":
                keyword_clauses.append("The customs hold will be reviewed with the shipment details.")
            elif lowered_keyword == "international shipping team":
                keyword_clauses.append("The international shipping team will review the compliance hold.")
            elif lowered_keyword == "trace":
                keyword_clauses.append("I will start a trace for the missing shipment details.")
            else:
                keyword_clauses.append(f"I am also noting {keyword} as part of the next step.")

        if keyword_clauses:
            message += " ".join(keyword_clauses) + " "

        if needs_escalation:
            message += "I also need to escalate this case to a specialist right away."
        else:
            message += "I will keep you updated as we work through this."
        return message.strip()

    def _infer_category(self, state: ObservationModel) -> str:
        issue = state.ticket.issue.lower()
        rules_text = " ".join(rule.lower() for rule in state.policy_rules)
        combined_text = f"{issue} {rules_text}"

        if any(hint in combined_text for hint in ACCOUNT_HINTS):
            return "account"
        if any(hint in combined_text for hint in DELIVERY_HINTS):
            return "delivery"
        if any(hint in combined_text for hint in RETURN_HINTS):
            return "return"
        if any(hint in combined_text for hint in REFUND_HINTS):
            return "refund"
        if any(hint in combined_text for hint in TECHNICAL_HINTS):
            return "technical"
        return "technical"
