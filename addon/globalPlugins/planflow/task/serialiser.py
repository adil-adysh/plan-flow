from datetime import datetime, timedelta
from typing import Any
from .model import ScheduledTask


"""
Serialization and deserialization utilities for ScheduledTask.
Handles interval formatting/parsing and dict conversion.
"""

from datetime import datetime, timedelta
import re
from typing import Any
from .model import ScheduledTask

def format_interval(delta: timedelta) -> str:
    """
    Format a timedelta as a compact string (e.g., '2d', '3h', '15m', '10s').
    """
    total_sec = int(delta.total_seconds())
    if total_sec % 86400 == 0:
        return f"{total_sec // 86400}d"
    if total_sec % 3600 == 0:
        return f"{total_sec // 3600}h"
    if total_sec % 60 == 0:
        return f"{total_sec // 60}m"
    return f"{total_sec}s"

def parse_interval(text: str) -> timedelta:
    """
    Parse a compact interval string (e.g., '2d', '3h', '15m', '10s') into a timedelta.
    Raises ValueError if the format is invalid.
    """
    m = re.match(r"^(\d+)([smhd])$", text)
    if not m:
        raise ValueError(f"Invalid interval format: {text}")
    value, unit = int(m[1]), m[2]
    return {
        "s": timedelta(seconds=value),
        "m": timedelta(minutes=value),
        "h": timedelta(hours=value),
        "d": timedelta(days=value),
    }[unit]

def to_dict(task: ScheduledTask) -> dict[str, Any]:
    """
    Convert a ScheduledTask to a serializable dict.
    """
    return {
        "id": task.id,
        "label": task.label,
        "time": task.time.isoformat(),
        "description": task.description,
        "link": task.link,
        "recurrence": format_interval(task.recurrence) if task.recurrence else None,
    }

def from_dict(data: dict[str, Any]) -> ScheduledTask:
    """
    Create a ScheduledTask from a dict (as produced by to_dict).
    """
    return ScheduledTask(
        id=data["id"],
        label=data["label"],
        time=datetime.fromisoformat(data["time"]),
        description=data.get("description"),
        link=data.get("link"),
        recurrence=parse_interval(data["recurrence"]) if data.get("recurrence") else None,
    )
