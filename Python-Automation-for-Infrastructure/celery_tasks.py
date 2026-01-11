from celery_app import celery_app
import time
import os
import requests

CALLBACK = os.environ.get("TASK_CALLBACK_URL")  # e.g. http://host:port/tasks/{task_id}/complete

@celery_app.task(bind=True)
def demo_task(self, payload=None):
    # simple demo task
    try:
        time.sleep(0.5)
        result = {"status": "ok", "payload": payload}
        status = "SUCCESS"
    except Exception as exc:
        result = {"error": str(exc)}
        status = "FAILED"

    # If callback URL is set, POST result back so the web app can update its TASKS store
    try:
        if CALLBACK:
            url = CALLBACK.format(task_id=payload.get('task_id')) if '{task_id}' in CALLBACK else CALLBACK
        else:
            url = f"http://127.0.0.1:8000/tasks/{payload.get('task_id')}/complete"
        requests.post(url, json={"status": status, "result": result}, timeout=5)
    except Exception:
        # best-effort: ignore callback errors
        pass

    return {"status": status, "result": result}
