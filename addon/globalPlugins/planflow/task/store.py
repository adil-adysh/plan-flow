"""
Persistence layer for ScheduledTask using TinyDB.
Provides add, update, remove, list, and clear operations.
"""

from typing import Any
from datetime import datetime
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage, Storage
from .serialiser import to_dict, from_dict
from .model import ScheduledTask

class TaskStore:
	"""
	TaskStore manages persistence of ScheduledTask objects using TinyDB.
	All tasks are loaded into memory for fast access.
	"""
	def __init__(self, file_path: str = "tasks.json", storage: type[Storage] = JSONStorage):
		"""Initialize the store and load all tasks from disk. Accepts custom storage for testing."""
		if storage is JSONStorage:
			self.db = TinyDB(file_path, storage=storage)
		else:
			self.db = TinyDB(storage=storage)
		self.query = Query()
		self.tasks: list[ScheduledTask] = []
		self.load()

	def load(self) -> None:
		"""Load all tasks from the database into memory."""
		self.tasks = []
		for doc in self.db.all():
			task = from_dict(doc)
			self.tasks.append(task)

	def save(self) -> None:
		"""Overwrite the database with the current in-memory tasks."""
		self.db.truncate()
		for task in self.tasks:
			self.db.insert(to_dict(task))

	def add(self, task: ScheduledTask) -> None:
		"""Add a new task to the store and persist it."""
		self.tasks.append(task)
		self.db.insert(to_dict(task))

	def update(self, task: ScheduledTask) -> None:
		"""Update an existing task by id."""
		found = self.db.search(self.query.id == task.id)
		if not found:
			raise ValueError(f"No task with id {task.id}")
		self.db.update(to_dict(task), self.query.id == task.id)
		for i, t in enumerate(self.tasks):
			if t.id == task.id:
				self.tasks[i] = task
				break

	def remove(self, task_id: str) -> None:
		"""Remove a task by id from the store and memory."""
		self.db.remove(self.query.id == task_id)
		self.tasks = [t for t in self.tasks if t.id != task_id]

	def list_due(self) -> list[ScheduledTask]:
		"""Return a list of tasks that are due now or earlier."""
		now = datetime.now()
		return [t for t in self.tasks if t.is_due(now)]

	def clear(self) -> None:
		"""Remove all tasks from the store and memory."""
		self.db.truncate()
		self.tasks = []

	def close(self) -> None:
		"""Close the TinyDB database explicitly."""
		self.db.close()

	def __del__(self) -> None:
		"""Destructor: closes the database (not always reliable). Prefer close()."""
		self.close()
