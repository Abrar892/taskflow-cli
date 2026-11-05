"""
Business logic layer for taskflow-cli.
Provides higher-level operations built on top of TaskflowDB.
"""

import datetime
import time
from typing import Dict, List, Optional

from .database import TaskflowDB
from .models import Project, Task, TimeEntry


class TaskflowOperations:
    """High-level operations for managing projects, tasks, and time tracking."""

    def __init__(self, db: TaskflowDB):
        self.db = db

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def create_project(self, name: str, description: str = "") -> Project:
        """Create and persist a new project."""
        project = Project(name=name, description=description)
        return self.db.create_project(project)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_task(
        self,
        project_id: int,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        tags: str = "",
        parent_id: Optional[int] = None,
    ) -> Task:
        """Create and persist a new task (or subtask) within a project."""
        task = Task(
            project_id=project_id,
            parent_task_id=parent_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags,
        )
        return self.db.create_task(task)

    def complete_task(self, task_id: int) -> Task:
        """Mark a task as done and record completion timestamp."""
        now = time.time()
        self.db.update_task(task_id, status="done", completed_at=now)
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        return task

    def start_task(self, task_id: int) -> Task:
        """Mark a task as in_progress."""
        self.db.update_task(task_id, status="in_progress")
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        return task

    # ------------------------------------------------------------------
    # Time tracking
    # ------------------------------------------------------------------

    def start_timer(self, task_id: int, note: str = "") -> TimeEntry:
        """Start a timer for a task (stops any existing open timer first)."""
        # Stop any active timer first
        self.db.stop_timer(task_id)
        entry = TimeEntry(task_id=task_id, note=note)
        return self.db.create_time_entry(entry)

    def stop_timer(self, task_id: int) -> TimeEntry:
        """Stop the active timer for a task."""
        entry = self.db.stop_timer(task_id)
        if entry is None:
            raise ValueError(f"No active timer for task {task_id}")
        return entry

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_project_summary(self, project_id: int) -> Dict:
        """Return a summary dictionary for a project."""
        project = self.db.get_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        tasks = self.db.list_tasks(project_id=project_id)
        tasks_total = len(tasks)
        tasks_done = sum(1 for t in tasks if t.status == "done")
        tasks_in_progress = sum(1 for t in tasks if t.status == "in_progress")

        # Total tracked time across all tasks in the project
        total_seconds = sum(self.db.get_total_time(t.id) for t in tasks if t.id is not None)
        total_time_hours = round(total_seconds / 3600, 2)

        today = datetime.date.today().isoformat()
        overdue_count = sum(
            1
            for t in tasks
            if t.due_date and t.due_date < today and t.status not in ("done", "cancelled")
        )

        return {
            "project": project,
            "tasks_total": tasks_total,
            "tasks_done": tasks_done,
            "tasks_in_progress": tasks_in_progress,
            "total_time_hours": total_time_hours,
            "overdue_count": overdue_count,
        }

    def get_overdue_tasks(self) -> List[Task]:
        """Return all overdue tasks (due_date < today, status not done/cancelled)."""
        return self.db.list_tasks(overdue_only=True)

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks whose title or description contains the query string (case-insensitive)."""
        all_tasks = self.db.list_tasks()
        q = query.lower()
        return [
            t for t in all_tasks
            if q in t.title.lower() or q in t.description.lower()
        ]

    def get_today_summary(self) -> Dict:
        """Return a high-level summary for today."""
        today = datetime.date.today().isoformat()
        projects = self.db.list_projects(status="active")
        all_tasks = self.db.list_tasks()

        tasks_due_today = [
            t for t in all_tasks
            if t.due_date == today and t.status not in ("done", "cancelled")
        ]
        overdue = [
            t for t in all_tasks
            if t.due_date and t.due_date < today and t.status not in ("done", "cancelled")
        ]
        in_progress = [t for t in all_tasks if t.status == "in_progress"]

        return {
            "projects_active": len(projects),
            "tasks_due_today": tasks_due_today,
            "overdue": overdue,
            "in_progress": in_progress,
        }
