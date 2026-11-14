"""Tests for taskflow summary, analytics, and filter engine."""

import unittest
import tempfile
import os
import time
from taskflow.database import TaskflowDB
from taskflow.models import Task, Project
from taskflow.summary import TaskAnalytics
from taskflow.filter_engine import TaskFilter


class TestSummaryAndFilter(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "taskflow_test.db")
        self.db = TaskflowDB(self.db_path)
        self.proj = Project(name="Test Proj")
        self.created_proj = self.db.create_project(self.proj)
        self.proj_id = self.created_proj.id

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    def test_overdue_and_daily_summary(self):
        t1 = Task(project_id=self.proj_id, title="Overdue Task", status="todo", due_date="2026-11-01", priority="high")
        t2 = Task(project_id=self.proj_id, title="Today Task", status="in_progress", due_date="2026-11-14", priority="critical")
        t3 = Task(project_id=self.proj_id, title="Done Task", status="done", due_date="2026-11-01", completed_at=time.time())
        self.db.create_task(t1)
        self.db.create_task(t2)
        self.db.create_task(t3)

        analytics = TaskAnalytics(self.db)
        overdue = analytics.get_overdue_tasks(reference_date="2026-11-14")
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].title, "Overdue Task")

        summary = analytics.get_daily_summary(target_date="2026-11-14")
        self.assertEqual(summary["total_tasks"], 3)
        self.assertEqual(summary["overdue_count"], 1)
        self.assertEqual(summary["due_today_count"], 1)
        self.assertEqual(summary["status_breakdown"]["done"], 1)
        
        report_text = analytics.render_summary_text("2026-11-14")
        self.assertIn("Overdue Task", report_text)
        self.assertIn("TASKFLOW DAILY SUMMARY", report_text)

    def test_task_filter_engine(self):
        t1 = Task(project_id=self.proj_id, title="Bugfix auth", description="Fix login token", status="todo", priority="high", tags="auth,sec")
        t2 = Task(project_id=self.proj_id, title="Add feature", description="Payment gateway", status="done", priority="medium", tags="billing")
        self.db.create_task(t1)
        self.db.create_task(t2)

        tf = TaskFilter(self.db)
        res_tag = tf.query(tag="sec")
        self.assertEqual(len(res_tag), 1)
        self.assertEqual(res_tag[0].title, "Bugfix auth")

        res_search = tf.query(search_query="payment")
        self.assertEqual(len(res_search), 1)
        self.assertEqual(res_search[0].title, "Add feature")

        res_none = tf.query(priority="critical")
        self.assertEqual(len(res_none), 0)


if __name__ == "__main__":
    unittest.main()
