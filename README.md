# Customer Support Ticket Resolution Environment

## Environment Description

This project implements an OpenEnv-compatible customer support environment for realistic ecommerce and SaaS support tickets. An agent must classify the issue, send a policy-aware customer response, escalate when the workflow requires it, and close the ticket only when the case is resolved correctly.

The environment is served by a FastAPI application and exposes deterministic task loading, grading, simulation, and state transitions.

Difficulty tiers:

- `easy`
- `medium`
- `hard`

## Action Space

Schema:

```json
{
  "action": "classify_ticket | respond | escalate | close_ticket",
  "message": "string | null",
  "category": "string | null"
}
```

Rules:

- `classify_ticket`
  - Required field: `category`
  - Allowed categories: `refund`, `return`, `delivery`, `account`, `technical`, `other`
- `respond`
  - Required field: `message`
- `escalate`
  - No extra fields required
- `close_ticket`
  - No extra fields required

## Observation Space

Schema:

```json
{
  "difficulty": "easy | medium | hard | null",
  "ticket": {
    "id": "string",
    "customer": "string",
    "issue": "string",
    "orderId": "string",
    "product": "string",
    "orderDateText": "string",
    "category": "string",
    "status": "string",
    "difficulty": "easy | medium | hard"
  },
  "status": "string",
  "done": "boolean",
  "steps_taken": "integer",
  "max_steps": "integer",
  "max_possible_reward": "float",
  "current_stage": "integer",
  "last_reward": "float",
  "reward_score": "float",
  "cumulative_reward": "float",
  "customer_ready_to_close": "boolean",
  "available_categories": ["string"],
  "available_actions": ["string"],
  "progress": {
    "classification": "pending | correct | incorrect",
    "reply": "pending | completed | incorrect",
    "escalation": "required | not_needed | completed | unnecessary"
  },
  "policy_rules": ["string"],
  "reply_guidance": {
    "positive_keywords": ["string"],
    "negative_keywords": ["string"]
  },
  "conversation_history": [
    {
      "role": "system | customer | agent",
      "message": "string"
    }
  ],
  "episode_metrics": {
    "actions_taken": ["string"],
    "classification_correct": "boolean",
    "reply_helpful": "boolean",
    "escalation_correct": "boolean",
    "closed_correctly": "boolean"
  },
  "info_messages": ["string"]
}
```

Idle `state()` returns a valid observation with `status: "idle"` and no active ticket.

## Reward Function

All rewards are deterministic floats in the range `0.0` to `1.0`.

Per-action grading:

- Classification
  - correct: `1.0`
  - incorrect: `0.0`
- Response
  - graded by positive keyword coverage, minimum message quality, off-policy penalties, and escalation expectation handling
  - output range: `0.0` to `1.0`
- Escalation
  - correct after customer communication: `1.0`
  - correct but premature: `0.6`
  - unnecessary: `0.0`
- Closure
  - correct and efficient: `1.0`
  - correct but late: `0.8`
  - incorrect: `0.0`

Episode score stays clamped to `0.0` to `1.0` while preserving partial scoring.

## Setup Instructions

Create `.env.local` from `.env.example`.

```bash
API_BASE_URL=
MODEL_NAME=
HF_TOKEN=
PYTHON_BACKEND_URL=http://127.0.0.1:8000
GEMINI_API_KEY=
OPENENV_RANDOM_SEED=7
```

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running Locally

Start the FastAPI API on port `8000`:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Running Inference

Run the deterministic baseline inference script:

```bash
python inference.py
```

The script:

- imports the OpenAI client and reads `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`
- falls back to a deterministic local policy when those variables are not configured or the remote call fails
- emits structured `[START]`, `[STEP]`, and `[END]` logs with rewards formatted to two decimal places
- evaluates every task across `easy`, `medium`, and `hard`
- writes a summarized score report to `inference_results.json`

Example log shape:

```text
[START] task=customer-support-baseline:TKT-E-1001 env=CustomerSupportTicketResolutionEnv model=heuristic-fallback
[STEP] step=1 action={"action":"classify_ticket","category":"refund"} reward=1.00 done=False error=remote_model_not_configured
[STEP] step=2 action={"action":"respond","message":"..."} reward=1.00 done=False error=remote_model_not_configured
[STEP] step=3 action={"action":"close_ticket"} reward=1.00 done=True error=remote_model_not_configured
[END] success=True steps=3 score=1.00 rewards=[1.00, 1.00, 1.00]
```

## API Endpoints

- `GET /`
- `GET /health`
- `GET /catalog`
- `GET /reset`
- `POST /reset`
- `POST /step`
- `GET /state`
- `POST /agent/auto`
- `POST /agent/draft-reply`

Examples:

Reset without a request body:

```bash
curl http://127.0.0.1:8000/reset
```

Reset with a request body:

```bash
curl -X POST http://127.0.0.1:8000/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"difficulty\":\"easy\",\"ticketId\":\"TKT-E-1001\"}"
```

Step:

```bash
curl -X POST http://127.0.0.1:8000/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action\":\"classify_ticket\",\"category\":\"refund\"}"
```

State:

```bash
curl http://127.0.0.1:8000/state
```

## Docker

Build the single-container image:

```bash
docker build -t openenv-customer-support .
```

Run it on port `8000`:

```bash
docker run --rm -p 8000:8000 --env-file .env.local openenv-customer-support
```

## Project Structure

```text
backend/app/models.py      Typed Pydantic models
backend/app/env.py         Environment implementation
backend/app/grader.py      Deterministic grading
backend/app/tasks.py       Task repository
backend/app/simulator.py   Customer simulation
backend/app/agent.py       Gemini-backed or fallback agent
backend/app/main.py        FastAPI entrypoint
inference.py               Deterministic inference runner
openenv.yaml               OpenEnv configuration
Dockerfile                 Single-container deployment
```
