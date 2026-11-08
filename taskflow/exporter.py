"""Taskflow exporters for CSV, JSON, and Markdown formats."""
import csv
import json
from typing import List
from taskflow.models import Task


class Exporter:
    @staticmethod
    def export_csv(tasks: List[Task], filepath: str):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "project_id", "title", "status", "priority", "due_date", "tags"])
            for t in tasks:
                writer.writerow([t.id, t.project_id, t.title, t.status, t.priority, t.due_date, t.tags])

    @staticmethod
    def export_json(tasks: List[Task], filepath: str):
        data = [
            {
                "id": t.id,
                "project_id": t.project_id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date,
                "tags": t.tags,
            }
            for t in tasks
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def export_markdown(tasks: List[Task], project_name: str, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Tasks for Project: {project_name}\n\n")
            for t in tasks:
                mark = "x" if t.status == "done" else " "
                f.write(f"- [{mark}] **{t.title}** (Priority: {t.priority}, Due: {t.due_date or 'None'})\n")
