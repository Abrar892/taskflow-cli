"""Tests for taskflow-cli dependencies and burndown modules."""

import unittest
import time
from taskflow.models import Task
from taskflow.dependencies import DependencyGraph
from taskflow.burndown import BurndownCalculator


class TestDependenciesAndBurndown(unittest.TestCase):
    def test_dependency_graph_normal(self):
        graph = DependencyGraph()
        graph.add_dependency(task_id=2, depends_on_id=1)
        graph.add_dependency(task_id=3, depends_on_id=2)

        self.assertEqual(graph.get_dependencies(2), {1})
        self.assertEqual(graph.get_dependencies(3), {2})
        self.assertEqual(graph.get_blocked_tasks(1), {2})

        # Task 2 is blocked if Task 1 is not completed
        self.assertTrue(graph.is_blocked(2, completed_task_ids=set()))
        # Task 2 is unblocked once Task 1 is completed
        self.assertFalse(graph.is_blocked(2, completed_task_ids={1}))
        # Task 3 is blocked if Task 1 is completed but Task 2 is not
        self.assertTrue(graph.is_blocked(3, completed_task_ids={1}))
        # Task 3 is unblocked once both are completed
        self.assertFalse(graph.is_blocked(3, completed_task_ids={1, 2}))

    def test_dependency_cycle_detection(self):
        graph = DependencyGraph()
        graph.add_dependency(task_id=2, depends_on_id=1)
        graph.add_dependency(task_id=3, depends_on_id=2)

        # Trying to make task 1 depend on task 3 creates a cycle: 1 -> 3 -> 2 -> 1
        with self.assertRaises(ValueError):
            graph.add_dependency(task_id=1, depends_on_id=3)

    def test_dependency_self_reference_raises(self):
        graph = DependencyGraph()
        with self.assertRaises(ValueError):
            graph.add_dependency(task_id=1, depends_on_id=1)

    def test_burndown_calculator(self):
        # Completed timestamp on 2026-11-04 (epoch ~ 1793750400 or use explicit datetime timestamp)
        import datetime
        completed_ts = datetime.datetime(2026, 11, 4, 12, 0).timestamp()
        t1 = Task(id=1, title="Task 1", status="done", completed_at=completed_ts)
        t2 = Task(id=2, title="Task 2", status="done", completed_at=completed_ts)
        t3 = Task(id=3, title="Task 3", status="todo")
        t4 = Task(id=4, title="Task 4", status="todo")

        tasks = [t1, t2, t3, t4]
        calc = BurndownCalculator(tasks, start_date="2026-11-01", target_end_date="2026-11-10")
        stats = calc.calculate_daily_burndown(as_of_date="2026-11-05")

        self.assertEqual(stats["total_tasks"], 4)
        self.assertEqual(stats["completed_tasks"], 2)
        self.assertEqual(stats["remaining_tasks"], 2)
        self.assertIn("ideal_remaining", stats)
        self.assertIn("velocity_tasks_per_day", stats)
        self.assertIn("is_on_track", stats)


if __name__ == "__main__":
    unittest.main()
