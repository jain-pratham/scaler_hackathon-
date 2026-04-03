# OpenEnv Customer Support AI Environment - Project Specification

## Project Overview

This project builds an **OpenEnv-based AI environment** for a hackathon that simulates a **customer support ticket system**. An AI agent interacts with the environment to solve real-world customer issues, receiving rewards for correct actions and penalties for mistakes.

**Key Principle**: The environment is **agent-driven, not button-driven**. No UI required.

---

## Environment Specifications

### OpenEnv API Implementation

The environment must implement the standard OpenEnv interface:

```python
class CustomerSupportEnv:
    def reset() → (initial_state, info)
        # Load a new ticket from the appropriate difficulty level
        # Return initial ticket state and metadata
    
    def step(action) → (observation, reward, done, truncated, info)
        # Process agent action
        # Return next state, reward, and episode status
    
    def state() → current_state
        # Return the current state without modifying it
```

---

## Agent Actions

The agent interacts with the environment through **4 discrete actions**:

| Action | Description | Expected Outcome |
|--------|-------------|------------------|
| **classify_ticket** | Identify the issue type (delivery, refund, return, account, other) | Agent selects the correct category for the ticket |
| **respond** | Send a reply to the customer (selected from templates or generated) | Agent provides helpful, policy-compliant response |
| **escalate** | Send the issue to a higher support tier | Agent recognizes complex issues requiring specialist assistance |
| **close_ticket** | Mark the issue as resolved | Agent confirms all customer concerns have been addressed |

---

## Difficulty Levels & Task Characteristics

### Easy Difficulty
- **Ticket Complexity**: Simple, single-issue tickets
- **Resolution Steps**: 1-2 actions needed
- **Examples**:
  - Simple shipping inquiry
  - Basic refund request with clear eligibility
  - Account status check
- **Reward Strategy**: Straightforward path to positive rewards

### Medium Difficulty
- **Ticket Complexity**: Multi-step issues requiring policy understanding
- **Resolution Steps**: 2-4 actions needed
- **Examples**:
  - Refund request requiring eligibility verification
  - Return process with condition checks
  - Mixed issues (e.g., delivery + refund)
- **Reward Strategy**: Requires correct classification and policy application

### Hard Difficulty
- **Ticket Complexity**: Complex scenarios with multiple issues, conversation flow, possible escalation needs
- **Resolution Steps**: 3-5+ actions needed
- **Examples**:
  - Multiple sequential issues requiring careful handling
  - Edge cases challenging policy interpretation
  - Issues requiring escalation after initial investigation
  - Emotionally complex situations (angry/confused customers)
- **Reward Strategy**: High reward for correct handling; severe penalty for missteps

---

## Reward System

The grader evaluates each agent trajectory and awards rewards based on:

### Positive Rewards
- ✅ **Correct classification** of ticket type: +0.2
- ✅ **Appropriate response** addressing customer concern: +0.2
- ✅ **Correct decision-making** (escalate when needed, close when resolved): +0.3
- ✅ **Efficient resolution** (minimal steps): +0.2

### Negative Rewards (Penalties)
- ❌ **Incorrect classification**: -0.2
- ❌ **Unhelpful or off-policy response**: -0.2
- ❌ **Unnecessary escalation**: -0.1
- ❌ **Premature closure** (unresolved issue): -0.3
- ❌ **Failure to escalate** when escalation needed: -0.25

### Final Score
- **Range**: 0.0 to 1.0
- **Calculation**: Each episode receives a cumulative score based on actions taken
- **Grading**: Hidden ground truth evaluates whether the agent's trajectory matches the optimal solution path

---

## Task Storage Format

Tasks are stored as **JSON files** (no database required):

### File Structure
```
tasks/
├── easy.json       # Easy difficulty tickets
├── medium.json     # Medium difficulty tickets
└── hard.json       # Hard difficulty tickets
```

### JSON Schema - Individual Ticket
```json
{
  "ticket_id": "TKT-001",
  "difficulty": "easy",
  "customer_name": "John Doe",
  "issue_description": "My package hasn't arrived yet",
  "order_id": "ORD-12345",
  "timestamp": "2024-04-01T10:30:00Z",
  "metadata": {
    "order_date": "2024-03-25",
    "delivery_promised": "2024-04-01",
    "issue_type": "delivery"
  },
  "correct_actions": [
    {"action": "classify_ticket", "parameter": "delivery"},
    {"action": "respond", "parameter": "We'll track your package immediately"},
    {"action": "close_ticket", "parameter": "issue_resolved"}
  ],
  "max_steps": 5,
  "positive_keywords": ["track", "update", "arrival"],
  "negative_keywords": ["refund immediately", "escalate now"]
}
```

### JSON Schema - Task Collection
```json
{
  "tasks": [
    { ticket object },
    { ticket object }
  ],
  "metadata": {
    "total_count": 10,
    "difficulty": "easy",
    "version": "1.0"
  }
}
```

---

## State Representation

The environment's internal state tracks:

