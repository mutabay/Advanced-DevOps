# Theory: Background & Design Principles

This section gives a short, practical theory primer for the automation backend implemented in this module. It explains the key concepts and trade-offs you should consider when designing and operating automation systems for infrastructure.

Asynchronous I/O and concurrency
- Async I/O (asyncio in Python) lets a single process manage many concurrent tasks efficiently when those tasks are I/O-bound (network calls, disk, etc.). It is lightweight and suitable for high-concurrency, low-CPU workloads.
- For CPU-bound work, process-based concurrency (multiprocessing, separate worker processes) or delegating work to dedicated workers is necessary.

Task queues and brokers
- A task queue decouples request submission from execution. Clients enqueue work and workers consume tasks asynchronously.
- A broker (e.g., Redis, RabbitMQ) persists messages and distributes them to workers. Brokers provide durability, routing, and scalable throughput.
- In-process queues (asyncio.Queue) are useful for local development and simple cases but are volatile and do not survive process restarts.

Workers and execution models
- In-process worker: simple, fast iterations; great for development and lightweight automations. Limited by single-process lifetime and cannot scale across hosts.
- Distributed workers (Celery/Dramatiq): run in separate processes or hosts, scale horizontally, and provide features like retries, scheduling, and result backends.

Durability and state management
- Task metadata (status, result) should be persisted when the system must survive restarts or support multiple web processes. Use a database (Postgres, SQLite) or a durable result backend.
- The common pattern is: web API writes a task record to DB, enqueues a message, worker processes the message and updates the DB record on completion. This avoids losing state and keeps web and workers consistent.

Idempotency, retries, and failure handling
- Tasks must be idempotent (or guarded) because they can be retried or delivered more than once.
- Use explicit retry policies, exponential backoff, and circuit-breakers for downstream calls.
- Track failure metadata and expose it in task results for troubleshooting.

Acknowledgements and message semantics
- Configure message acknowledgement semantics carefully. A worker should acknowledge a task only after successful processing to avoid message loss.
- Beware of "poison pill" messages (tasks that always fail); implement dead-letter queues or move failing tasks to a separate queue for manual inspection.

Observability and monitoring
- Emit metrics (queue depth, task durations, failure rates) and logs from both web and worker components.
- Use tools like Flower (Celery), Prometheus, and a centralized log system for operational visibility.

Security and hardening
- Secure any callback endpoints (webhooks) used by workers (shared secret headers, short-lived tokens, mTLS, or IP restrictions).
- Validate and sanitize inputs, avoid executing arbitrary shell commands directly, and run remediation actions with limited privileges.

Design patterns and integration notes
- Transactional outbox: persist a DB record and an outgoing message in a single transaction; a separate process reliably publishes the message to the broker to avoid loss between DB write and enqueue.
- Request -> Enqueue -> Execute -> Report-back is a robust pattern. Report-back can be push (worker POSTs to API) or pull (web polls result backend/DB).

Trade-offs summary
- In-process: simple, fast for dev, not durable or scalable.
- Broker + workers (Celery/Dramatiq): production-grade, durable, scalable, more operational complexity.

---

# Python Automation for Infrastructure

A small training, FastAPI module for automating infrastructure tasks.
This repository demonstrates an automation backend pattern: accept task requests, enqueue execution, run work asynchronously, and report results back to the API.

Table of contents
- About
- Features
- Architecture (how it works)
- Quick start (dev)
- Celery (optional production-like setup)
- Callback / result sync (what we added)
- Environment variables
- Endpoints
- Testing
- Production recommendations
- Contributing & License


This module consists of the building blocks of an automation backend used for infrastructure remediation, task runners, and health agents.

Features
- FastAPI web API with lightweight endpoints to submit and query tasks.
- In-process asyncio worker for local development and fast feedback loops.
- Optional Celery integration for distributed execution (Redis broker).
- Celery-to-API callback implemented (quick approach) so task results are pushed back to the web API.
- Simple in-memory task store (intended to be replaced with a DB for production).

