"""Full test suite for taskflow-cli."""
import unittest
import os
import tempfile
from taskflow.database import TaskflowDB
from taskflow.operations import TaskflowOperations
from taskflow.models import Project, Task
from taskflow.board import KanbanBoard
from taskflow.exporter import Exporter


class TestDatabaseAndOperations(unittest.TestCase):
    def setUp(self):
        self.db = TaskflowDB(":memory:")
        self.ops = TaskflowOperations(self.db)

    def tearDown(self):
        self.db.close()

    def test_project_and_task_lifecycle(self):
        proj = self.ops.create_project("Backend API", "Core services")
        self.assertIsNotNone(proj.id)

        task = self.ops.add_task(proj.id, "Setup auth", priority="high")
        self.assertEqual(task.status, "todo")

        started = self.ops.start_task(task.id)
        self.assertEqual(started.status, "in_progress")

        completed = self.ops.complete_task(task.id)
        self.assertEqual(completed.status, "done")
        self.assertIsNotNone(completed.completed_at)

    def test_kanban_rendering(self):
        tasks = [
            Task(id=1, title="Task 1", status="todo", priority="medium"),
            Task(id=2, title="Task 2", status="in_progress", priority="high"),
            Task(id=3, title="Task 3", status="done", priority="low"),
        ]
        board = KanbanBoard(tasks)
        rendered = board.render()
        self.assertIn("TODO", rendered)
        self.assertIn("IN PROGRESS", rendered)
        self.assertIn("DONE", rendered)
        self.assertIn("Task 1", rendered)
        self.assertIn("Task 2", rendered)

    def test_export(self):
        tasks = [Task(id=1, title="Sample Task", status="todo", priority="low")]
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "tasks.csv")
            Exporter.export_csv(tasks, csv_path)
            self.assertTrue(os.path.exists(csv_path))

            json_path = os.path.join(tmpdir, "tasks.json")
            Exporter.export_json(tasks, json_path)
            self.assertTrue(os.path.exists(json_path))

            md_path = os.path.join(tmpdir, "tasks.md")
            Exporter.export_markdown(tasks, "TestProj", md_path)
            self.assertTrue(os.path.exists(md_path))


if __name__ == "__main__":
    unittest.main()
