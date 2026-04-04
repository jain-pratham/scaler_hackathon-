from __future__ import annotations

import copy
import random
from typing import Any, Optional

from .agent import GeminiDecisionAgent
from .grader import SupportTicketGrader
from .simulator import CustomerSimulator
from .tasks import TaskRepository


SUPPORTED_ACTIONS = {
    "classify_ticket",
    "respond",
    "escalate",
    "close_ticket",
}

CATEGORY_LABELS = {
    "refund": "Refund Request",
    "return": "Return Request",
    "delivery": "Delivery Problem",
    "account": "Account Issue",
    "technical": "Technical Support",
    "other": "Other",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class CustomerSupportEnv:
    def __init__(
        self,
        repository: TaskRepository,
        grader: SupportTicketGrader,
        simulator: CustomerSimulator,
        agent: GeminiDecisionAgent,
        seed: int = 7,
    ) -> None:
        self.repository = repository
        self.grader = grader
        self.simulator = simulator
        self.agent = agent
        self.seed = seed
        self.sessions: dict[str, dict[str, Any]] = {}

    def reset(
        self,
        session_id: str,
        difficulty: str,
        ticket_id: Optional[str] = None,
    ) -> dict[str, Any]:
        session = self.sessions.setdefault(
            session_id,
            {"rng": random.Random(f"{self.seed}:{session_id}")},
        )
        rng = session["rng"]

        if ticket_id:
            task = self.repository.get_task(difficulty, ticket_id)
        else:
            index = rng.randrange(len(self.repository.list_tasks(difficulty)))
            task = self.repository.get_task_by_index(difficulty, index)

        ticket = {
            "id": task["ticket"]["id"],
            "customer": task["ticket"]["customer"],
            "issue": task["ticket"]["issue"],
            "orderId": task["ticket"]["order_id"],
            "product": task["ticket"]["product"],
            "orderDateText": task["ticket"]["order_date_text"],
            "category": "Pending classification",
            "status": "open",
            "difficulty": difficulty,
        }

        state = {
            "difficulty": difficulty,
            "task": task,
            "ticket": ticket,
            "status": "open",
            "done": False,
            "steps_taken": 0,
            "max_steps": task.get("max_steps", 6),
            "current_stage": 0,
            "last_reward": 0.0,
            "reward_score": 0.5,
            "cumulative_reward": 0.0,
            "customer_ready_to_close": False,
            "available_categories": list(CATEGORY_LABELS.keys()),
            "available_actions": ["classify_ticket", "respond", "escalate", "close_ticket"],
            "progress": {
                "classification": "pending",
                "reply": "pending",
                "escalation": "required"
                if task["resolution"].get("needs_escalation")
                else "not_needed",
            },
            "policy_rules": task.get("policy_rules", []),
            "reply_guidance": task.get("reply_guidance", {}),
            "conversation_history": [
                {
                    "role": "system",
                    "message": "Ticket loaded. Review the policy panel before acting.",
                },
                {
                    "role": "customer",
                    "message": task["ticket"]["issue"],
                },
            ],
            "episode_metrics": {
                "actions_taken": [],
                "classification_correct": False,
                "reply_helpful": False,
                "escalation_correct": False,
                "closed_correctly": False,
            },
            "info_messages": [],
        }

        self.sessions[session_id] = {"rng": rng, "state": state}
        return self._serialize_state(state)

    def state(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session or "state" not in session:
            return {
                "status": "idle",
                "done": False,
                "reward_score": 0.5,
                "conversation_history": [],
                "progress": {
                    "classification": "pending",
                    "reply": "pending",
                    "escalation": "not_needed",
                },
            }
        return self._serialize_state(session["state"])

    def step(
        self,
        session_id: str,
        action: str,
        message: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict[str, Any]:
        if action not in SUPPORTED_ACTIONS:
            raise ValueError(f"Unsupported action: {action}")

        state = self._get_live_state(session_id)
        task = state["task"]
        feedback: list[str] = []

        if state["done"]:
            serialized = self._serialize_state(state)
            return {
                "observation": serialized,
                "reward": 0.0,
                "done": True,
                "info": {"message": "Episode already completed.", "state": serialized},
            }

        if state["steps_taken"] >= state["max_steps"]:
            state["done"] = True
            state["status"] = "max_steps_reached"
            state["ticket"]["status"] = state["status"]
            serialized = self._serialize_state(state)
            return {
                "observation": serialized,
                "reward": -0.2,
                "done": True,
                "info": {
                    "message": "Maximum step count reached.",
                    "state": serialized,
                },
            }

        reward = 0.0
        state["steps_taken"] += 1
        state["episode_metrics"]["actions_taken"].append(action)

        if action == "classify_ticket":
            reward, is_correct = self.grader.evaluate_classification(task, category)
            normalized_category = (category or "").strip().lower() or "other"
            state["ticket"]["category"] = CATEGORY_LABELS.get(normalized_category, normalized_category.title())
            state["progress"]["classification"] = "correct" if is_correct else "incorrect"
            state["episode_metrics"]["classification_correct"] = is_correct
            feedback.append(
                "Classification matched the expected category."
                if is_correct
                else f"Expected category was {task['display_category']}."
            )
            state["status"] = "classified"
            state["current_stage"] = max(state["current_stage"], 1)

        elif action == "respond":
            reward, helpful, response_feedback = self.grader.evaluate_response(task, state, message)
            state["conversation_history"].append(
                {"role": "agent", "message": (message or "").strip()}
            )
            feedback.extend(response_feedback or ["Response recorded."])
            state["progress"]["reply"] = "completed" if helpful else "incorrect"
            state["episode_metrics"]["reply_helpful"] = helpful
            already_replied = state["customer_ready_to_close"]
            customer_message = self.simulator.next_customer_message(
                task,
                action="respond",
                helpful=helpful,
                already_replied=already_replied,
            )
            if customer_message:
                state["conversation_history"].append(
                    {"role": "customer", "message": customer_message}
                )

            state["customer_ready_to_close"] = bool(helpful) and (
                task["resolution"].get("can_close_after_response")
                or not task["resolution"].get("needs_escalation")
            )
            if task["resolution"].get("needs_escalation"):
                state["status"] = "needs_escalation"
                state["progress"]["escalation"] = "required"
            elif helpful:
                state["status"] = "awaiting_close"
            else:
                state["status"] = "customer_waiting"
            state["current_stage"] = max(state["current_stage"], 2)

        elif action == "escalate":
            reward, correct, escalation_feedback = self.grader.evaluate_escalation(task, state)
            state["progress"]["escalation"] = "completed" if correct else "unnecessary"
            state["episode_metrics"]["escalation_correct"] = correct
            feedback.append(escalation_feedback)
            customer_message = self.simulator.next_customer_message(
                task,
                action="escalate",
                helpful=correct,
                already_replied=False,
            )
            if customer_message:
                state["conversation_history"].append(
                    {"role": "customer", "message": customer_message}
                )
            state["status"] = "escalated" if correct else "in_progress"
            state["customer_ready_to_close"] = correct
            state["current_stage"] = max(state["current_stage"], 3)

        elif action == "close_ticket":
            reward, closed_correctly, close_feedback = self.grader.evaluate_closure(task, state)
            feedback.extend(close_feedback)
            state["episode_metrics"]["closed_correctly"] = closed_correctly
            if closed_correctly:
                state["done"] = True
                state["status"] = "closed"
                state["ticket"]["status"] = "closed"
                state["current_stage"] = 3
                state["conversation_history"].append(
                    {
                        "role": "system",
                        "message": "Ticket closed successfully.",
                    }
                )
            else:
                state["status"] = "reopened"
                customer_message = self.simulator.next_customer_message(
                    task,
                    action="close_ticket",
                    helpful=False,
                    already_replied=False,
                )
                if customer_message:
                    state["conversation_history"].append(
                        {"role": "customer", "message": customer_message}
                    )

        state["last_reward"] = reward
        state["cumulative_reward"] = clamp(state["cumulative_reward"] + reward, -1.0, 1.0)
        state["reward_score"] = round(clamp(0.5 + (state["cumulative_reward"] / 2.0), 0.0, 1.0), 2)
        state["ticket"]["status"] = state["status"]
        state["info_messages"] = feedback

        if state["steps_taken"] >= state["max_steps"] and not state["done"]:
            state["done"] = True
            state["status"] = "max_steps_reached"
            state["ticket"]["status"] = state["status"]
            feedback.append("Maximum step count reached before resolution.")

        serialized = self._serialize_state(state)
        return {
            "observation": serialized,
            "reward": reward,
            "done": state["done"],
            "info": {
                "messages": feedback,
                "state": serialized,
            },
        }

    def run_auto_agent(self, session_id: str, max_turns: int = 8) -> dict[str, Any]:
        state = self._get_live_state(session_id)
        trajectory: list[dict[str, Any]] = []

        for _ in range(max_turns):
            if state["done"]:
                break

            decision = self.agent.decide(self._serialize_state(state))
            action = decision.get("action") or "close_ticket"
            result = self.step(
                session_id,
                action=action,
                message=decision.get("message"),
                category=decision.get("category"),
            )
            trajectory.append(
                {
                    "decision": decision,
                    "reward": result["reward"],
                    "done": result["done"],
                }
            )
            state = self._get_live_state(session_id)
            if result["done"]:
                break

        return {
            "state": self._serialize_state(state),
            "done": state["done"],
            "trajectory": trajectory,
        }

    def generate_reply_draft(self, session_id: str) -> dict[str, Any]:
        state = self._get_live_state(session_id)
        return {
            "message": self.agent.generate_reply(self._serialize_state(state)),
            "state": self._serialize_state(state),
        }

    def _get_live_state(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session or "state" not in session:
            raise KeyError("No active ticket for this session. Call reset first.")
        return session["state"]

    def _serialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        public_state = copy.deepcopy(state)
        public_state.pop("task", None)
        return public_state
