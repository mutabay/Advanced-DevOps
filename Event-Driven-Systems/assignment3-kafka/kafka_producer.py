from kafka import KafkaProducer
import json
import uuid
import time
import subprocess
from datetime import datetime

class SmartEventProducer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.use_container_fallback = False
        
        print("Initializing Kafka producer...")
        
        # Try to connect with Python client
        if self._try_python_client():
            print("Using Python Kafka client")
        else:
            print("Python client failed, using container commands")
            self.use_container_fallback = True
    
    def _try_python_client(self):
        """Try to initialize Python Kafka client"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                request_timeout_ms=10000
            )
            
            # Test the connection
            metadata = self.producer.list_topics(timeout=5)
            print(f"Connected! Found {len(metadata.topics)} topics")
            return True
            
        except Exception as e:
            print(f"Python client connection failed: {e}")
            return False
    
    def create_event(self, event_type, data, source="kafka_producer"):
        """Create standardized event envelope"""
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "source": source,
            "data": data
        }
    
    def send_event_python(self, topic, key, event):
        """Send event using Python client"""
        try:
            future = self.producer.send(topic, key=key, value=event)
            record_metadata = future.get(timeout=10)
            
            print(f"Sent to {topic} partition {record_metadata.partition} (key: {key})")
            return record_metadata
            
        except Exception as e:
            print(f"Failed to send to {topic}: {e}")
            return None
    
    def send_event_container(self, topic, key, event):
        """Send event using container commands"""
        try:
            # Convert event to JSON string
            event_json = json.dumps(event)
            
            # Use kafka-console-producer via container
            cmd = [
                'podman', 'exec', '-i', 'kafka',
                '/opt/kafka/bin/kafka-console-producer.sh',
                '--bootstrap-server', 'localhost:9092',
                '--topic', topic,
                '--property', f'key.separator=:',
                '--property', 'parse.key=true'
            ]
            
            # Format as key:value
            message = f"{key}:{event_json}"
            
            result = subprocess.run(cmd, input=message, text=True, 
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                print(f"Sent to {topic} (key: {key}) via container")
                return True
            else:
                print(f"Container send failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Container send error: {e}")
            return False
    
    def send_order_event(self, order_data):
        """Send order event partitioned by customer_id"""
        event = self.create_event("order_placed", order_data)
        partition_key = order_data['customer_id']
        
        if self.use_container_fallback:
            return self.send_event_container('ecommerce.orders', partition_key, event)
        else:
            return self.send_event_python('ecommerce.orders', partition_key, event)
    
    def send_payment_event(self, payment_data):
        """Send payment event partitioned by order_id"""
        event = self.create_event("payment_processed", payment_data)
        partition_key = payment_data['order_id']
        
        if self.use_container_fallback:
            return self.send_event_container('ecommerce.payments', partition_key, event)
        else:
            return self.send_event_python('ecommerce.payments', partition_key, event)
    
    def send_inventory_event(self, inventory_data):
        """Send inventory event partitioned by product_id"""
        event = self.create_event("inventory_updated", inventory_data)
        partition_key = inventory_data['product_id']
        
        if self.use_container_fallback:
            return self.send_event_container('ecommerce.inventory', partition_key, event)
        else:
            return self.send_event_python('ecommerce.inventory', partition_key, event)
    
    def generate_realistic_order_flow(self):
        """Generate a complete order flow with related events"""
        customer_id = f"customer_{uuid.uuid4().hex[:6]}"
        order_id = f"order_{uuid.uuid4().hex[:8]}"
        product_id = "laptop_123"
        
        order_data = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": [
                {"product_id": product_id, "quantity": 1, "price": 999.99}
            ],
            "total": 999.99,
            "status": "pending"
        }
        
        payment_data = {
            "payment_id": f"pay_{uuid.uuid4().hex[:8]}",
            "order_id": order_id,
            "amount": 999.99,
            "method": "credit_card",
            "status": "completed"
        }
        
        inventory_data = {
            "product_id": product_id,
            "action": "reserved",
            "quantity": 1,
            "remaining_stock": 49,
            "order_id": order_id
        }
        
        return order_data, payment_data, inventory_data
    
    def run_order_flow_simulation(self, count=5):
        """Generate multiple complete order flows"""
        print(f"\nStarting order flow simulation ({count} flows)")
        print("=" * 50)
        
        successful = 0
        
        for i in range(count):
            print(f"\n--- Order Flow {i+1}/{count} ---")
            
            order_data, payment_data, inventory_data = self.generate_realistic_order_flow()
            
            # Send events in business logic order
            if self.send_order_event(order_data):
                time.sleep(0.1)
                
                if self.send_payment_event(payment_data):
                    time.sleep(0.1)
                    
                    if self.send_inventory_event(inventory_data):
                        successful += 1
                        print(f"Flow {i+1} completed successfully")
                    else:
                        print(f"Flow {i+1} failed at inventory")
                else:
                    print(f"Flow {i+1} failed at payment")
            else:
                print(f"Flow {i+1} failed at order")
            
            time.sleep(1)
        
        print(f"\nSimulation complete! {successful}/{count} flows successful")
    
    def verify_messages_sent(self):
        """Verify messages were actually sent to topics"""
        print("\nVerifying messages in topics...")
        
        for topic in ['ecommerce.orders', 'ecommerce.payments', 'ecommerce.inventory']:
            try:
                # Use container command to count messages
                cmd = [
                    'podman', 'exec', 'kafka',
                    '/opt/kafka/bin/kafka-console-consumer.sh',
                    '--bootstrap-server', 'localhost:9092',
                    '--topic', topic,
                    '--from-beginning',
                    '--timeout-ms', '3000'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.stdout:
                    message_count = len(result.stdout.strip().split('\n'))
                    print(f"{topic}: {message_count} messages")
                else:
                    print(f"{topic}: 0 messages")
                    
            except subprocess.TimeoutExpired:
                print(f"{topic}: timeout (likely has messages)")
            except Exception as e:
                print(f"{topic}: error checking - {e}")
    
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            print("Producer closed")

def main():
    print("Kafka Smart Event Producer")
    print("=" * 30)
    
    try:
        producer = SmartEventProducer()
        
        print("\n1. Run order flow simulation (5 flows)")
        print("2. Send single order flow")
        print("3. Verify messages in topics")
        
        choice = input("\nChoose option (1-3): ")
        
        if choice == "1":
            producer.run_order_flow_simulation(5)
            producer.verify_messages_sent()
            
        elif choice == "2":
            order_data, payment_data, inventory_data = producer.generate_realistic_order_flow()
            
            print("Sending single order flow...")
            producer.send_order_event(order_data)
            producer.send_payment_event(payment_data)
            producer.send_inventory_event(inventory_data)
            
        elif choice == "3":
            producer.verify_messages_sent()
            
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nStopping producer...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'producer' in locals():
            producer.close()

if __name__ == "__main__":
    main()