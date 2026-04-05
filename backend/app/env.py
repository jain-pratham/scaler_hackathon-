from __future__ import annotations

import random

from .agent import GeminiDecisionAgent
from .grader import SupportTicketGrader
from .models import (
    Action,
    ActionType,
    AutoAgentResponse,
    AutoAgentTrajectoryStep,
    CategoryCatalog,
    CategoryOption,
    ConversationEntry,
    DifficultyLevel,
    DraftReplyResponse,
    EpisodeMetrics,
    Observation,
    Progress,
    Session,
    SessionRegistry,
    State,
    StepInfo,
    StepResponse,
    Task,
    TicketState,
)
from .simulator import CustomerSimulator
from .tasks import TaskRepository


SUPPORTED_ACTIONS: list[ActionType] = ["classify_ticket", "respond", "escalate", "close_ticket"]
CATEGORY_CATALOG = CategoryCatalog(
    options=[
        CategoryOption(key="refund", label="Refund Request"),
        CategoryOption(key="return", label="Return Request"),
        CategoryOption(key="delivery", label="Delivery Problem"),
        CategoryOption(key="account", label="Account Issue"),
        CategoryOption(key="technical", label="Technical Support"),
        CategoryOption(key="other", label="Other"),
    ]
)


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


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
        self.sessions = SessionRegistry()

    def reset(
        self,
        session_id: str,
        difficulty: DifficultyLevel,
        ticket_id: str | None = None,
    ) -> Observation:
        existing_session = self.sessions.find(session_id)
        rng = existing_session.rng if existing_session is not None else random.Random(f"{self.seed}:{session_id}")
        task = (
            self.repository.get_task(difficulty, ticket_id)
            if ticket_id
            else self.repository.get_task_by_index(difficulty, rng.randrange(len(self.repository.list_tasks(difficulty))))
        )
        state = self._build_initial_state(task, difficulty)
        self.sessions.upsert(Session(session_id=session_id, rng=rng, task=task, state=state))
        return self._public_state(state)

    def state(self, session_id: str) -> Observation:
        session = self.sessions.find(session_id)
        if session is None:
            return Observation(
                status="idle",
                done=False,
                reward_score=0.0,
                available_categories=CATEGORY_CATALOG.keys(),
                available_actions=list(SUPPORTED_ACTIONS),
            )
        return self._public_state(session.state)

    def step(self, session_id: str, action: Action) -> StepResponse:
        session = self._get_session(session_id)
        state = session.state
        task = session.task
        feedback: list[str] = []

        if state.done:
            observation = self._public_state(state)
            return StepResponse(
                observation=observation,
                reward=0.0,
                done=True,
                info=StepInfo(messages=["Episode already completed."], state=observation),
            )

        if state.steps_taken >= state.max_steps:
            state.done = True
            state.status = "max_steps_reached"
            state.ticket.status = state.status
            observation = self._public_state(state)
            return StepResponse(
                observation=observation,
                reward=0.0,
                done=True,
                info=StepInfo(messages=["Maximum step count reached."], state=observation),
            )

        reward = 0.0
        state.steps_taken += 1
        state.episode_metrics.actions_taken.append(action.action)

        if action.action == "classify_ticket":
            reward, is_correct = self.grader.evaluate_classification(task, action.category)
            normalized_category = (action.category or "").strip().lower() or "other"
            state.ticket.category = CATEGORY_CATALOG.label_for(normalized_category)
            state.progress.classification = "correct" if is_correct else "incorrect"
            state.episode_metrics.classification_correct = is_correct
            feedback.append(
                "Classification matched the expected category."
                if is_correct
                else f"Expected category was {task.display_category}."
            )
            state.status = "classified"
            state.current_stage = max(state.current_stage, 1)

        elif action.action == "respond":
            reward, helpful, response_feedback = self.grader.evaluate_response(task, state, action.message)
            state.conversation_history.append(ConversationEntry(role="agent", message=(action.message or "").strip()))
            feedback.extend(response_feedback or ["Response recorded."])
            state.progress.reply = "completed" if helpful else "incorrect"
            state.episode_metrics.reply_helpful = helpful
            customer_message = self.simulator.next_customer_message(
                task=task,
                action="respond",
                helpful=helpful,
                already_replied=state.customer_ready_to_close,
            )
            if customer_message is not None:
                state.conversation_history.append(ConversationEntry(role="customer", message=customer_message))

            state.customer_ready_to_close = (
                bool(helpful)
                and (not task.resolution.needs_escalation)
                and task.resolution.can_close_after_response
            )
            if task.resolution.needs_escalation:
                state.status = "needs_escalation"
                state.progress.escalation = "required"
            elif helpful:
                state.status = "awaiting_close"
            else:
                state.status = "customer_waiting"
            state.current_stage = max(state.current_stage, 2)

        elif action.action == "escalate":
            reward, correct, escalation_feedback = self.grader.evaluate_escalation(task, state)
            state.progress.escalation = "completed" if correct else "unnecessary"
            state.episode_metrics.escalation_correct = correct
            feedback.append(escalation_feedback)
            customer_message = self.simulator.next_customer_message(
                task=task,
                action="escalate",
                helpful=correct,
                already_replied=False,
            )
            if customer_message is not None:
                state.conversation_history.append(ConversationEntry(role="customer", message=customer_message))
            state.status = "escalated" if correct else "in_progress"
            state.customer_ready_to_close = correct
            state.current_stage = max(state.current_stage, 3)

        else:
            reward, closed_correctly, close_feedback = self.grader.evaluate_closure(task, state)
            feedback.extend(close_feedback)
            state.episode_metrics.closed_correctly = closed_correctly
            if closed_correctly:
                state.done = True
                state.status = "closed"
                state.ticket.status = "closed"
                state.current_stage = 3
                state.conversation_history.append(
                    ConversationEntry(role="system", message="Ticket closed successfully.")
                )
            else:
                state.status = "reopened"
                customer_message = self.simulator.next_customer_message(
                    task=task,
                    action="close_ticket",
                    helpful=False,
                    already_replied=False,
                )
                if customer_message is not None:
                    state.conversation_history.append(ConversationEntry(role="customer", message=customer_message))

        state.last_reward = clamp_score(reward)
        state.cumulative_reward = clamp_score(
            state.cumulative_reward + (state.last_reward / max(state.max_possible_reward, 1.0))
        )
        state.reward_score = state.cumulative_reward
        state.ticket.status = state.status
        state.info_messages = feedback

        if state.steps_taken >= state.max_steps and not state.done:
            state.done = True
            state.status = "max_steps_reached"
            state.ticket.status = state.status
            feedback.append("Maximum step count reached before resolution.")

        observation = self._public_state(state)
        return StepResponse(
            observation=observation,
            reward=state.last_reward,
            done=state.done,
            info=StepInfo(messages=feedback, state=observation),
        )

    def run_auto_agent(self, session_id: str, max_turns: int = 8) -> AutoAgentResponse:
        session = self._get_session(session_id)
        trajectory: list[AutoAgentTrajectoryStep] = []

        for _ in range(max_turns):
            if session.state.done:
                break

            decision = self.agent.decide(self._public_state(session.state))
            result = self.step(session_id, Action.model_validate_json(decision.model_dump_json()))
            trajectory.append(
                AutoAgentTrajectoryStep(decision=decision, reward=result.reward, done=result.done)
            )
            session = self._get_session(session_id)
            if result.done:
                break

        return AutoAgentResponse(
            state=self._public_state(session.state),
            done=session.state.done,
            trajectory=trajectory,
        )

    def generate_reply_draft(self, session_id: str) -> DraftReplyResponse:
        session = self._get_session(session_id)
        observation = self._public_state(session.state)
        return DraftReplyResponse(message=self.agent.generate_reply(observation), state=observation)

    def _get_session(self, session_id: str) -> Session:
        session = self.sessions.find(session_id)
        if session is None:
            raise KeyError("No active ticket for this session. Call reset first.")
        return session

    def _build_initial_state(self, task: Task, difficulty: DifficultyLevel) -> State:
        escalation_status = "required" if task.resolution.needs_escalation else "not_needed"
        ticket = TicketState(
            id=task.ticket.id,
            customer=task.ticket.customer,
            issue=task.ticket.issue,
            orderId=task.ticket.order_id,
            product=task.ticket.product,
            orderDateText=task.ticket.order_date_text,
            category="Pending classification",
            status="open",
            difficulty=difficulty,
        )
        return State(
            difficulty=difficulty,
            ticket=ticket,
            status="open",
            done=False,
            steps_taken=0,
            max_steps=task.max_steps,
            max_possible_reward=float(len(task.expected_flow)),
            current_stage=0,
            last_reward=0.0,
            reward_score=0.0,
            cumulative_reward=0.0,
            customer_ready_to_close=False,
            available_categories=CATEGORY_CATALOG.keys(),
            available_actions=list(SUPPORTED_ACTIONS),
            progress=Progress(classification="pending", reply="pending", escalation=escalation_status),
            policy_rules=task.policy_rules,
            reply_guidance=task.reply_guidance.model_copy(deep=True),
            conversation_history=[
                ConversationEntry(role="system", message="Ticket loaded. Review the policy panel before acting."),
                ConversationEntry(role="customer", message=task.ticket.issue),
            ],
            episode_metrics=EpisodeMetrics(),
            info_messages=[],
        )

    def _public_state(self, state: State) -> Observation:
        return Observation.model_validate_json(state.model_dump_json())
