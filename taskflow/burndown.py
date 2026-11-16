"""burndown.py — Sprint burndown and completion velocity metrics for taskflow-cli."""

from __future__ import annotations
import datetime
from typing import Dict, List, Any
from taskflow.models import Task


class BurndownCalculator:
    """Computes daily burndown velocity and projected completion timelines."""

    def __init__(self, tasks: List[Task], start_date: str, target_end_date: str):
        self.tasks = tasks
        self.start_date = start_date
        self.target_end_date = target_end_date

    def calculate_daily_burndown(self, as_of_date: str) -> Dict[str, Any]:
        """
        Calculate remaining task count vs ideal burndown trajectory.
        """
        total_tasks = len(self.tasks)
        s_date = datetime.date.fromisoformat(self.start_date)
        e_date = datetime.date.fromisoformat(self.target_end_date)
        curr_date = datetime.date.fromisoformat(as_of_date)

        total_days = max(1, (e_date - s_date).days)
        elapsed_days = max(0, min(total_days, (curr_date - s_date).days))

        # Completed tasks before or on as_of_date
        completed_count = 0
        for t in self.tasks:
            if t.status == "done" and t.completed_at:
                c_date = datetime.datetime.fromtimestamp(t.completed_at).date()
                if c_date <= curr_date:
                    completed_count += 1

        remaining = total_tasks - completed_count
        ideal_remaining = max(0.0, total_tasks - (total_tasks / total_days) * elapsed_days)

        velocity_per_day = (completed_count / elapsed_days) if elapsed_days > 0 else 0.0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "remaining_tasks": remaining,
            "ideal_remaining": round(ideal_remaining, 1),
            "elapsed_days": elapsed_days,
            "total_days": total_days,
            "velocity_tasks_per_day": round(velocity_per_day, 2),
            "is_on_track": remaining <= ideal_remaining,
        }
