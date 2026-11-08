# Taskflow CLI

Feature-rich task and project management CLI with SQLite persistence.

## Features
- **Project & Task CRUD:** Organize tasks by projects with priorities, due dates, tags, and subtasks.
- **Terminal Kanban Board:** Visual ASCII/Unicode column display of TODO, IN PROGRESS, and DONE tasks.
- **Time Tracking:** Start, stop, and audit durations directly on tasks.
- **Exporters:** Export reports in CSV, JSON, and Markdown format.
- **Zero External Dependencies:** Built entirely with Python 3.12 standard library.

## Quickstart
```bash
python -m taskflow.cli project create "Platform Engine"
python -m taskflow.cli task add --project 1 "Setup database schema" --priority high
python -m taskflow.cli board --project 1
```
