"""Kanban board terminal renderer for taskflow."""
from typing import List
from taskflow.models import Task


class KanbanBoard:
    """Renders a 3-column Kanban board in terminal ASCII."""

    def __init__(self, tasks: List[Task], col_width: int = 24):
        self.tasks = tasks
        self.col_width = col_width

    def render(self) -> str:
        todo = [t for t in self.tasks if t.status == "todo"]
        in_progress = [t for t in self.tasks if t.status == "in_progress"]
        done = [t for t in self.tasks if t.status == "done"]

        max_rows = max(len(todo), len(in_progress), len(done), 1)

        border = "+" + ("-" * (self.col_width + 2) + "+") * 3
        header = f"| {'TODO':^{self.col_width}} | {'IN PROGRESS':^{self.col_width}} | {'DONE':^{self.col_width}} |"

        lines = [border, header, border]

        for i in range(max_rows):
            col_todo = self._format_cell(todo[i] if i < len(todo) else None)
            col_inp = self._format_cell(in_progress[i] if i < len(in_progress) else None)
            col_done = self._format_cell(done[i] if i < len(done) else None)
            lines.append(f"| {col_todo} | {col_inp} | {col_done} |")

        lines.append(border)
        return "\n".join(lines)

    def _format_cell(self, task: Task | None) -> str:
        if task is None:
            return " " * self.col_width
        prio_icon = "!" if task.priority == "critical" else ("^" if task.priority == "high" else " ")
        text = f"[{prio_icon}] {task.title}"
        if len(text) > self.col_width:
            text = text[: self.col_width - 3] + "..."
        return f"{text:<{self.col_width}}"
