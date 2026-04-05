from __future__ import annotations

import random
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


DifficultyLevel = Literal["easy", "medium", "hard"]
ActionType = Literal["classify_ticket", "respond", "escalate", "close_ticket"]
ConversationRole = Literal["system", "customer", "agent"]
ClassificationStatus = Literal["pending", "correct", "incorrect"]
ReplyStatus = Literal["pending", "completed", "incorrect"]
EscalationStatus = Literal["required", "not_needed", "completed", "unnecessary"]


class ReplyGuidance(BaseModel):
    positive_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)


class CategoryOption(BaseModel):
    key: str
    label: str


class CategoryCatalog(BaseModel):
    options: list[CategoryOption] = Field(default_factory=list)

    def keys(self) -> list[str]:
        return [option.key for option in self.options]

    def label_for(self, key: str) -> str:
        for option in self.options:
            if option.key == key:
                return option.label
        return key.title()


class ResolutionRules(BaseModel):
    needs_escalation: bool = False
    can_close_after_response: bool = True


class CustomerSimulation(BaseModel):
    after_good_response: Optional[str] = None
    after_bad_response: Optional[str] = None
    after_followup_response: Optional[str] = None
    after_failed_close: Optional[str] = None
    after_escalation: Optional[str] = None


class Ticket(BaseModel):
    id: str
    customer: str
    issue: str
    order_id: str
    product: str
    order_date_text: str


class Task(BaseModel):
    ticket_id: str
    display_category: str
    expected_category: str
    expected_flow: list[ActionType]
    max_steps: int = 6
    policy_rules: list[str] = Field(default_factory=list)
    reply_guidance: ReplyGuidance = Field(default_factory=ReplyGuidance)
    resolution: ResolutionRules = Field(default_factory=ResolutionRules)
    customer_simulation: CustomerSimulation = Field(default_factory=CustomerSimulation)
    ticket: Ticket


class TaskBundleMetadata(BaseModel):
    difficulty: DifficultyLevel
    total_count: int
    version: str


class TaskBundle(BaseModel):
    metadata: TaskBundleMetadata
    tasks: list[Task]


class CatalogTicket(BaseModel):
    id: str
    category: str
    customer: str
    issue: str
    difficulty: DifficultyLevel
    status: str
    orderId: str
    product: str
    orderDateText: str


class CatalogResponse(BaseModel):
    tickets: list[CatalogTicket] = Field(default_factory=list)


class TicketState(BaseModel):
    id: str
    customer: str
    issue: str
    orderId: str
    product: str
    orderDateText: str
    category: str
    status: str
    difficulty: DifficultyLevel


class ConversationEntry(BaseModel):
    role: ConversationRole
    message: str


class Progress(BaseModel):
    classification: ClassificationStatus = "pending"
    reply: ReplyStatus = "pending"
    escalation: EscalationStatus = "not_needed"


class EpisodeMetrics(BaseModel):
    actions_taken: list[ActionType] = Field(default_factory=list)
    classification_correct: bool = False
    reply_helpful: bool = False
    escalation_correct: bool = False
    closed_correctly: bool = False


class State(BaseModel):
    difficulty: Optional[DifficultyLevel] = None
    ticket: Optional[TicketState] = None
    status: str = "idle"
    done: bool = False
    steps_taken: int = 0
    max_steps: int = 0
    max_possible_reward: float = 1.0
    current_stage: int = 0
    last_reward: float = 0.0
    reward_score: float = 0.0
    cumulative_reward: float = 0.0
    customer_ready_to_close: bool = False
    available_categories: list[str] = Field(default_factory=list)
    available_actions: list[ActionType] = Field(default_factory=list)
    progress: Progress = Field(default_factory=Progress)
    policy_rules: list[str] = Field(default_factory=list)
    reply_guidance: ReplyGuidance = Field(default_factory=ReplyGuidance)
    conversation_history: list[ConversationEntry] = Field(default_factory=list)
    episode_metrics: EpisodeMetrics = Field(default_factory=EpisodeMetrics)
    info_messages: list[str] = Field(default_factory=list)


