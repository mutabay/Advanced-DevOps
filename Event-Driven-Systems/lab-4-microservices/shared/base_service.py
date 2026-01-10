import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import List
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from events import BaseEvent

class BaseService(ABC):
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(service_name)
        
        # Initialize Kafka
        self.producer = None
        self.consumer = None
        self._init_kafka()
    
    def _init_kafka(self):
        try:
            # Use port 9093 since that's what we mapped
            self.producer = KafkaProducer(
                bootstrap_servers='localhost:9093',
                value_serializer=lambda v: v.encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                request_timeout_ms=30000,  # 30 seconds timeout
                retries=5
            )
            
            self.consumer = KafkaConsumer(
                bootstrap_servers='localhost:9093',
                group_id=f"{self.service_name}-group",
                value_deserializer=lambda m: m.decode('utf-8'),
                auto_offset_reset='latest',
                request_timeout_ms=30000
            )
            
            self.logger.info(f"Kafka initialized for {self.service_name}")
            
        except NoBrokersAvailable:
            self.logger.error("Kafka not available")
            raise
    
    def publish_event(self, event: BaseEvent):
        event.source = self.service_name
        topic = self._get_topic_for_event(event.event_type)
        
        try:
            self.producer.send(topic, value=event.to_json())
            self.producer.flush()
            self.logger.info(f"Published {event.event_type} to {topic}")
        except Exception as e:
            self.logger.error(f"Failed to publish {event.event_type}: {e}")
    
    def _get_topic_for_event(self, event_type: str) -> str:
        topic_mapping = {
            'UserRegistered': 'user.events',
            'OrderPlaced': 'order.events',
            'PaymentProcessed': 'payment.events',
            'PaymentFailed': 'payment.events',
        }
        return topic_mapping.get(event_type, 'general.events')
    
    def subscribe_to_topics(self, topics: List[str]):
        self.consumer.subscribe(topics)
        self.logger.info(f"Subscribed to: {topics}")
    
    def start_consuming(self):
        self.running = True
        for message in self.consumer:
            if not self.running:
                break
            
            try:
                # Parse the JSON back to event
                import json
                data = json.loads(message.value)
                event = BaseEvent.from_json(message.value)
                
                self.logger.info(f"Received {event.event_type}")
                self.handle_event(event)
                
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
    
    @abstractmethod
    def handle_event(self, event: BaseEvent):
        pass
    
    @abstractmethod
    def get_subscribed_topics(self) -> List[str]:
        pass