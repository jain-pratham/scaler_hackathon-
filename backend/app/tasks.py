from __future__ import annotations

from pathlib import Path

from .models import CatalogTicket, DifficultyLevel, Task, TaskBundle, TaskCache


DIFFICULTIES: tuple[DifficultyLevel, ...] = ("easy", "medium", "hard")


class TaskRepository:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self._cache = TaskCache()

    def _get_cached_bundle(self, difficulty: DifficultyLevel) -> TaskBundle | None:
        if difficulty == "easy":
            return self._cache.easy
        if difficulty == "medium":
            return self._cache.medium
        return self._cache.hard

    def _set_cached_bundle(self, difficulty: DifficultyLevel, bundle: TaskBundle) -> None:
        if difficulty == "easy":
            self._cache.easy = bundle
        elif difficulty == "medium":
            self._cache.medium = bundle
        else:
            self._cache.hard = bundle

    def _load_bundle(self, difficulty: DifficultyLevel) -> TaskBundle:
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"Unsupported difficulty: {difficulty}")

        cached_bundle = self._get_cached_bundle(difficulty)
        if cached_bundle is not None:
            return cached_bundle

        bundle_path = self.base_path / f"{difficulty}.json"
        bundle = TaskBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
        self._set_cached_bundle(difficulty, bundle)
        return bundle

    def list_tasks(self, difficulty: DifficultyLevel) -> list[Task]:
        bundle = self._load_bundle(difficulty)
        return [task.model_copy(deep=True) for task in bundle.tasks]

    def get_task(self, difficulty: DifficultyLevel, ticket_id: str) -> Task:
        for task in self._load_bundle(difficulty).tasks:
            if task.ticket.id == ticket_id or task.ticket_id == ticket_id:
                return task.model_copy(deep=True)
        raise KeyError(f"Ticket {ticket_id} not found for difficulty {difficulty}")

    def get_task_by_index(self, difficulty: DifficultyLevel, index: int) -> Task:
        tasks = self._load_bundle(difficulty).tasks
        return tasks[index % len(tasks)].model_copy(deep=True)

    def get_summary_catalog(self) -> list[CatalogTicket]:
        catalog: list[CatalogTicket] = []
        for difficulty in DIFFICULTIES:
            for task in self._load_bundle(difficulty).tasks:
                catalog.append(
                    CatalogTicket(
                        id=task.ticket.id,
                        category=task.display_category,
                        customer=task.ticket.customer,
                        issue=task.ticket.issue,
                        difficulty=difficulty,
                        status="open",
                        orderId=task.ticket.order_id,
                        product=task.ticket.product,
                        orderDateText=task.ticket.order_date_text,
                    )
                )
        return catalog