class Observation(State):
    pass


class Action(BaseModel):
    action: ActionType
    message: Optional[str] = None
    category: Optional[str] = None


class ResetRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    difficulty: DifficultyLevel
    ticket_id: Optional[str] = Field(default=None, alias="ticketId")


class AutoAgentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    max_turns: int = Field(default=8, ge=1, le=12, alias="maxTurns")


class StepInfo(BaseModel):
    messages: list[str] = Field(default_factory=list)
    state: Observation


class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: StepInfo


class ResetResponse(BaseModel):
    ticket: TicketState
    state: Observation


class AgentDecision(BaseModel):
    action: ActionType
    message: str = ""
    category: str = ""


class GeminiTextPart(BaseModel):
    text: str


class GeminiContent(BaseModel):
    role: str
    parts: list[GeminiTextPart] = Field(default_factory=list)


class GeminiGenerationConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temperature: float
    response_mime_type: str = Field(alias="responseMimeType")


class GeminiGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    contents: list[GeminiContent] = Field(default_factory=list)
    generation_config: GeminiGenerationConfig = Field(alias="generationConfig")


class GeminiCandidateContent(BaseModel):
    parts: list[GeminiTextPart] = Field(default_factory=list)


class GeminiCandidate(BaseModel):
    content: GeminiCandidateContent = Field(default_factory=GeminiCandidateContent)


class GeminiGenerateResponse(BaseModel):
    candidates: list[GeminiCandidate] = Field(default_factory=list)


class ReplyPayload(BaseModel):
    message: str = ""


class AutoAgentTrajectoryStep(BaseModel):
    decision: AgentDecision
    reward: float
    done: bool


class AutoAgentResponse(BaseModel):
    state: Observation
    done: bool
    trajectory: list[AutoAgentTrajectoryStep] = Field(default_factory=list)


class DraftReplyResponse(BaseModel):
    message: str
    state: Observation


class HealthResponse(BaseModel):
    status: str


class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    rng: random.Random
    task: Task
    state: State


class SessionRegistry(BaseModel):
    sessions: list[Session] = Field(default_factory=list)

    def find(self, session_id: str) -> Optional[Session]:
        for session in self.sessions:
            if session.session_id == session_id:
                return session
        return None

    def upsert(self, session: Session) -> None:
        for index, existing in enumerate(self.sessions):
            if existing.session_id == session.session_id:
                self.sessions[index] = session
                return
        self.sessions.append(session)


class TaskCache(BaseModel):
    easy: Optional[TaskBundle] = None
    medium: Optional[TaskBundle] = None
    hard: Optional[TaskBundle] = None


class InferenceTaskCase(BaseModel):
    difficulty: DifficultyLevel
    ticket_id: str


class InferenceEpisode(BaseModel):
    difficulty: DifficultyLevel
    ticket_id: str
    reward_score: float
    steps_taken: int
    done: bool
    status: str


class InferenceResults(BaseModel):
    seed: int
    average_score: float
    episodes: list[InferenceEpisode] = Field(default_factory=list)


class InferenceEnvironmentConfig(BaseModel):
    api_base_url: str = ""
    model_name: str = ""
    hf_token: str = ""


class InferenceStepLog(BaseModel):
    step: int
    action: str


ActionModel = Action
ObservationModel = Observation
StateModel = State
StepInfoModel = StepInfo
StepResponseModel = StepResponse
ResetResponseModel = ResetResponse
TaskDefinition = Task
ResetRequestModel = ResetRequest
AutoAgentRequestModel = AutoAgentRequest
AutoAgentResponseModel = AutoAgentResponse
DraftReplyResponseModel = DraftReplyResponse
ProgressState = Progress
EnvironmentSession = Session
