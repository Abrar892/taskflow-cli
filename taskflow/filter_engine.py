"""filter_engine.py — Advanced multi-attribute task query & filtering engine."""

from __future__ import annotations
from typing import List, Optional
from taskflow.models import Task
from taskflow.database import TaskflowDB


class TaskFilter:
    """Filter tasks using flexible combinations of status, priority, tags, and text search."""

    def __init__(self, db: TaskflowDB):
        self.db = db

    def query(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        search_query: Optional[str] = None,
        has_due_date: Optional[bool] = None,
    ) -> List[Task]:
        """Query tasks matching all non-None filter parameters."""
        tasks = self.db.list_tasks(project_id=project_id)
        results = []

        for t in tasks:
            if status is not None and t.status.lower() != status.lower():
                continue
            if priority is not None and t.priority.lower() != priority.lower():
                continue
            if tag is not None:
                task_tags = [x.strip().lower() for x in t.tags.split(",") if x.strip()]
                if tag.lower() not in task_tags:
                    continue
            if has_due_date is not None:
                if has_due_date and not t.due_date:
                    continue
                if not has_due_date and t.due_date:
                    continue
            if search_query is not None:
                sq = search_query.lower()
                in_title = sq in t.title.lower()
                in_desc = sq in t.description.lower()
                if not (in_title or in_desc):
                    continue
            results.append(t)

        return results
