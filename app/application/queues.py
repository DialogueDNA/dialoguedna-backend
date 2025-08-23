from __future__ import annotations
from typing import Protocol, Any, Callable
from fastapi import BackgroundTasks

class TaskQueue(Protocol):
    def enqueue(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None: ...

class BackgroundTasksQueue(TaskQueue):
    """Adapter so we can pass FastAPI BackgroundTasks where a TaskQueue is expected."""
    def __init__(self, bg: BackgroundTasks):
        self._bg = bg
    def enqueue(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self._bg.add_task(fn, *args, **kwargs)
