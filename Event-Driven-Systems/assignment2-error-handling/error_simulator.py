import redis
import json
import uuid
import time
import random
from datetime import datetime

class ErrorSimulator:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def generate_poison_messages(self, count=3):
        """Create malformed events that will always fail"""
        print(f"Generating {count} poison messages...")
        
        poison_events = [
            # Invalid JSON in data field
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "order_placed",
                "timestamp": datetime.now().isoformat(),
                "source": "poison_generator",
                "version": "1.0",
                "data": "invalid_json_data"  # This will break JSON parsing
            },
            # Missing required fields
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "payment_processed",
                "timestamp": datetime.now().isoformat(),
                "source": "poison_generator",
                "version": "1.0"
                # Missing 'data' field entirely
            },
            # Wrong data types
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "order_placed", 
                "timestamp": datetime.now().isoformat(),
                "source": "poison_generator",
                "version": "1.0",
                "data": json.dumps({
                    "order_id": 12345,  # Should be string
                    "total": "not_a_number"  # Should be float
                })
            }
        ]
        
        for i, event in enumerate(poison_events[:count]):
            self.client.xadd("ecommerce:orders", event)
            print(f"Published poison message {i+1}")
            time.sleep(0.5)
    
    def simulate_high_failure_rate(self, duration=30):
        """Generate events that will trigger many retries"""
        print(f"Simulating high failure rate for {duration} seconds...")
        
        end_time = time.time() + duration
        while time.time() < end_time:
            # Create events that will likely fail in your consumer
            order_data = {
                "order_id": f"fail_order_{uuid.uuid4().hex[:8]}",
                "customer_id": f"customer_{uuid.uuid4().hex[:6]}",
                "total": random.uniform(1.0, 100.0),
                "items": [{"product_id": "laptop_123", "quantity": 1}]
            }
            
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "order_placed",
                "timestamp": datetime.now().isoformat(),
                "source": "failure_simulator",
                "version": "1.0", 
                "data": json.dumps(order_data)
            }
            
            self.client.xadd("ecommerce:orders", event)
            print(f"Published order: {order_data['order_id']}")
            time.sleep(2)
    
    def flood_with_events(self, count=50):
        """Generate many events quickly to test load"""
        print(f"Flooding with {count} events...")
        
        for i in range(count):
            order_data = {
                "order_id": f"flood_order_{i:03d}",
                "customer_id": f"customer_{uuid.uuid4().hex[:6]}",
                "total": random.uniform(10.0, 1000.0),
                "items": [{"product_id": "test_product", "quantity": 1}]
            }
            
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "order_placed",
                "timestamp": datetime.now().isoformat(),
                "source": "flood_generator",
                "version": "1.0",
                "data": json.dumps(order_data)
            }
            
            self.client.xadd("ecommerce:orders", event)
            
            if i % 10 == 0:
                print(f"Published {i} events...")
        
        print(f"Flood complete: {count} events published")

def main():
    simulator = ErrorSimulator()
    
    print("Error Simulator Options:")
    print("1. Generate poison messages")
    print("2. Simulate high failure rate")
    print("3. Flood with events")
    
    choice = input("Choose option (1-3): ")
    
    if choice == "1":
        count = int(input("Number of poison messages (default 3): ") or "3")
        simulator.generate_poison_messages(count)
    elif choice == "2":
        duration = int(input("Duration in seconds (default 30): ") or "30")
        simulator.simulate_high_failure_rate(duration)
    elif choice == "3":
        count = int(input("Number of events (default 50): ") or "50")
        simulator.flood_with_events(count)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()