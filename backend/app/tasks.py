from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Union


DIFFICULTIES = ("easy", "medium", "hard")


class TaskRepository:
    def __init__(self, base_path: Union[str, Path]) -> None:
        self.base_path = Path(base_path)
        self._cache: dict[str, dict[str, Any]] = {}

    def _load_bundle(self, difficulty: str) -> dict[str, Any]:
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"Unsupported difficulty: {difficulty}")

        if difficulty not in self._cache:
            bundle_path = self.base_path / f"{difficulty}.json"
            with bundle_path.open("r", encoding="utf-8") as handle:
                self._cache[difficulty] = json.load(handle)
        return self._cache[difficulty]

    def list_tasks(self, difficulty: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._load_bundle(difficulty)["tasks"])

    def get_task(self, difficulty: str, ticket_id: str) -> dict[str, Any]:
        for task in self._load_bundle(difficulty)["tasks"]:
            if task["ticket"]["id"] == ticket_id or task["ticket_id"] == ticket_id:
                return copy.deepcopy(task)
        raise KeyError(f"Ticket {ticket_id} not found for difficulty {difficulty}")

    def get_task_by_index(self, difficulty: str, index: int) -> dict[str, Any]:
        tasks = self._load_bundle(difficulty)["tasks"]
        return copy.deepcopy(tasks[index % len(tasks)])

    def get_summary_catalog(self) -> list[dict[str, Any]]:
        catalog: list[dict[str, Any]] = []
        for difficulty in DIFFICULTIES:
            for task in self._load_bundle(difficulty)["tasks"]:
                ticket = task["ticket"]
                catalog.append(
                    {
                        "id": ticket["id"],
                        "category": task["display_category"],
                        "customer": ticket["customer"],
                        "issue": ticket["issue"],
                        "difficulty": difficulty,
                        "status": "open",
                        "orderId": ticket["order_id"],
                        "product": ticket["product"],
                        "orderDateText": ticket["order_date_text"],
                    }
                )
        return catalog
