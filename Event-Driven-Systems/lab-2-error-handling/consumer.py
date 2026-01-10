import redis
import json
import time
import uuid
from datetime import datetime

class Consumer:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.max_retries = 3
        self.base_delay = 1.0
        
    def connect(self):
        try:
            self.redis_client.ping()
            print("Connected to Redis")
            return True
        except:
            print("Redis connection failed")
            return False
    
    def process_with_retry(self, message_id, fields, stream_name):
        # Get retry count from message metadata
        retry_count = int(fields.get('retry_count', 0))

        if retry_count >= self.max_retries:
            print(f"Max retries reached for message {message_id}. Sending to DLQ.")
            self.send_to_dlq(message_id, "Max retries exceeded", stream_name)
            return False

        try:
            # Try to process the message
            result = self.process_message(fields)
            if result:
                print(f"Message {message_id} processed successfully")
                return True
            else:
                # Processing failed, schedule retry
                self.schedule_retry(message_id, fields, stream_name, retry_count)
                return False
            
        except Exception as e:
            print(f"Error processing message {message_id}: {e}")
            self.schedule_retry(message_id, fields, stream_name, retry_count)


    def schedule_retry(self, message_id, fields, stream_name, retry_count):
        # Calculate exponential backoff delay
        delay = self.base_delay * (2 ** retry_count)
        print(f"Scheduling retry {retry_count + 1} for message {message_id} after {delay} seconds")

        # Add retry metadata
        retry_fields = fields.copy()
        retry_fields['retry_count'] = str(retry_count + 1)
        retry_fields['retry_timestamp'] = datetime.now().isoformat()
        retry_fields['original_message_id'] = message_id

        # Wait for delay, then republish to the retry stream
        time.sleep(delay)
        retry_stream = f"retry:{stream_name}"
        self.redis_client.xadd(retry_stream, retry_fields)


    def send_to_dlq(self, fields, error, stream_name):
        # Route failed messages to dead letter queue
        dlq_stream = f"{stream_name}:dlq"
        dlq_fields = fields.copy()
        dlq_fields['dlq_timestamp'] = datetime.now().isoformat()
        dlq_fields['error_reason'] = str(error)

        self.redis_client.xadd(dlq_stream, dlq_fields)
        print(f"Message sent to DLQ: {dlq_stream}")

    def process_message(self, fields):
        # Simulate processing with random failures
        event_type = fields.get('event_type')

        # Simulate different failure scenarios
        import random
        
        if event_type == "order_placed":
            
            if random.random() < 0.3: # 30% failure rate
                raise Exception("Simulated order processing error")
            
            data = json.loads(fields['data'])
            order_id = data['order_id']
            print(f"Processing order {order_id}")
            return True

        elif event_type == "payment_processed":
            if random.random() < 0.2: # 20% failure rate
                raise Exception("Simulated payment processing error")
            
            data = json.loads(fields['data'])
            payment_id = data['payment_id']
            print(f"Processing payment {payment_id}")
            return True
        
        return True

    def start_consuming(self):
        # Setup consumer groups
        streams = ["ecommerce:orders", "ecommerce:payments"]
        group_name = "error_handling_group"
        consumer_name = "consumer_1"
        
        for stream in streams:
            try:
                self.redis_client.xgroup_create(stream, group_name, id='0', mkstream=True)
            except:
                pass  # Group already exists
            
            # Also handle retry streams
            retry_stream = f"retry:{stream}"
            try:
                self.redis_client.xgroup_create(retry_stream, group_name, id='0', mkstream=True)
            except:
                pass
        
        print("Starting consumer with error handling...")
        
        try:
            while True:
                # Read from main streams and retry streams
                stream_dict = {}
                for stream in streams:
                    stream_dict[stream] = ">"
                    stream_dict[f"retry:{stream}"] = ">"
                
                messages = self.redis_client.xreadgroup(
                    group_name, consumer_name, stream_dict, 
                    count=1, block=1000
                )
                
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            print(f"\n--- Processing from {stream_name} ---")
                            
                            success = self.process_with_retry(message_id, fields, stream_name)
                            
                            if success:
                                self.redis_client.xack(stream_name, group_name, message_id)
                                print(f"Acknowledged {message_id}")
                            
        except KeyboardInterrupt:
            print("\nConsumer stopped")


if __name__ == "__main__":
    consumer = Consumer()
    if consumer.connect():
        consumer.start_consuming()