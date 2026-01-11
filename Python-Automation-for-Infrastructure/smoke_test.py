"""Simple smoke test for the module. Run with `python smoke_test.py`.

This starts FastAPI's TestClient in-process (no uvicorn), calls /, creates a task and polls it until final status.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
from fastapi.testclient import TestClient

from main import app


def run():
    print("Running smoke test (in-process). This does NOT start a server.")
    with TestClient(app) as client:
        r = client.get("/")
        print("GET / ->", r.status_code, r.json())

        r = client.get("/health")
        print("GET /health ->", r.status_code, r.json())

        r = client.post("/tasks/run")
        print("POST /tasks/run ->", r.status_code, r.json())
        tid = r.json().get("id")

        # Poll until final state or timeout
        final = None
        for i in range(50):
            res = client.get(f"/tasks/{tid}")
            print(f"poll {i}:", res.status_code, res.json())
            status = res.json().get("status")
            if status in ("SUCCESS", "FAILED"):
                final = status
                break
            time.sleep(0.05)

        print("Final status:", final)


if __name__ == '__main__':
    run()

