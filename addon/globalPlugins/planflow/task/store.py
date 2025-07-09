from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from .serialiser import to_dict, from_dict
from .model import ScheduledTask
from typing import Any

class TaskStore:
    def __init__(self, file_path: str = "tasks.json"):
        self.db = TinyDB(file_path, storage=JSONStorage)
        self.query = Query()
        self.tasks: list[ScheduledTask] = []
        self.load()

    def load(self) -> None:
        self.tasks = []
        for doc in self.db.all():
            task = from_dict(doc)
            self.tasks.append(task)

    def save(self) -> None:
        self.db.truncate()
        for task in self.tasks:
            self.db.insert(to_dict(task))

    def add(self, task: ScheduledTask) -> None:
        self.tasks.append(task)
        self.db.insert(to_dict(task))

    def update(self, task: ScheduledTask) -> None:
        found = self.db.search(self.query.id == task.id)
        if not found:
            raise ValueError(f"No task with id {task.id}")
        self.db.update(to_dict(task), self.query.id == task.id)
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break

    def remove(self, task_id: str) -> None:
        self.db.remove(self.query.id == task_id)
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def list_due(self) -> list[ScheduledTask]:
        from datetime import datetime
        now = datetime.now()
        return [t for t in self.tasks if t.is_due(now)]

    def clear(self) -> None:
        self.db.truncate()
        self.tasks = []

    def __del__(self) -> None:
        self.db.close()
