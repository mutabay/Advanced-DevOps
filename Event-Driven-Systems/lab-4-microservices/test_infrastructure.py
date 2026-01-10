import sys
import os

# Add shared folder to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from events import UserRegisteredEvent, OrderPlacedEvent
from base_service import BaseService

class TestService(BaseService):
    def get_subscribed_topics(self):
        return ['user.events', 'order.events']
    
    def handle_event(self, event):
        print(f"RECEIVED EVENT: {event.event_type}")
        print(f"  Data: {event.data}")

def main():
    print("Testing Event Framework")
    print("=" * 30)
    
    service = TestService("test-service")
    
    try:
        # Test 1: Create and publish events
        print("1. Publishing events...")
        
        user_event = UserRegisteredEvent(
            correlation_id="test-123",
            data={"user_id": "user-456", "email": "test@example.com"}
        )
        
        order_event = OrderPlacedEvent(
            correlation_id="test-123", 
            data={"order_id": "order-789", "customer_id": "user-456", "total": 99.99}
        )
        
        service.publish_event(user_event)
        service.publish_event(order_event)
        
        print("✓ Events published")
        
        # Test 2: Try to consume events  
        print("\n2. Starting consumer...")
        service.subscribe_to_topics(service.get_subscribed_topics())
        
        import threading
        consumer_thread = threading.Thread(target=service.start_consuming)
        consumer_thread.daemon = True
        consumer_thread.start()
        
        # Wait a bit to see events
        import time
        time.sleep(10)
        
        print("✓ Test completed")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Make sure Kafka is running:")
        print("  docker-compose up -d zookeeper kafka")
    finally:
        service.stop()

if __name__ == "__main__":
    main()