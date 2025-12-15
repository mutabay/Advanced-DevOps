import redis
import json
import time

def connect_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("Consumer connected to Redis!")
        return r
    except redis.ConnectionError:
        print("Failed to connect to Redis")
        return None

def process_order_event(event_data):
    """Process order placed events"""
    # Parse the JSON string in the 'data' field
    data = json.loads(event_data['data'])
    order_id = data['order_id']
    total = data['total']
    customer_id = data['customer_id']
    items_count = len(data['items'])
    
    print(f"Processing order {order_id}")
    print(f"  Customer: {customer_id}")
    print(f"  Items: {items_count}")
    print(f"  Total: ${total}")
    
    # Simulate processing work
    time.sleep(0.5)
    print(f"Order {order_id} processed successfully!")

def process_payment_event(event_data):
    """Process payment events"""
    # Parse the JSON string in the 'data' field
    data = json.loads(event_data['data'])
    payment_id = data['payment_id']
    order_id = data['order_id']
    amount = data['amount']
    method = data['method']
    
    print(f"Processing payment {payment_id}")
    print(f"  Order: {order_id}")
    print(f"  Amount: ${amount}")
    print(f"  Method: {method}")
    
    # Simulate processing work
    time.sleep(0.5)
    print(f"Payment {payment_id} processed successfully!")

def setup_consumer_group(redis_client, stream_name, group_name):
    """Create consumer group if it doesn't exist"""
    try:
        redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        print(f"Created consumer group '{group_name}' for stream '{stream_name}'")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{group_name}' already exists for stream '{stream_name}'")
        else:
            raise e

def main():
    # Connect to Redis
    redis_client = connect_redis()
    if not redis_client:
        return
    
    # Setup consumer groups
    group_name = "ecommerce_processors"
    consumer_name = "consumer_1"
    
    setup_consumer_group(redis_client, "ecommerce:orders", group_name)
    setup_consumer_group(redis_client, "ecommerce:payments", group_name)
    
    print(f"Starting consumer '{consumer_name}' in group '{group_name}'")
    print("Waiting for events... (Press Ctrl+C to stop)")
    
    try:
        while True:
            # Read from multiple streams
            streams = {
                "ecommerce:orders": ">",
                "ecommerce:payments": ">"
            }
            
            messages = redis_client.xreadgroup(
                group_name, 
                consumer_name, 
                streams, 
                count=1, 
                block=1000  # Wait 1 second
            )
            
            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        print(f"\n--- New event from {stream_name} ---")
                        print(f"Event ID: {fields.get('event_id')}")
                        print(f"Event Type: {fields.get('event_type')}")
                        print(f"Timestamp: {fields.get('timestamp')}")
                        
                        # Parse the event
                        event_type = fields.get('event_type')
                        
                        try:
                            # Process based on event type
                            if event_type == 'order_placed':
                                process_order_event(fields)
                            elif event_type == 'payment_processed':
                                process_payment_event(fields)
                            else:
                                print(f"Unknown event type: {event_type}")
                            
                            # Acknowledge the message
                            redis_client.xack(stream_name, group_name, message_id)
                            print(f"Acknowledged message {message_id}")
                            
                        except Exception as e:
                            print(f"Error processing message {message_id}: {e}")
                            print(f"Raw fields: {fields}")
                            # In real systems, you'd send to DLQ here
            
    except KeyboardInterrupt:
        print("\nConsumer stopped by user")

if __name__ == "__main__":
    main()