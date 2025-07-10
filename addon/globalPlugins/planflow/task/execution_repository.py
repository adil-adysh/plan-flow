"""ExecutionRepository: TinyDB-backed storage for PlanFlow task data.

This module provides a pure, type-safe repository for persisting and retrieving
TaskDefinition, TaskOccurrence, and TaskExecution records. Supports pluggable storage
(file-based or in-memory) for testability and decoupling from logic layers.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import asdict, is_dataclass
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from tinydb.table import Table
from .task_model import TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy, TaskEvent
from datetime import datetime, timedelta
import typing as t
import copy
def _serialize_datetime(dt: datetime) -> str:
    return dt.isoformat()

def _deserialize_datetime(val: str) -> datetime:
    return datetime.fromisoformat(val)

def _serialize_timedelta(td: timedelta | None) -> float | None:
    return td.total_seconds() if td is not None else None

def _deserialize_timedelta(val: float | None) -> timedelta | None:
    return timedelta(seconds=val) if val is not None else None


def _serialize_retry_policy(rp: RetryPolicy) -> dict[str, t.Any]:
    return {
        "max_retries": rp.max_retries,
    }


def _deserialize_retry_policy(data: dict[str, t.Any]) -> RetryPolicy:
    return RetryPolicy(
        max_retries=data["max_retries"]
    )


def _serialize_task_definition(task: TaskDefinition) -> dict[str, t.Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "link": task.link,
        "created_at": _serialize_datetime(task.created_at),
        "recurrence": _serialize_timedelta(task.recurrence),
        "priority": task.priority,
        "preferred_slots": task.preferred_slots,
        "retry_policy": _serialize_retry_policy(task.retry_policy),
    }



def _deserialize_task_definition(data: dict[str, t.Any]) -> TaskDefinition:
    return TaskDefinition(
        id=data["id"],
        title=data["title"],
        description=data.get("description"),
        link=data.get("link"),
        created_at=_deserialize_datetime(data["created_at"]),
        recurrence=_deserialize_timedelta(data.get("recurrence")),
        priority=data.get("priority", "medium"),
        preferred_slots=data.get("preferred_slots", []),
        retry_policy=_deserialize_retry_policy(data["retry_policy"]),
    )


def _serialize_task_occurrence(occ: TaskOccurrence) -> dict[str, t.Any]:
    return {
        "id": occ.id,
        "task_id": occ.task_id,
        "scheduled_for": _serialize_datetime(occ.scheduled_for),
        "slot_name": occ.slot_name,
        "pinned_time": _serialize_datetime(occ.pinned_time) if occ.pinned_time is not None else None,
    }



def _deserialize_task_occurrence(data: dict[str, t.Any]) -> TaskOccurrence:
    return TaskOccurrence(
        id=data["id"],
        task_id=data["task_id"],
        scheduled_for=_deserialize_datetime(data["scheduled_for"]),
        slot_name=data.get("slot_name", None),
        pinned_time=_deserialize_datetime(data["pinned_time"]) if data.get("pinned_time") is not None else None,
    )

def _serialize_task_event(ev: TaskEvent) -> dict[str, t.Any]:
    return {
        "event": ev.event,
        "timestamp": _serialize_datetime(ev.timestamp),
    }

def _deserialize_task_event(data: dict[str, t.Any]) -> TaskEvent:
    return TaskEvent(
        event=data["event"],
        timestamp=_deserialize_datetime(data["timestamp"]),
    )

def _serialize_task_execution(exec: TaskExecution) -> dict[str, t.Any]:
    return {
        "occurrence_id": exec.occurrence_id,
        "state": exec.state,
        "retries_remaining": exec.retries_remaining,
        "history": [_serialize_task_event(ev) for ev in exec.history],
    }

def _deserialize_task_execution(data: dict[str, t.Any]) -> TaskExecution:
    return TaskExecution(
        occurrence_id=data["occurrence_id"],
        state=data["state"],
        retries_remaining=data["retries_remaining"],
        history=[_deserialize_task_event(ev) for ev in data.get("history", [])],
    )

class ExecutionRepository:
    """Manages persistent storage of tasks, occurrences, and executions using TinyDB.

    Provides atomic, type-safe CRUD operations for PlanFlow task entities.
    Supports both file-based and in-memory storage for testability.
    """

    def __init__(self, db: TinyDB | None = None) -> None:
        """Initialize the repository with a TinyDB instance.

        Args:
            db: Optional TinyDB instance. If None, uses in-memory storage.
        """
        self._db: TinyDB = db if db is not None else TinyDB(storage=MemoryStorage)
        self._tasks: Table = self._db.table("tasks")
        self._occurrences: Table = self._db.table("occurrences")
        self._executions: Table = self._db.table("executions")

    def add_task(self, task: TaskDefinition) -> None:
        """Store a new task definition.

        Args:
            task: The TaskDefinition to store.
        """
        self._tasks.upsert(_serialize_task_definition(task), lambda doc: doc.get("id") == task.id)

    def get_task(self, task_id: str) -> TaskDefinition | None:
        """Fetch a task by ID.

        Args:
            task_id: The ID of the task to fetch.

        Returns:
            The TaskDefinition if found, else None.
        """
        doc = self._tasks.get(lambda d: d.get("id") == task_id)
        if doc is not None:
            return _deserialize_task_definition(doc)
        return None

    def list_tasks(self) -> list[TaskDefinition]:
        """Return all task definitions.

        Returns:
            A list of all TaskDefinition records.
        """
        return [_deserialize_task_definition(d) for d in self._tasks.all()]

    def add_occurrence(self, occ: TaskOccurrence) -> None:
        """Store a task occurrence.

        Args:
            occ: The TaskOccurrence to store.
        """
        self._occurrences.upsert(_serialize_task_occurrence(occ), lambda doc: doc.get("id") == occ.id)

    def list_occurrences(self) -> list[TaskOccurrence]:
        """Return all known occurrences.

        Returns:
            A list of all TaskOccurrence records.
        """
        return [_deserialize_task_occurrence(d) for d in self._occurrences.all()]

    def add_execution(self, exec: TaskExecution) -> None:
        """Store a new task execution record.

        Args:
            exec: The TaskExecution to store.
        """
        self._executions.upsert(_serialize_task_execution(exec), lambda doc: doc.get("occurrence_id") == exec.occurrence_id)

    def list_executions(self) -> list[TaskExecution]:
        """Return all executions.

        Returns:
            A list of all TaskExecution records.
        """
        return [_deserialize_task_execution(d) for d in self._executions.all()]
