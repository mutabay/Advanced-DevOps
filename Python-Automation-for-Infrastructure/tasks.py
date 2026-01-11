from uuid import UUID, uuid4
from typing import Optional
import asyncio
import logging
import traceback
import os

from models import Task, TaskStatus
from store import TASKS
from worker import AsyncWorker

log = logging.getLogger(__name__)

USE_CELERY = os.environ.get("USE_CELERY", "0") == "1"
if USE_CELERY:
    try:
        from celery_tasks import demo_task
    except Exception:
        demo_task = None

# Single global worker for demo purposes
_worker: Optional[AsyncWorker] = None


def get_worker() -> AsyncWorker:
    """Return the global AsyncWorker instance. Do not start it here; startup_worker()
    will start workers under FastAPI lifespan to ensure they're created in the right
    event loop.
    """
    global _worker
    if _worker is None:
        _worker = AsyncWorker(num_workers=2)
    return _worker


async def _run_task(task_id: UUID) -> None:
    """Background task runner. Updates TASKS[task_id] status and result.

    Ensures failures are captured and the task is marked FAILED.
    """
    task = TASKS.get(task_id)
    if not task:
        log.warning("Task %s not found when starting run", task_id)
        return

    try:
        task.status = TaskStatus.RUNNING
        # Simulate work — replace with real remediation/action logic.
        await asyncio.sleep(0.1)
        task.result = "ok"
        task.status = TaskStatus.SUCCESS
    except Exception as exc:  # capture and mark failed
        tb = traceback.format_exc()
        log.exception("Error while running task %s: %s", task_id, exc)
        task.result = tb
        task.status = TaskStatus.FAILED


def create_task(task_id: UUID | None = None) -> Task:
    if task_id is None:
        task_id = uuid4()
    task = Task(id=task_id, status=TaskStatus.PENDING, result="")
    TASKS[task_id] = task

    if USE_CELERY and demo_task is not None:
        # delegate to celery task, store the celery task id as result placeholder
        async_result = demo_task.apply_async(args=[{"task_id": str(task_id)}])
        task.result = f"celery:{async_result.id}"
        task.status = TaskStatus.RUNNING
    else:
        # schedule background work
        worker = get_worker()
        worker.submit(_run_task, task_id)

    return task


def get_task(task_id: UUID) -> Task | None:
    return TASKS.get(task_id)


async def startup_worker():
    if not USE_CELERY:
        worker = get_worker()
        await worker.start()


async def shutdown_worker():
    global _worker
    if _worker:
        await _worker.stop()
        _worker = None
