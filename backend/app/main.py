from __future__ import annotations
import traceback

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

from .agent import GeminiDecisionAgent
from .env import CustomerSupportEnv
from .grader import SupportTicketGrader
from .models import (
    Action,
    AutoAgentRequest,
    AutoAgentResponse,
    CatalogResponse,
    DraftReplyResponse,
    HealthResponse,
    Observation,
    ResetRequest,
    ResetResponse,
    StepResponse,
)
from .simulator import CustomerSimulator
from .tasks import TaskRepository


ROOT_DIR = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT_DIR / "tasks"
DEFAULT_SESSION_ID = "openenv-default-session"

repository = TaskRepository(TASKS_DIR)
grader = SupportTicketGrader()
simulator = CustomerSimulator()
agent = GeminiDecisionAgent(os.getenv("GEMINI_API_KEY"))
environment = CustomerSupportEnv(
    repository=repository,
    grader=grader,
    simulator=simulator,
    agent=agent,
    seed=int(os.getenv("OPENENV_RANDOM_SEED", "7")),
)

app = FastAPI(
    title="Customer Support Ticket Resolution Environment",
    version="1.2.0",
)


def resolve_session_id(x_session_id: Optional[str]) -> str:
    return x_session_id or DEFAULT_SESSION_ID


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/catalog", response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return CatalogResponse(tickets=repository.get_summary_catalog())


@app.api_route("/reset", methods=["GET", "POST"], response_model=ResetResponse)
def reset(
    payload: Optional[ResetRequest] = None,
    x_session_id: Optional[str] = Header(default=None),
) -> ResetResponse:
    try:
        session_id = resolve_session_id(x_session_id)

        # ✅ Default values if no body provided (IMPORTANT)
        difficulty = payload.difficulty if payload else "easy"
        ticket_id = payload.ticket_id if payload else None

        state = environment.reset(
            session_id=session_id,
            difficulty=difficulty,
            ticket_id=ticket_id,
        )

        if state.ticket is None:
            raise HTTPException(status_code=500, detail="Reset did not produce a ticket state.")

        return ResetResponse(ticket=state.ticket, state=state)

    except Exception as e:
        return ResetResponse(
            ticket=None,
            state=None,
        )


@app.post("/step", response_model=StepResponse)
def step(
    payload: Action,
    x_session_id: Optional[str] = Header(default=None),
) -> StepResponse:
    session_id = resolve_session_id(x_session_id)
    try:
        return environment.step(session_id=session_id, action=payload)
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/state", response_model=Observation)
def state(x_session_id: Optional[str] = Header(default=None)) -> Observation:
    session_id = resolve_session_id(x_session_id)
    return environment.state(session_id)


@app.post("/agent/auto", response_model=AutoAgentResponse)
def auto_agent(
    payload: AutoAgentRequest,
    x_session_id: Optional[str] = Header(default=None),
) -> AutoAgentResponse:
    session_id = resolve_session_id(x_session_id)
    try:
        return environment.run_auto_agent(session_id, max_turns=payload.max_turns)
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/agent/draft-reply", response_model=DraftReplyResponse)
def draft_reply(x_session_id: Optional[str] = Header(default=None)) -> DraftReplyResponse:
    session_id = resolve_session_id(x_session_id)
    try:
        return environment.generate_reply_draft(session_id)
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
