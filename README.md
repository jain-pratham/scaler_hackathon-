---
title: OpenEnv Support Agent
emoji: "🤖"
colorFrom: blue
colorTo: indigo
sdk: docker
tags:
  - openenv
app_port: 8000
pinned: false
---

# Customer Support OpenEnv Environment

`openenv-support-agent` is a realistic multi-step environment designed for training and evaluating AI agents on customer support workflows.

Instead of treating support as a single reply, this environment models the full lifecycle:

1. classify the issue
2. respond with policy-aware guidance
3. escalate if required
4. close the ticket correctly

---

## Problem Statement

Most chatbot benchmarks are too simple:

* they evaluate single responses instead of workflows
* they ignore escalation logic
* they don’t simulate real customer scenarios
* they lack transparent reward systems

This project solves that by turning support handling into a structured, multi-step environment.

---

## Why This Matters

In real systems, good support handling prevents:

* customer dissatisfaction
* refund losses
* escalation overload
* policy violations

This environment helps:

* evaluate agent decision-making
* train RL-based workflows
* simulate real-world support systems
* benchmark reasoning + action sequencing

---

## Environment Design

```text
Agent / Inference Script
        |
        v
FastAPI Backend
  - /reset
  - /step
  - /state
  - /health
        |
        v
CustomerSupportEnv
  - reset()
  - step()
  - state()
        |
        v
Grader System
  - classification scoring
  - response quality scoring
  - escalation correctness
  - closure validation
        |
        v
Task Dataset
  - easy / medium / hard tickets
```

---

## Action Space

```json
{
  "action": "classify_ticket | respond | escalate | close_ticket",
  "message": "string | null",
  "category": "string | null"
}
```

---

## Observation Space

The environment returns structured state including:

* ticket details
* progress tracking
* conversation history
* reward signals
* policy guidance

---

## Reward System

Each episode returns a score between `0.0 → 1.0`.

Breakdown:

* Classification → correctness
* Response → quality + relevance
* Escalation → correct decision
* Closure → correct timing

Supports:

* partial rewards
* deterministic grading
* explainable scoring

---

## Tasks

The environment includes 3 difficulty levels:

* **Easy** → straightforward classification + response
* **Medium** → reasoning + response quality
* **Hard** → escalation + multi-step correctness

Each task simulates real customer issues.

---

## Inference

Run full evaluation:

```bash
python inference.py
```

Output:

* structured logs `[START] → [STEP] → [END]`
* reward scores
* inference_results.json

---

## Local Run

Start backend:

```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Test:

```
http://localhost:8000/reset
```

---

## Docker

Build:

```bash
docker build -t openenv-support-agent .
```

Run:

```bash
docker run -p 8000:8000 openenv-support-agent
```

---

## Hugging Face Spaces Deployment

1. Create Space → Docker
2. Upload project files
3. Add environment variables:

```
API_BASE_URL=
MODEL_NAME=
HF_TOKEN=
GEMINI_API_KEY=
```

4. Deploy

---

## API Endpoints

* `GET /` → health check
* `GET /reset` → start new episode
* `POST /step` → take action
* `GET /state` → current state

---

## Project Structure

```text
backend/
tasks/
openenv.yaml
inference.py
Dockerfile
README.md
```

---

## License

MIT
