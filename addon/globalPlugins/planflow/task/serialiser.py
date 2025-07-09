from datetime import datetime, timedelta
from typing import Any
from .model import ScheduledTask

def format_interval(delta: timedelta) -> str:
    total_sec = int(delta.total_seconds())
    if total_sec % 86400 == 0: return f"{total_sec // 86400}d"
    if total_sec % 3600 == 0: return f"{total_sec // 3600}h"
    if total_sec % 60 == 0: return f"{total_sec // 60}m"
    return f"{total_sec}s"

def parse_interval(text: str) -> timedelta:
    import re
    m = re.match(r"^(\\d+)([smhd])$", text)
    if not m: raise ValueError(f"Invalid interval format: {text}")
    value, unit = int(m[1]), m[2]
    return {"s": timedelta(seconds=value),
            "m": timedelta(minutes=value),
            "h": timedelta(hours=value),
            "d": timedelta(days=value)}[unit]

def to_dict(task: ScheduledTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "label": task.label,
        "time": task.time.isoformat(),
        "description": task.description,
        "link": task.link,
        "recurrence": format_interval(task.recurrence) if task.recurrence else None
    }

def from_dict(data: dict[str, Any]) -> ScheduledTask:
    return ScheduledTask(
        id=data["id"],
        label=data["label"],
        time=datetime.fromisoformat(data["time"]),
        description=data.get("description"),
        link=data.get("link"),
        recurrence=parse_interval(data["recurrence"]) if data.get("recurrence") else None,
    )