```json
{
  "current_ticket": {
    "id": "TKT-001",
    "description": "...",
    "issue_type": null,
    "status": "open",
    "steps_taken": 0
  },
  "conversation_history": [
    {"role": "customer", "message": "..."},
    {"role": "agent", "message": "..."}
  ],
  "episode_metrics": {
    "cumulative_reward": 0.0,
    "actions_taken": [],
    "is_correct": null
  }
}
```

---

## Implementation Requirements

### Core Components

1. **Environment Class** (`env.py`)
   - Implements OpenEnv API
   - Manages ticket loading and state transitions
   - Calculates rewards based on grading logic
   - In-memory state management

2. **Task Manager** (`tasks.py`)
   - Loads JSON task files
   - Provides random ticket selection per difficulty
   - Manages task metadata

3. **Grader/Evaluator** (`grader.py`)
   - Evaluates agent actions against ground truth
   - Calculates rewards and final scores
   - Tracks episode statistics

4. **Baseline Agent** (`baseline_agent.py`)
   - Simple rule-based agent for testing
   - Produces reproducible, documentable scores
   - Serves as reference implementation

---

## Configuration Files

### `openenv.yaml`
Must define:
- Environment name and version
- Action space specification
- Observation space specification
- Difficulty levels and task counts
- Reward bounds (min: -1.0, max: 1.0)

Example:
```yaml
name: "CustomerSupportEnv"
version: "1.0"
action_space:
  type: "discrete"
  size: 4
observation_space:
  type: "text"
difficulty_levels: ["easy", "medium", "hard"]
max_steps_per_episode: 10
reward_bounds: [-1.0, 1.0]
```

### `docker/Dockerfile`
- Base Python image (3.10+)
- Install dependencies from `requirements.txt`
- Copy environment files
- Expose port for serving (if distributed)

### `requirements.txt`
- `gym>=0.26.0` (or Gymnasium)
- `numpy`
- `json` (built-in)
- Any additional dependencies for grading/evaluation

---

## Deployment Requirements

### Docker Setup
- Build image: `docker build -t customer-support-env .`
- Run: `docker run -p 8000:8000 customer-support-env`

### Hugging Face Spaces Integration
- Push to HF Spaces with Space type: "Docker"
- Include:
  - Dockerfile
  - `openenv.yaml`
  - Task JSON files
  - Environment code
  - README with setup instructions
- Space directory structure mirrors repo structure

### Reproducibility
- Fix random seed for baseline agent
- Document exact dependencies and versions
- Include example agent runs with expected scores

---

## Test Scenarios

### Baseline Testing
Run baseline agent 100 episodes across each difficulty:
- **Easy**: Expected score 0.8-1.0
- **Medium**: Expected score 0.6-0.8
- **Hard**: Expected score 0.4-0.7

### Metrics to Track
- Average reward per episode
- Success rate (correct resolution)
- Escalation rate (should vary by difficulty)
- Episode length (steps to resolution)

---

## Directory Structure

```
scaler_hackathon-/
├── src/
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.js
│   │   └── globals.css
│   ├── env.py                    # Main environment class
│   ├── tasks.py                  # Task management
│   ├── grader.py                 # Reward calculation & grading
│   └── baseline_agent.py         # Reference agent
├── tasks/
│   ├── easy.json
│   ├── medium.json
│   └── hard.json
├── docker/
│   └── Dockerfile
├── openenv.yaml
├── requirements.txt
├── package.json
├── next.config.mjs
├── eslint.config.mjs
├── jsconfig.json
├── postcss.config.mjs
├── README.md
├── PROJECT_SPECIFICATION.md      # This file
├── AGENTS.md
└── CLAUDE.md
```

---

## README Structure (To Document)

The README should include:

1. **Overview** - What this environment does
2. **Installation**
   - Clone repo
   - Install Python dependencies
   - Download/setup tasks
3. **Quick Start**
   - How to instantiate the environment
   - Example agent interaction
4. **API Reference**
   - `reset()` parameters and returns
   - `step(action)` parameters and returns
   - `state()` return format
5. **Actions Reference** - Detailed action descriptions
6. **Task Structure** - JSON schema and examples
7. **Reward System** - Scoring logic and examples
8. **Running Baseline Agent** - Commands and expected output
9. **Deployment** - Docker and HF Spaces setup
10. **Contributing** - How to add new tasks

---

## Success Criteria

✅ Environment implements full OpenEnv API  
✅ 4 discrete actions fully functional  
✅ 3 difficulty levels with 10+ tasks each  
✅ Reward system discriminates between good/bad actions  
✅ Baseline agent achieves expected scores  
✅ Reproducible with fixed seed  
✅ Docker deployment functional  
✅ HF Spaces integration complete  
✅ Comprehensive README with examples  
✅ Task JSON files properly formatted and validated  

---

## Notes for Implementation

- **No UI**: Focus on environment logic and agent interaction patterns
- **JSON over Database**: Keep tasks as JSON files for simplicity and portability
- **Reproducibility**: All random elements must be seedable
- **Clear Grading**: The grading logic must be unambiguous and deterministic
- **Documentation**: Each action type should have clear examples of correct/incorrect usage
- **Scalability**: Design for future expansion to 50+ tasks per difficulty level

---

**Last Updated**: April 3, 2026  
**Status**: Specification Ready for Development
