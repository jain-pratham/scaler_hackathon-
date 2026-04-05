from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI

from backend.app.agent import GeminiDecisionAgent
from backend.app.env import CustomerSupportEnv
from backend.app.grader import SupportTicketGrader
from backend.app.models import Action, AgentDecision, InferenceEpisode, InferenceResults, InferenceTaskCase, Observation
from backend.app.simulator import CustomerSimulator
from backend.app.tasks import TaskRepository


ROOT_DIR = Path(__file__).resolve().parent
TASKS_DIR = ROOT_DIR / "tasks"
SEED = 7
TASK_SELECTIONS = [
    InferenceTaskCase(difficulty="easy", ticket_id="TKT-E-1001"),
    InferenceTaskCase(difficulty="medium", ticket_id="TKT-M-2001"),
    InferenceTaskCase(difficulty="hard", ticket_id="TKT-H-3001"),
]
RESULTS_PATH = ROOT_DIR / "inference_results.json"
ENV_FILES = (ROOT_DIR / ".env.local", ROOT_DIR / ".env", ROOT_DIR / ".env.example")


def load_env_files() -> None:
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key and key not in os.environ:
                os.environ[key] = value


class OpenAIInferenceAgent:
    def __init__(self) -> None:
        self.api_base_url = os.getenv("API_BASE_URL", "").strip()
        self.model_name = os.getenv("MODEL_NAME", "").strip()
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self.client: Optional[OpenAI] = None

        if self.api_base_url and self.model_name and self.hf_token:
            self.client = OpenAI(base_url=self.api_base_url, api_key=self.hf_token)

    def decide(self, observation: Observation) -> AgentDecision:
        if self.client is None:
            return self._fallback_decision(observation)

        prompt = (
            "You are controlling a deterministic OpenEnv customer-support environment. "
            "Return strict JSON only with keys action, message, category. "
            "Allowed actions: classify_ticket, respond, escalate, close_ticket. "
            "If a field is unused, return an empty string.\n\n"
            f"STATE:\n{observation.model_dump_json()}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=0,
                messages=[
                    {"role": "system", "content": "Respond with JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            return self._parse_decision(content)
        except Exception:
            return self._fallback_decision(observation)

    def _parse_decision(self, content: str) -> AgentDecision:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))
        return AgentDecision.model_validate(parsed)

    def _fallback_decision(self, observation: Observation) -> AgentDecision:
        return GeminiDecisionAgent(api_key=None).decide(observation)


def build_environment() -> CustomerSupportEnv:
    return CustomerSupportEnv(
        repository=TaskRepository(TASKS_DIR),
        grader=SupportTicketGrader(),
        simulator=CustomerSimulator(),
        agent=GeminiDecisionAgent(os.getenv("GEMINI_API_KEY")),
        seed=SEED,
    )


def run_inference() -> None:
    load_env_files()
    environment = build_environment()
    inference_agent = OpenAIInferenceAgent()
    episodes: list[InferenceEpisode] = []
    step_counter = 0

    print("[START]")

    for task_case in TASK_SELECTIONS:
        observation = environment.reset(
            session_id=f"inference-{task_case.difficulty}",
            difficulty=task_case.difficulty,
            ticket_id=task_case.ticket_id,
        )

        while not observation.done and observation.steps_taken < observation.max_steps:
            decision = inference_agent.decide(observation)
            step_counter += 1
            print(f"[STEP] step={step_counter}, action={decision.action}")
            result = environment.step(
                f"inference-{task_case.difficulty}",
                Action.model_validate(decision.model_dump()),
            )
            observation = result.observation
            if result.done:
                break

        episodes.append(
            InferenceEpisode(
                difficulty=task_case.difficulty,
                ticket_id=task_case.ticket_id,
                reward_score=observation.reward_score,
                steps_taken=observation.steps_taken,
                done=observation.done,
                status=observation.status,
            )
        )

    average_score = round(
        sum(episode.reward_score for episode in episodes) / max(len(episodes), 1),
        4,
    )
    results = InferenceResults(seed=SEED, average_score=average_score, episodes=episodes)
    RESULTS_PATH.write_text(json.dumps(results.model_dump(), indent=2), encoding="utf-8")
    print("[END]")


if __name__ == "__main__":
    run_inference()
