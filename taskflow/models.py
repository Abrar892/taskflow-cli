"""
Data models for taskflow-cli.
Defines Project, Task, and TimeEntry dataclasses.
"""

from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class Project:
    """Represents a project container for tasks."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)
    status: str = "active"  # active, archived


@dataclass
class Task:
    """Represents a task (or subtask) within a project."""
    id: Optional[int] = None
    project_id: Optional[int] = None
    parent_task_id: Optional[int] = None   # for subtasks
    title: str = ""
    description: str = ""
    status: str = "todo"      # todo, in_progress, done, cancelled
    priority: str = "medium"  # critical, high, medium, low
    due_date: Optional[str] = None  # ISO 8601 date string YYYY-MM-DD
    tags: str = ""             # comma-separated tags
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class TimeEntry:
    """Represents a time-tracking entry for a task."""
    id: Optional[int] = None
    task_id: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    note: str = ""

    @property
    def duration_seconds(self) -> float:
        """Return duration in seconds; uses current time if still running."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