Architecture (how it works)

1. Client POSTs to the API to create a task. The API returns a UUID for the logical task.
2. The API enqueues work in one of two modes:
   - Default: an in-process AsyncWorker (asyncio.Queue) executes the job in the same process (good for dev/testing).
   - Optional: the API enqueues the work to Celery (Redis broker) and the job runs in external worker processes.
3. When Celery is used, the Celery worker posts the result back to the API callback endpoint (/tasks/{id}/complete). The web API updates its in-memory task record with final status and result.

This flow provides a clear, practical example of request -> enqueue -> execute -> report back -> API shows final status. The callback approach is a fast, practical way to make Celery results visible to the web API without a persistent database.

Quick start

1. Install dependencies:

```powershell
.\.venv\Scripts\Activate
python -m pip install -r requirements.txt
```

2. Run the app (default in-process worker):

```powershell
uvicorn main:app --reload
```

3. Try a quick smoke test (no server required):

```powershell
# recommended: run the included smoke test script instead of a long one-liner
python smoke_test.py
```

# or use curl against a running server
```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

Celery (optional production-like setup)

Use Celery when you need distributed, durable workers that run outside the web process.

1. Ensure Redis (or another supported broker) is running. Example (Docker):

```powershell
docker run -p 6379:6379 --name redis -d redis:7
```

2. Start a Celery worker (run from this project root):

```powershell
celery -A celery_tasks worker --loglevel=info
```

3. Start the web app in Celery mode (PowerShell):

```powershell
$env:USE_CELERY = "1"
uvicorn main:app --reload
```

Notes on Celery integration
- When `USE_CELERY=1`, the web API delegates execution to `celery_tasks.demo_task` and stores the Celery task id in the task record as a placeholder (e.g. `celery:<id>`).
- The Celery task posts its final result back to the web API callback endpoint. That lets the API update its in-memory task record so GET /tasks/{id} returns final status and result.
- This quick callback approach is intended for demonstration and small deployments. For production, prefer storing tasks in a database so both web and worker can read/write durable state.

Callback / result sync (quick approach implemented)

- The web API exposes POST `/tasks/{task_id}/complete`.
- Celery tasks call this endpoint with JSON payload: `{"status": "SUCCESS"|"FAILED", "result": <value>}`.
- The API updates the in-memory `TASKS` store accordingly.

Environment variables
- `USE_CELERY` (default `0`) — set to `1` to enable Celery mode.
- `CELERY_BROKER_URL` — broker URL (default `redis://localhost:6379/0`).
- `CELERY_RESULT_BACKEND` — Celery result backend (default `redis://localhost:6379/1`).
- `TASK_CALLBACK_URL` — optional: instruct Celery tasks where to POST results; if not set Celery posts to `http://127.0.0.1:8000/tasks/{task_id}/complete`.

Endpoints (summary)
- GET `/` — basic service message
- GET `/health` — health check
- POST `/tasks/run` — create a task (returns `{"message": "Task submitted", "id": "<uuid>"}`)
- GET `/tasks/queue` — returns `{"queue_size": <int>, "num_workers": <int>}` (in-process worker only)
- GET `/tasks/{task_id}` — returns `{"task_id": "<uuid>", "status": "PENDING|RUNNING|SUCCESS|FAILED", "result": <value>}`
- POST `/tasks/{task_id}/complete` — callback endpoint used by Celery tasks to report final results

Testing
- Unit / integration testing: use `pytest` and FastAPI `TestClient` for in-process tests.
- Quick run: `python -m pytest -q` (if tests are present)

Production recommendations (next steps)
- Persist task metadata in a database (Postgres/SQLite) — this makes task state durable and accessible across restarts and multiple web processes.
- Let Celery workers update the same database record on completion (instead of an in-memory store).
- Monitor: deploy Flower, expose Prometheus metrics, and ship logs to a central logging service.
- Security: protect the callback endpoint (`/tasks/{id}/complete`) with authentication (e.g., a shared secret or mTLS) if workers run on different hosts.
