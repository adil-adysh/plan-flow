"""
Unit tests for store.py in PlanFlow add-on.
"""
from addon.globalPlugins.planflow.task.store import TaskStore
from addon.globalPlugins.planflow.task.model import ScheduledTask
from datetime import datetime
import tempfile
import os


def make_task(task_id: str) -> ScheduledTask:
    """
    Helper to create a ScheduledTask for store tests.
    """
    return ScheduledTask(
        id=task_id,
        label=f"Task {task_id}",
        time=datetime(2025, 7, 9, 12, 0, 0),
        description=None,
        link=None,
        recurrence=None,
        callback=None,
    )


def test_add_and_list_tasks() -> None:
    """
    Test adding a task to TaskStore and listing it.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        store = TaskStore(tf.name)
        task = make_task("1")
        store.add(task)
        # Check that the task is present in the store
        assert any(t.id == "1" for t in store.tasks)
        store.clear()
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)  # Explicit cleanup


def test_update_task() -> None:
    """
    Test updating a task in TaskStore and verifying the update.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        store = TaskStore(tf.name)
        task = make_task("2")
        store.add(task)
        task2 = ScheduledTask(
            id=task.id,
            label="Updated Label",
            time=task.time,
            description=task.description,
            link=task.link,
            recurrence=task.recurrence,
            callback=task.callback,
        )
        store.update(task2)
        # Check that the updated label is present
        assert any(t.label == "Updated Label" for t in store.tasks)
        store.clear()
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)  # Explicit cleanup


def test_remove_and_clear_tasks() -> None:
    """
    Test removing a task and clearing all tasks in TaskStore.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        store = TaskStore(tf.name)
        t1 = make_task("3")
        t2 = make_task("4")
        store.add(t1)
        store.add(t2)
        store.remove("3")
        # Check that the removed task is no longer present
        assert all(t.id != "3" for t in store.tasks)
        store.clear()
        # Check that the store is empty after clear
        assert store.tasks == []
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)  # Explicit cleanup
