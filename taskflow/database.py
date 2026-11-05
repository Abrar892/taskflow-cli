"""
SQLite database layer for taskflow-cli.
Implements TaskflowDB with full CRUD for projects, tasks, and time entries.
"""

import sqlite3
from typing import Optional, List
import time

from .models import Project, Task, TimeEntry


class TaskflowDB:
    """SQLite-backed persistence layer for taskflow data."""

    def __init__(self, db_path: str = "taskflow.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        """Create all required tables if they do not exist."""
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at  REAL NOT NULL,
                status      TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id     INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                title          TEXT NOT NULL,
                description    TEXT NOT NULL DEFAULT '',
                status         TEXT NOT NULL DEFAULT 'todo',
                priority       TEXT NOT NULL DEFAULT 'medium',
                due_date       TEXT,
                tags           TEXT NOT NULL DEFAULT '',
                created_at     REAL NOT NULL,
                updated_at     REAL NOT NULL,
                completed_at   REAL
            );

            CREATE TABLE IF NOT EXISTS time_entries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id    INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                start_time REAL NOT NULL,
                end_time   REAL,
                note       TEXT NOT NULL DEFAULT ''
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Project CRUD
    # ------------------------------------------------------------------

    def create_project(self, project: Project) -> Project:
        """Insert a new project and return it with its assigned id."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description, created_at, status) VALUES (?, ?, ?, ?)",
            (project.name, project.description, project.created_at, project.status),
        )
        self.conn.commit()
        project.id = cursor.lastrowid
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """Return a Project by id, or None if not found."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            status=row["status"],
        )

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """List all projects, optionally filtered by status."""
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY created_at", (status,))
        else:
            cursor.execute("SELECT * FROM projects ORDER BY created_at")
        rows = cursor.fetchall()
        return [
            Project(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                created_at=r["created_at"],
                status=r["status"],
            )
            for r in rows
        ]

    def update_project(self, project_id: int, **kwargs) -> None:
        """Update arbitrary fields of a project."""
        if not kwargs:
            return
        allowed = {"name", "description", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [project_id]
        self.conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def delete_project(self, project_id: int) -> None:
        """Delete a project by id (cascades to tasks and time_entries)."""
        self.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    def create_task(self, task: Task) -> Task:
        """Insert a new task and return it with its assigned id."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks
                (project_id, parent_task_id, title, description, status, priority,
                 due_date, tags, created_at, updated_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.project_id,
                task.parent_task_id,
                task.title,
                task.description,
                task.status,
                task.priority,
                task.due_date,
                task.tags,
                task.created_at,
                task.updated_at,
                task.completed_at,
            ),
        )
        self.conn.commit()
        task.id = cursor.lastrowid
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """Return a Task by id, or None if not found."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def list_tasks(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        overdue_only: bool = False,
    ) -> List[Task]:
        """List tasks with optional filters."""
        import datetime
        clauses: List[str] = []
        params: List = []

        if project_id is not None:
            clauses.append("project_id = ?")
            params.append(project_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if priority is not None:
            clauses.append("priority = ?")
            params.append(priority)
        if tag is not None:
            clauses.append("(',' || tags || ',' LIKE ?)")
            params.append(f"%,{tag},%")
        if overdue_only:
            today = datetime.date.today().isoformat()
            clauses.append("due_date < ?")
            params.append(today)
            clauses.append("status NOT IN ('done', 'cancelled')")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM tasks {where} ORDER BY created_at", params)
        return [self._row_to_task(r) for r in cursor.fetchall()]

    def update_task(self, task_id: int, **kwargs) -> None:
        """Update arbitrary fields of a task; always bumps updated_at."""
        allowed = {
            "project_id", "parent_task_id", "title", "description",
            "status", "priority", "due_date", "tags", "completed_at", "updated_at",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        fields["updated_at"] = time.time()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [task_id]
        self.conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        """Delete a task by id (cascades to time_entries)."""
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Time Entry operations
    # ------------------------------------------------------------------

    def create_time_entry(self, entry: TimeEntry) -> TimeEntry:
        """Insert a new time entry and return it with its assigned id."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO time_entries (task_id, start_time, end_time, note) VALUES (?, ?, ?, ?)",
            (entry.task_id, entry.start_time, entry.end_time, entry.note),
        )
        self.conn.commit()
        entry.id = cursor.lastrowid
        return entry

    def get_active_timer(self, task_id: int) -> Optional[TimeEntry]:
        """Return the currently running (open) time entry for a task, or None."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM time_entries WHERE task_id = ? AND end_time IS NULL ORDER BY start_time DESC LIMIT 1",
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_time_entry(row)

    def stop_timer(self, task_id: int) -> Optional[TimeEntry]:
        """Stop the active timer for a task; return the closed entry or None."""
        entry = self.get_active_timer(task_id)
        if entry is None:
            return None
        end = time.time()
        self.conn.execute(
            "UPDATE time_entries SET end_time = ? WHERE id = ?",
            (end, entry.id),
        )
        self.conn.commit()
        entry.end_time = end
        return entry

    def list_time_entries(self, task_id: int) -> List[TimeEntry]:
        """List all time entries for a task."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM time_entries WHERE task_id = ? ORDER BY start_time",
            (task_id,),
        )
        return [self._row_to_time_entry(r) for r in cursor.fetchall()]

    def get_total_time(self, task_id: int) -> float:
        """Return total tracked seconds for a task (completed entries only)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT SUM(end_time - start_time) FROM time_entries WHERE task_id = ? AND end_time IS NOT NULL",
            (task_id,),
        )
        result = cursor.fetchone()[0]
        return result if result is not None else 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            project_id=row["project_id"],
            parent_task_id=row["parent_task_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            due_date=row["due_date"],
            tags=row["tags"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    @staticmethod
    def _row_to_time_entry(row: sqlite3.Row) -> TimeEntry:
        return TimeEntry(
            id=row["id"],
            task_id=row["task_id"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            note=row["note"],
        )

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
