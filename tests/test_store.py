"""
Unit tests for store.py in PlanFlow add-on.
"""
from addon.globalPlugins.planflow.task.store import TaskStore
from addon.globalPlugins.planflow.task.model import ScheduledTask
from datetime import datetime
import tempfile
import os

def make_task(task_id: str) -> ScheduledTask:
    return ScheduledTask(
        id=task_id,
        label=f"Task {task_id}",
        time=datetime(2025, 7, 9, 12, 0, 0),
        description=None,
        link=None,
        recurrence=None,
        callback=None,
    )

def test_add_and_list_tasks():
    """Test adding and listing tasks in TaskStore."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        store = TaskStore(tf.name)
        task = make_task("1")
        store.add(task)
        assert any(t.id == "1" for t in store.tasks)
        store.clear()
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)

def test_update_task():
    """Test updating a task in TaskStore."""
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
        assert any(t.label == "Updated Label" for t in store.tasks)
        store.clear()
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)

def test_remove_and_clear_tasks():
    """Test removing and clearing tasks in TaskStore."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        store = TaskStore(tf.name)
        t1 = make_task("3")
        t2 = make_task("4")
        store.add(t1)
        store.add(t2)
        store.remove("3")
        assert all(t.id != "3" for t in store.tasks)
        store.clear()
        assert store.tasks == []
        store.close()  # Ensure TinyDB file handle is closed before removal
        tf.close()
        os.remove(tf.name)
