# Customer Support Ticket Resolution Environment

## Environment Description

This project implements an OpenEnv-compatible customer support environment for resolving real-world ecommerce and SaaS support tickets. Agents must classify incoming tickets, send policy-compliant customer replies, escalate when required, and close tickets only when the issue is properly resolved.

The app includes:

- A Next.js App Router dashboard for human interaction and public route-handler APIs.
- A FastAPI backend that owns environment state, task loading, grading, simulation, and deterministic agent execution.
- Three difficulty tiers with policy-sensitive workflows:
  - `easy`
  - `medium`
  - `hard`

The public OpenEnv endpoints are:

- `POST /reset`
- `POST /step`
- `GET /state`
- `POST /agent/auto`

These routes proxy to the backend service and are available from the single-container deployment.

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

Example:

```json
{
  "action": "respond",
  "message": "I am sorry this happened. I have documented the issue and outlined the next steps.",
  "category": null
}
```

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

Episode score:

- `cumulative_reward` is a normalized running score in the range `0.0` to `1.0`
- `reward_score` is updated as:

```text
reward_score = cumulative_reward + (last_reward / max_possible_reward)
```

after clamping to `0.0` to `1.0`.

This preserves partial-progress feedback and keeps every reward output inside the required `0.0` to `1.0` range.

## Setup Instructions

### Environment variables

Create `.env.local` from `.env.example`.

```bash
API_BASE_URL=
MODEL_NAME=
HF_TOKEN=
PYTHON_BACKEND_URL=http://127.0.0.1:8000
GEMINI_API_KEY=
OPENENV_RANDOM_SEED=7
```

Notes:

- `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` are used by `inference.py` through the OpenAI-compatible client.
- `GEMINI_API_KEY` remains supported for the dashboard auto-agent and draft-reply backend.
- `PYTHON_BACKEND_URL` is used by the Next.js route handlers to reach the local FastAPI backend.

### Dependencies

Install JavaScript dependencies:

```bash
npm install
```

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running Locally

Start the FastAPI backend:

```bash
npm run dev:backend
```

Start the Next.js UI:

```bash
npm run dev:ui
```

Open:

- UI: `http://127.0.0.1:3000`
- Backend health: `http://127.0.0.1:8000/health`

### OpenEnv API examples

Reset:

```bash
curl -X POST http://127.0.0.1:3000/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"difficulty\":\"easy\",\"ticketId\":\"TKT-E-1001\"}"
```

Step:

```bash
curl -X POST http://127.0.0.1:3000/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action\":\"classify_ticket\",\"category\":\"refund\"}"
```

State:

```bash
curl http://127.0.0.1:3000/state
```

## Running Inference

Run the deterministic baseline inference script:

```bash
python inference.py
```

Runtime behavior:

- Uses `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` with the OpenAI client when configured.
- Falls back to a deterministic local policy if the remote model is unavailable.
- Prints logs in strict format:

```text
[START]
[STEP] step=1, action=classify_ticket
[STEP] step=2, action=respond
[END]
```

Scores are written to `inference_results.json`.

## Docker

Build the single-container image:

```bash
docker build -t openenv-customer-support .
```

Run it:

```bash
docker run --rm -p 7860:7860 --env-file .env.local openenv-customer-support
```

The single container starts:

- FastAPI on `127.0.0.1:8000` inside the container
- Next.js on the public port `7860`

## Hugging Face Spaces

This repository is configured for a single-container Docker deployment.

Recommended Space settings:

- SDK: `Docker`
- App port: `7860`
- Required variables:
  - `API_BASE_URL`
  - `MODEL_NAME`
  - `HF_TOKEN`
  - `GEMINI_API_KEY`
  - `OPENENV_RANDOM_SEED`

The public OpenEnv-compatible paths exposed by the Space are:

- `/reset`
- `/step`
- `/state`
- `/agent/auto`

## Project Structure

```text
backend/app/models.py      Typed Pydantic models
backend/app/env.py         Environment implementation
backend/app/grader.py      Deterministic grading
backend/app/tasks.py       Task repository
backend/app/simulator.py   Customer simulation
backend/app/agent.py       Gemini-backed / fallback agent
src/app/reset/route.js     Public reset endpoint
src/app/step/route.js      Public step endpoint
src/app/state/route.js     Public state endpoint
inference.py               Deterministic baseline runner
openenv.yaml               OpenEnv configuration
Dockerfile                 Single-container deployment
```

