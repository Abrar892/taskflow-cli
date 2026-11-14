"""summary.py — Daily summary reports and overdue task analytics for taskflow-cli."""

from __future__ import annotations
import datetime
from typing import List, Dict, Any, Optional
from taskflow.models import Task
from taskflow.database import TaskflowDB


class TaskAnalytics:
    """Provides analytical reports over tasks and projects."""

    def __init__(self, db: TaskflowDB):
        self.db = db

    def get_overdue_tasks(self, reference_date: Optional[str] = None) -> List[Task]:
        """
        Return all tasks that are not done/cancelled and have due_date < reference_date.
        reference_date format: YYYY-MM-DD. Defaults to today.
        """
        if reference_date is None:
            reference_date = datetime.date.today().isoformat()

        all_tasks = self.db.list_tasks()
        overdue = []
        for t in all_tasks:
            if t.status in ("done", "cancelled"):
                continue
            if t.due_date and t.due_date < reference_date:
                overdue.append(t)
        return overdue

    def get_daily_summary(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate daily summary for a given date (YYYY-MM-DD).
        Includes tasks completed, tasks due, overdue tasks, and status counts.
        """
        if target_date is None:
            target_date = datetime.date.today().isoformat()

        all_tasks = self.db.list_tasks()
        overdue = self.get_overdue_tasks(reference_date=target_date)

        completed_today = []
        due_today = []
        by_status = {"todo": 0, "in_progress": 0, "done": 0, "cancelled": 0}
        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for t in all_tasks:
            st = t.status if t.status in by_status else "todo"
            by_status[st] += 1
            
            pri = t.priority if t.priority in by_priority else "medium"
            by_priority[pri] += 1

            if t.due_date == target_date:
                due_today.append(t)

            if t.completed_at:
                c_date = datetime.datetime.fromtimestamp(t.completed_at).strftime("%Y-%m-%d")
                if c_date == target_date:
                    completed_today.append(t)

        return {
            "date": target_date,
            "total_tasks": len(all_tasks),
            "status_breakdown": by_status,
            "priority_breakdown": by_priority,
            "due_today_count": len(due_today),
            "due_today": due_today,
            "overdue_count": len(overdue),
            "overdue_tasks": overdue,
            "completed_today_count": len(completed_today),
            "completed_today": completed_today,
        }

    def render_summary_text(self, target_date: Optional[str] = None) -> str:
        """Render a formatted plain-text daily summary report."""
        summary = self.get_daily_summary(target_date)
        lines = [
            "=" * 60,
            f" TASKFLOW DAILY SUMMARY: {summary['date']}",
            "=" * 60,
            f"Total Tasks: {summary['total_tasks']}",
            f"Completed Today: {summary['completed_today_count']}",
            f"Due Today:       {summary['due_today_count']}",
            f"Overdue Tasks:   {summary['overdue_count']}",
            "-" * 60,
            "Status Breakdown:",
        ]
        for st, count in summary["status_breakdown"].items():
            lines.append(f"  {st.upper():<12} : {count}")

        lines.append("-" * 60)
        lines.append("Overdue Tasks List:")
        if not summary["overdue_tasks"]:
            lines.append("  (None - all clear!)")
        else:
            for ot in summary["overdue_tasks"]:
                lines.append(f"  [#{ot.id}] {ot.title} (Due: {ot.due_date}, Priority: {ot.priority})")

        lines.append("=" * 60)
        return "\n".join(lines)
