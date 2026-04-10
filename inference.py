from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from backend.app.agent import GeminiDecisionAgent
from backend.app.env import CustomerSupportEnv
from backend.app.grader import SupportTicketGrader
from backend.app.models import (
    Action,
    DifficultyLevel,
    InferenceEnvironmentConfig,
    InferenceEpisode,
    InferenceResults,
    Observation,
)
from backend.app.simulator import CustomerSimulator
from backend.app.tasks import DIFFICULTIES, TaskRepository


ROOT_DIR = Path(__file__).resolve().parent
TASKS_DIR = ROOT_DIR / "tasks"
RESULTS_PATH = ROOT_DIR / "inference_results.json"
BENCHMARK = "CustomerSupportTicketResolutionEnv"
TASK_NAME = "customer-support-baseline"
SUCCESS_SCORE_THRESHOLD = 0.80
ENV_FILE_CANDIDATES = (".env.local", ".env")

FALLBACK_AGENT = GeminiDecisionAgent(api_key=None)
REFUND_HINTS = (
    "refund",
    "charged",
    "billing",
    "invoice",
    "rebill",
    "rebilled",
    "adjustment",
    "defective",
)
DELIVERY_HINTS = (
    "delivery",
    "delivered",
    "shipment",
    "shipping",
    "package",
    "missing",
    "customs",
    "carrier",
    "trace",
)
RETURN_HINTS = (
    "return",
    "wrong size",
    "pickup",
    "hardware",
    "prepaid label",
)
TECHNICAL_HINTS = (
    "sync",
    "activation",
    "license",
    "app",
    "technical",
    "data",
    "design files",
    "reinstall",
)
ACCOUNT_HINTS = (
    "password",
    "account",
    "two-factor",
    "authenticator",
    "security",
    "fraud",
    "backup code",
    "shipping address",
    "payment methods",
)


def load_local_env_files() -> None:
    for file_name in ENV_FILE_CANDIDATES:
        env_path = ROOT_DIR / file_name
        if not env_path.exists():
            continue

        # Accept UTF-8 files saved with or without a BOM so .env.local works
        # consistently across Windows editors.
        for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and (key not in os.environ or not os.environ[key]):
                os.environ[key] = value


def load_environment_config() -> InferenceEnvironmentConfig:
    return InferenceEnvironmentConfig(
        api_base_url=os.getenv("API_BASE_URL", "").strip(),
        model_name=os.getenv("MODEL_NAME", "gemini-1.5-flash").strip(),
        api_key=os.getenv("API_KEY", "").strip(),
        hf_token=os.getenv("HF_TOKEN", "").strip(),
    )


def build_client(config: InferenceEnvironmentConfig) -> OpenAI:
    if not config.api_base_url or not config.api_key:
        raise ValueError("Missing API_BASE_URL or API_KEY in environment.")

    return OpenAI(
        base_url=config.api_base_url,
        api_key=config.api_key,
    )


def can_use_remote_model(config: InferenceEnvironmentConfig) -> bool:
    return bool(config.api_base_url and config.model_name and (config.api_key or config.hf_token))


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def format_reward(value: float) -> str:
    return f"{value:.2f}"


def format_rewards(values: list[float]) -> str:
    return "[" + ", ".join(format_reward(value) for value in values) + "]"


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: Action, reward: float, done: bool, error: str | None) -> None:
    print(
        "[STEP] "
        f"step={step} "
        f"action={action.model_dump_json(exclude_none=True)} "
        f"reward={format_reward(reward)} "
        f"done={done} "
        f"error={error}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    print(
        "[END] "
        f"success={success} "
        f"steps={steps} "
        f"score={format_reward(score)} "
        f"rewards={format_rewards(rewards)}",
        flush=True,
    )


def get_last_context_message(observation: Observation) -> str:
    if observation.conversation_history:
        return observation.conversation_history[-1].message
    return observation.ticket.issue


def build_model_prompt(
    step: int,
    last_context_message: str,
    last_reward: float,
    history: list[str],
    observation: Observation,
) -> str:
    recent_history = "\n".join(history[-6:]) if history else "No prior steps."
    return (
        "You are solving an OpenEnv customer support task.\n"
        "Return strict JSON only with keys: action, category, message.\n"
        "Allowed actions: classify_ticket, respond, escalate, close_ticket.\n"
        "Rules:\n"
        "- If action is classify_ticket, include category and leave message empty.\n"
        "- If action is respond, include message and leave category empty.\n"
        "- If action is escalate or close_ticket, leave message and category empty.\n"
        "- Stay policy-compliant and maximize the reward.\n\n"
        f"step={step}\n"
        f"last_context_message={last_context_message!r}\n"
        f"last_reward={format_reward(last_reward)}\n"
        f"history:\n{recent_history}\n\n"
        f"observation:\n{observation.model_dump_json()}"
    )


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return ""


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return json.loads(stripped)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(stripped[start : end + 1])


def infer_category(observation: Observation) -> str:
    issue = observation.ticket.issue.lower()
    if any(hint in issue for hint in REFUND_HINTS):
        return "refund"
    if any(hint in issue for hint in RETURN_HINTS):
        return "return"
    if any(hint in issue for hint in ACCOUNT_HINTS):
        return "account"
    if any(hint in issue for hint in TECHNICAL_HINTS):
        return "technical"
    if any(hint in issue for hint in DELIVERY_HINTS):
        return "delivery"

    rules_text = " ".join(rule.lower() for rule in observation.policy_rules)
    combined_text = f"{issue} {rules_text}"
    if any(hint in combined_text for hint in REFUND_HINTS):
        return "refund"
    if any(hint in combined_text for hint in RETURN_HINTS):
        return "return"
    if any(hint in combined_text for hint in ACCOUNT_HINTS):
        return "account"
    if any(hint in combined_text for hint in TECHNICAL_HINTS):
        return "technical"
    if any(hint in combined_text for hint in DELIVERY_HINTS):
        return "delivery"
    return "other"


