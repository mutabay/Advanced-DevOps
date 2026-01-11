from fastapi import FastAPI, HTTPException, Body
from uuid import UUID
from contextlib import asynccontextmanager

from tasks import create_task, get_task, startup_worker, shutdown_worker, get_worker
from models import TaskStatus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await startup_worker()
    try:
        yield
    finally:
        # shutdown
        await shutdown_worker()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Automation API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tasks/run")
async def run_task():
    task = create_task()
    return {"message": "Task submitted", "id": str(task.id)}


@app.get("/tasks/queue")
async def tasks_queue():
    worker = get_worker()
    return {"queue_size": worker.queue_size(), "num_workers": worker.num_workers_active()}


@app.get("/tasks/{task_id}")
async def read_task(task_id: UUID):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": str(task.id), "status": task.status.value, "result": task.result}


@app.post("/tasks/{task_id}/complete")
async def task_complete(task_id: UUID, payload: dict = Body(...)):
    """Callback endpoint Celery tasks can POST to with JSON {"status": "SUCCESS"|"FAILED", "result": ...}
    Updates the in-memory TASKS entry for the given UUID.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    status = payload.get("status")
    result = payload.get("result", "")
    try:
        if status:
            task.status = TaskStatus(status)
    except Exception:
        task.status = TaskStatus.FAILED
    task.result = result
    return {"updated": True}
