"""CLI entry point for taskflow-cli."""
import argparse
from taskflow.database import TaskflowDB
from taskflow.operations import TaskflowOperations
from taskflow.board import KanbanBoard
from taskflow.exporter import Exporter


def main():
    parser = argparse.ArgumentParser(description="Taskflow CLI - Terminal Project & Task Manager")
    parser.add_argument("--db", default="taskflow.db", help="Path to SQLite DB file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Project commands
    proj_p = subparsers.add_parser("project")
    proj_sub = proj_p.add_subparsers(dest="proj_command", required=True)
    p_create = proj_sub.add_parser("create")
    p_create.add_argument("name")
    p_create.add_argument("--description", default="")
    proj_sub.add_parser("list")

    # Task commands
    task_p = subparsers.add_parser("task")
    task_sub = task_p.add_subparsers(dest="task_command", required=True)
    t_add = task_sub.add_parser("add")
    t_add.add_argument("--project", type=int, required=True)
    t_add.add_argument("title")
    t_add.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
    t_add.add_argument("--due", default=None)
    t_add.add_argument("--tags", default="")

    t_list = task_sub.add_parser("list")
    t_list.add_argument("--project", type=int)

    t_done = task_sub.add_parser("done")
    t_done.add_argument("task_id", type=int)

    # Board command
    board_p = subparsers.add_parser("board")
    board_p.add_argument("--project", type=int, required=True)

    # Export command
    export_p = subparsers.add_parser("export")
    export_p.add_argument("--project", type=int, required=True)
    export_p.add_argument("--format", choices=["csv", "json", "md"], default="md")
    export_p.add_argument("--output", required=True)

    args = parser.parse_args()
    db = TaskflowDB(args.db)
    ops = TaskflowOperations(db)

    try:
        if args.command == "project":
            if args.proj_command == "create":
                p = ops.create_project(args.name, args.description)
                print(f"Created project [{p.id}] {p.name}")
            elif args.proj_command == "list":
                projects = db.list_projects()
                for p in projects:
                    print(f"[{p.id}] {p.name} - {p.description}")

        elif args.command == "task":
            if args.task_command == "add":
                t = ops.add_task(args.project, args.title, priority=args.priority, due_date=args.due, tags=args.tags)
                print(f"Created task [{t.id}] {t.title}")
            elif args.task_command == "list":
                tasks = db.list_tasks(project_id=args.project)
                for t in tasks:
                    print(f"[{t.id}] [{t.status.upper()}] {t.title} ({t.priority})")
            elif args.task_command == "done":
                t = ops.complete_task(args.task_id)
                print(f"Task [{t.id}] marked as done.")

        elif args.command == "board":
            tasks = db.list_tasks(project_id=args.project)
            board = KanbanBoard(tasks)
            print(board.render())

        elif args.command == "export":
            tasks = db.list_tasks(project_id=args.project)
            proj = db.get_project(args.project)
            proj_name = proj.name if proj else "Unknown"
            if args.format == "csv":
                Exporter.export_csv(tasks, args.output)
            elif args.format == "json":
                Exporter.export_json(tasks, args.output)
            elif args.format == "md":
                Exporter.export_markdown(tasks, proj_name, args.output)
            print(f"Exported {len(tasks)} tasks to {args.output}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
