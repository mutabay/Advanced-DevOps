import redis
import json
import uuid
import time
import threading
from datetime import datetime

def connect_redis():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return r

def create_event(event_type, source, data):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "version": "1.0",
        "data": json.dumps(data)
    }

# Simulate different systems publishing events independently
def website_order_generator(redis_client):
    """Simulates web orders coming in randomly"""
    for i in range(10):
        order_data = {
            "order_id": f"web_order_{uuid.uuid4().hex[:8]}",
            "customer_id": f"customer_{uuid.uuid4().hex[:6]}",
            "source": "website",
            "items": [{"product_id": "laptop_123", "quantity": 1, "price": 999.99}],
            "total": 999.99
        }
        event = create_event("order_placed", "website", order_data)
        redis_client.xadd("ecommerce:orders", event)
        print(f"Website: Order {order_data['order_id']} placed")
        time.sleep(2)  # Orders every 2 seconds

def mobile_order_generator(redis_client):
    """Simulates mobile app orders coming in randomly"""
    for i in range(8):
        order_data = {
            "order_id": f"mobile_order_{uuid.uuid4().hex[:8]}",
            "customer_id": f"customer_{uuid.uuid4().hex[:6]}",
            "source": "mobile_app",
            "items": [{"product_id": "phone_456", "quantity": 1, "price": 699.99}],
            "total": 699.99
        }
        event = create_event("order_placed", "mobile_app", order_data)
        redis_client.xadd("ecommerce:orders", event)
        print(f"Mobile: Order {order_data['order_id']} placed")
        time.sleep(3)  # Orders every 3 seconds

def payment_webhook_simulator(redis_client):
    """Simulates payment webhooks arriving randomly"""
    for i in range(12):
        payment_data = {
            "payment_id": f"pay_{uuid.uuid4().hex[:8]}",
            "order_id": f"order_{uuid.uuid4().hex[:8]}",
            "amount": 850.50,
            "method": "credit_card",
            "status": "completed"
        }
        event = create_event("payment_processed", "payment_gateway", payment_data)
        redis_client.xadd("ecommerce:payments", event)
        print(f"Payment: {payment_data['payment_id']} processed")
        time.sleep(1.5)  # Payments every 1.5 seconds

def main():
    redis_client = connect_redis()
    print("Starting ASYNC event generation from multiple sources...")
    
    # Start multiple threads - each represents a different system
    website_thread = threading.Thread(target=website_order_generator, args=(redis_client,))
    mobile_thread = threading.Thread(target=mobile_order_generator, args=(redis_client,))
    payment_thread = threading.Thread(target=payment_webhook_simulator, args=(redis_client,))
    
    # All start at the same time - TRUE ASYNC!
    website_thread.start()
    mobile_thread.start() 
    payment_thread.start()
    
    # Wait for all to complete
    website_thread.join()
    mobile_thread.join()
    payment_thread.join()
    
    print("All async producers finished!")

if __name__ == "__main__":
    main()