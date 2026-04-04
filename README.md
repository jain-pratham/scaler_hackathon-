# Customer Support Ticket Resolution Environment

Next.js provides the existing dashboard UI. Route Handlers under `src/app/api/*` act as the backend-for-frontend layer. A FastAPI service in `backend/app/` owns environment state, reward logic, customer simulation, and Gemini-powered auto-agent runs.

## Architecture

```text
Dashboard UI (Next.js App Router)
  -> /api/reset
  -> /api/step
  -> /api/state
  -> /api/auto-agent
       -> FastAPI environment
            -> task JSON files
            -> reward / grading logic
            -> Gemini 1.5 Flash auto agent
```

## What Is Implemented

- `POST /api/reset`
  - Resets the active environment for the selected difficulty.
  - The UI also sends `ticketId` so clicking a queue item loads that exact task.
- `POST /api/step`
  - Supports `classify_ticket`, `respond`, `escalate`, and `close_ticket`.
- `GET /api/state`
  - Returns the current environment state for refresh or recovery.
- `POST /api/auto-agent`
  - Runs the Gemini loop until the task is done or the turn cap is reached.
- Python environment modules
  - `backend/app/tasks.py`
  - `backend/app/grader.py`
  - `backend/app/simulator.py`
  - `backend/app/agent.py`
  - `backend/app/env.py`
  - `backend/app/main.py`
- JSON task bundles
  - `tasks/easy.json`
  - `tasks/medium.json`
  - `tasks/hard.json`
- Docker support
  - `docker/python.Dockerfile`
  - `docker/next.Dockerfile`
  - `docker-compose.yml`

## UI Integration

The dashboard keeps the existing layout and now maps UI actions to the environment:

- Ticket selection -> `POST /api/reset`
- `Classify` button -> `POST /api/step` with `action: "classify_ticket"`
- Send message -> `POST /api/step` with `action: "respond"`
- `Escalate` button -> `POST /api/step` with `action: "escalate"`
- `Close` button -> `POST /api/step` with `action: "close_ticket"`
- `Auto Agent Mode` or `Run Auto Agent` -> `POST /api/auto-agent`

The UI updates from environment state:

- chat from `conversation_history`
- score panel from `reward_score` and `last_reward`
- progress panel from `progress`
- stage bar from `current_stage`
- ticket status from `ticket.status`

## Environment Variables

Create a root `.env.local` from `.env.example`.

```bash
PYTHON_BACKEND_URL=http://127.0.0.1:8000
GEMINI_API_KEY=your_gemini_key
OPENENV_RANDOM_SEED=7
```

`GEMINI_API_KEY` is optional for development. If it is missing or Gemini fails, the backend falls back to a deterministic rule-based agent so the environment still works.

## Local Run

Install JavaScript dependencies:

```bash
npm install
```

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
npm run dev:backend
```

Start the Next.js UI:

```bash
npm run dev:ui
```

Open `http://localhost:3000`.

## Docker

Run both services together:

```bash
docker compose up --build
```

UI: `http://localhost:3000`  
FastAPI: `http://localhost:8000`

## Example API Calls

Reset to an easy ticket:

```bash
curl -X POST http://localhost:3000/api/reset ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"difficulty\":\"easy\",\"ticketId\":\"TKT-E-1001\"}"
```

Classify:

```bash
curl -X POST http://localhost:3000/api/step ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"action\":\"classify_ticket\",\"category\":\"refund\"}"
```

Respond:

```bash
curl -X POST http://localhost:3000/api/step ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"action\":\"respond\",\"message\":\"I am sorry the speaker arrived damaged. You are eligible for a refund within 7 days and I will confirm the refund timeline for you now.\"}"
```

Escalate:

```bash
curl -X POST http://localhost:3000/api/step ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"action\":\"escalate\"}"
```

Close:

```bash
curl -X POST http://localhost:3000/api/step ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"action\":\"close_ticket\"}"
```

Read state:

```bash
curl http://localhost:3000/api/state -H "X-Session-Id: demo-session"
```

Run the auto agent:

```bash
curl -X POST http://localhost:3000/api/auto-agent ^
  -H "Content-Type: application/json" ^
  -H "X-Session-Id: demo-session" ^
  -d "{\"maxTurns\":8}"
```

## Reward System

- correct classification: `+0.2`
- helpful policy-compliant reply: `+0.2`
- correct escalation: `+0.3`
- correct closure: `+0.3`
- efficient closure bonus: `+0.2`
- incorrect classification: `-0.2`
- poor reply: `-0.2`
- unnecessary escalation: `-0.1`
- early closing: `-0.3`

The live score shown in the UI is a normalized `0.00` to `1.00` value derived from cumulative reward.

## Difficulty Levels

- `easy`
  - single-issue tickets that typically resolve after classify -> respond -> close
- `medium`
  - more policy-heavy tickets that still close without escalation when handled well
- `hard`
  - complex tickets that require a helpful response, escalation, and then closure

## OpenEnv Notes

`openenv.yaml` documents the action space, observation shape, reward bounds, and task files. The FastAPI environment itself exposes the `reset`, `step`, and `state` primitives expected by the UI and by any future agent runner.
