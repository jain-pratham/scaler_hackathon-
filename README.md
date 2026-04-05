---

title: Customer Support OpenEnv
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
-------------

# Customer Support Ticket Resolution Environment

## Environment Description

This project implements an OpenEnv-compatible customer support environment for realistic ecommerce and SaaS support tickets. An agent must classify the issue, send a policy-aware customer response, escalate when the workflow requires it, and close the ticket only when the case is resolved correctly.

The environment is served by a FastAPI application and exposes deterministic task loading, grading, simulation, and state transitions.

Difficulty tiers:

* `easy`
* `medium`
* `hard`

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

* `classify_ticket`

  * Required field: `category`
  * Allowed categories: `refund`, `return`, `delivery`, `account`, `technical`, `other`
* `respond`

  * Required field: `message`
* `escalate`

  * No extra fields required
* `close_ticket`

  * No extra fields required

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

## Reward Function

All rewards are deterministic floats in the range `0.0` to `1.0`.

* Classification → `1.0 / 0.0`
* Response → `0.0 to 1.0`
* Escalation → `1.0 / 0.6 / 0.0`
* Closure → `1.0 / 0.8 / 0.0`

## Setup Instructions

```bash
API_BASE_URL=
MODEL_NAME=
HF_TOKEN=
PYTHON_BACKEND_URL=http://127.0.0.1:8000
GEMINI_API_KEY=
OPENENV_RANDOM_SEED=7
```

Install:

```bash
python -m pip install -r requirements.txt
```

## Running Locally

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Running Inference

```bash
python inference.py
```

## API Endpoints

* `/`
* `/health`
* `/reset`
* `/step`
* `/state`

## Docker

```bash
docker build -t openenv-customer-support .
docker run -p 8000:8000 openenv-customer-support
```