def build_fallback_action(observation: Observation) -> Action:
    if observation.progress.classification in ("pending", "incorrect"):
        return Action(action="classify_ticket", category=infer_category(observation))
    if observation.progress.reply in ("pending", "incorrect"):
        return Action(action="respond", message=FALLBACK_AGENT.generate_reply(observation))
    if observation.progress.escalation == "required":
        return Action(action="escalate")
    return Action(action="close_ticket")


def normalize_action(candidate: dict[str, Any], observation: Observation) -> Action:
    action_name = str(candidate.get("action", "")).strip()
    if action_name not in {"classify_ticket", "respond", "escalate", "close_ticket"}:
        raise ValueError(f"Unsupported action from model: {action_name!r}")

    category = str(candidate.get("category", "") or "").strip().lower() or None
    message = str(candidate.get("message", "") or "").strip() or None

    if action_name == "classify_ticket":
        allowed_categories = set(observation.available_categories or [])
        if category not in allowed_categories:
            category = infer_category(observation)
        message = None
    elif action_name == "respond":
        if not message:
            message = FALLBACK_AGENT.generate_reply(observation)
        category = None
    else:
        category = None
        message = None

    return Action(action=action_name, category=category, message=message)


def get_model_action(
    client: OpenAI,
    config: InferenceEnvironmentConfig,
    step: int,
    last_context_message: str,
    last_reward: float,
    history: list[str],
    observation: Observation,
) -> tuple[Action, str | None]:
    if not can_use_remote_model(config):
        raise RuntimeError("Remote model is not properly configured. Check API_BASE_URL, API_KEY, and MODEL_NAME.")

    prompt = build_model_prompt(
        step=step,
        last_context_message=last_context_message,
        last_reward=last_reward,
        history=history,
        observation=observation,
    )

    try:
        completion = client.chat.completions.create(
            model=config.model_name,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise OpenEnv policy agent. Output JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        text = extract_text_content(completion.choices[0].message.content)
        action = normalize_action(extract_json_object(text), observation)
        return action, None
    except Exception as error:
        return build_fallback_action(observation), f"fallback:{type(error).__name__}"


def build_environment() -> CustomerSupportEnv:
    repository = TaskRepository(TASKS_DIR)
    grader = SupportTicketGrader()
    simulator = CustomerSimulator()
    return CustomerSupportEnv(
        repository=repository,
        grader=grader,
        simulator=simulator,
        agent=FALLBACK_AGENT,
        seed=int(os.getenv("OPENENV_RANDOM_SEED", "7")),
    )


def enumerate_task_cases(repository: TaskRepository) -> list[tuple[DifficultyLevel, str]]:
    cases: list[tuple[DifficultyLevel, str]] = []
    for difficulty in DIFFICULTIES:
        for task in repository.list_tasks(difficulty):
            cases.append((difficulty, task.ticket.id))
    return cases


async def run_episode(
    env: CustomerSupportEnv,
    client: OpenAI,
    config: InferenceEnvironmentConfig,
    difficulty: DifficultyLevel,
    ticket_id: str,
) -> InferenceEpisode:
    history: list[str] = []
    rewards: list[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    session_id = f"inference-{difficulty}-{ticket_id}"
    observation = env.reset(session_id=session_id, difficulty=difficulty, ticket_id=ticket_id)
    max_total_reward = max(observation.max_possible_reward, 1.0)
    last_context_message = get_last_context_message(observation)
    last_reward = 0.0
    model_label = config.model_name or "heuristic-fallback"

    log_start(task=f"{TASK_NAME}:{ticket_id}", env=BENCHMARK, model=model_label)

    try:
        for step in range(1, observation.max_steps + 1):
            if observation.done:
                break

            action, error = get_model_action(
                client=client,
                config=config,
                step=step,
                last_context_message=last_context_message,
                last_reward=last_reward,
                history=history,
                observation=observation,
            )

            result = env.step(session_id=session_id, action=action)
            observation = result.observation
            reward = clamp_score(result.reward or 0.0)

            rewards.append(reward)
            steps_taken = step
            last_context_message = get_last_context_message(observation)
            last_reward = reward

            log_step(step=step, action=action, reward=reward, done=result.done, error=error)
            history.append(
                f"Step {step}: {action.model_dump_json(exclude_none=True)} -> reward {reward:+.2f}"
            )

            if result.done:
                break

        score = clamp_score(sum(rewards) / max_total_reward)
        success = score >= SUCCESS_SCORE_THRESHOLD
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return InferenceEpisode(
        difficulty=difficulty,
        ticket_id=ticket_id,
        reward_score=score,
        steps_taken=steps_taken,
        done=observation.done,
        status=observation.status,
    )


async def main() -> None:
    config = load_environment_config()
    client = build_client(config)
    repository = TaskRepository(TASKS_DIR)
    env = build_environment()
    episodes: list[InferenceEpisode] = []

    for difficulty, ticket_id in enumerate_task_cases(repository):
        episodes.append(
            await run_episode(
                env=env,
                client=client,
                config=config,
                difficulty=difficulty,
                ticket_id=ticket_id,
            )
        )

    average_score = clamp_score(
        sum(episode.reward_score for episode in episodes) / max(len(episodes), 1)
    )
    results = InferenceResults(
        seed=int(os.getenv("OPENENV_RANDOM_SEED", "7")),
        average_score=average_score,
        episodes=episodes,
    )
    RESULTS_PATH.write_text(results.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
