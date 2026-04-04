from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agent import GeminiDecisionAgent
from .env import CustomerSupportEnv
from .grader import SupportTicketGrader
from .simulator import CustomerSimulator
from .tasks import TaskRepository


ROOT_DIR = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT_DIR / "tasks"

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
    version="1.0.0",
)


class ResetRequest(BaseModel):
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    ticketId: Optional[str] = None


class StepRequest(BaseModel):
    action: str = Field(
        pattern="^(classify_ticket|respond|escalate|close_ticket)$"
    )
    message: Optional[str] = None
    category: Optional[str] = None


class AutoAgentRequest(BaseModel):
    maxTurns: int = Field(default=8, ge=1, le=12)


def require_session_id(x_session_id: Optional[str]) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header.")
    return x_session_id


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/catalog")
def catalog() -> dict[str, object]:
    return {"tickets": repository.get_summary_catalog()}


@app.post("/reset")
def reset(payload: ResetRequest, x_session_id: Optional[str] = Header(default=None)) -> dict[str, object]:
    session_id = require_session_id(x_session_id)
    state = environment.reset(
        session_id=session_id,
        difficulty=payload.difficulty,
        ticket_id=payload.ticketId,
    )
    return {"ticket": state["ticket"], "state": state}


@app.post("/step")
def step(payload: StepRequest, x_session_id: Optional[str] = Header(default=None)) -> dict[str, object]:
    session_id = require_session_id(x_session_id)
    try:
        return environment.step(
            session_id=session_id,
            action=payload.action,
            message=payload.message,
            category=payload.category,
        )
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/state")
def state(x_session_id: Optional[str] = Header(default=None)) -> dict[str, object]:
    session_id = require_session_id(x_session_id)
    return environment.state(session_id)


@app.post("/agent/auto")
def auto_agent(
    payload: AutoAgentRequest,
    x_session_id: Optional[str] = Header(default=None),
) -> dict[str, object]:
    session_id = require_session_id(x_session_id)
    try:
        return environment.run_auto_agent(session_id, max_turns=payload.maxTurns)
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/agent/draft-reply")
def draft_reply(x_session_id: Optional[str] = Header(default=None)) -> dict[str, object]:
    session_id = require_session_id(x_session_id)
    try:
        return environment.generate_reply_draft(session_id)
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

