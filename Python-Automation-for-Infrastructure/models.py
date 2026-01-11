from enum import Enum
from pydantic import BaseModel
from uuid import UUID


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Task(BaseModel):
    id: UUID
    status: TaskStatus
    result: str = ""

