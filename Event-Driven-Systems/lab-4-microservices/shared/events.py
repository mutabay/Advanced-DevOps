from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
import json

@dataclass
class BaseEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    source: str = ""
    correlation_id: str = ""
    causation_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "data": self.data
        })
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version=data["version"],
            source=data["source"],
            correlation_id=data["correlation_id"],
            causation_id=data.get("causation_id"),
            data=data["data"]
        )

@dataclass
class UserRegisteredEvent(BaseEvent):
    event_type: str = "UserRegistered"

@dataclass
class OrderPlacedEvent(BaseEvent):
    event_type: str = "OrderPlaced"

@dataclass
class PaymentProcessedEvent(BaseEvent):
    event_type: str = "PaymentProcessed"

@dataclass
class PaymentFailedEvent(BaseEvent):
    event_type: str = "PaymentFailed"