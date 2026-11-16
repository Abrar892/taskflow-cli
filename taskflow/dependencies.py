"""dependencies.py — Task dependency graph and blocker tracking for taskflow-cli."""

from __future__ import annotations
from typing import Dict, List, Set, Optional
from taskflow.models import Task


class DependencyGraph:
    """
    Tracks directed task dependency edges: task A depends on task B (B blocks A).
    Detects circular dependencies and identifies actionable vs blocked tasks.
    """

    def __init__(self):
        # task_id -> list of task_ids that it depends on
        self._depends_on: Dict[int, Set[int]] = {}
        # task_id -> list of task_ids that depend on it
        self._blocking: Dict[int, Set[int]] = {}

    def add_dependency(self, task_id: int, depends_on_id: int) -> None:
        """Add rule: task_id depends on depends_on_id."""
        if task_id == depends_on_id:
            raise ValueError("Task cannot depend on itself")

        # Cycle check: does depends_on_id reach task_id?
        if self._reaches(depends_on_id, task_id):
            raise ValueError(f"Adding dependency {task_id} -> {depends_on_id} creates a circular dependency cycle")

        self._depends_on.setdefault(task_id, set()).add(depends_on_id)
        self._blocking.setdefault(depends_on_id, set()).add(task_id)

    def _reaches(self, start: int, target: int) -> bool:
        visited = set()
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr == target:
                return True
            if curr not in visited:
                visited.add(curr)
                queue.extend(self._depends_on.get(curr, set()))
        return False

    def get_dependencies(self, task_id: int) -> Set[int]:
        return self._depends_on.get(task_id, set())

    def get_blocked_tasks(self, task_id: int) -> Set[int]:
        return self._blocking.get(task_id, set())

    def is_blocked(self, task_id: int, completed_task_ids: Set[int]) -> bool:
        """A task is blocked if any of the tasks it depends on are not in completed_task_ids."""
        deps = self.get_dependencies(task_id)
        return not deps.issubset(completed_task_ids)
