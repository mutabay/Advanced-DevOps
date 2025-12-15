from kafka import KafkaConsumer, TopicPartition
import json
import time
import threading
import subprocess
from datetime import datetime

class SmartEventConsumer:
    def __init__(self, bootstrap_servers='localhost:9092', group_id='ecommerce_processors'):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumers = {}
        self.running = False
        self.use_container_fallback = False
        
        print("Initializing Kafka consumers...")
        
        # Try Python client first
        if not self._try_python_client():
            print("Python client failed, will use container commands")
            self.use_container_fallback = True
    
    def _try_python_client(self):
        """Try to initialize Python Kafka consumer"""
        try:
            # Test with a simple consumer
            test_consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"{self.group_id}_test",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000
            )
            
            # Test if we can get metadata
            topics = test_consumer.list_consumer_group_offsets()
            test_consumer.close()
            
            print("Python Kafka client connection successful")
            return True
            
        except Exception as e:
            print(f"Python client failed: {e}")
            return False
    
    def create_python_consumer(self, topics):
        """Create Python Kafka consumer for specific topics"""
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000
            )
            return consumer
        except Exception as e:
            print(f"Failed to create consumer: {e}")
            return None
    
    def process_order_event(self, key, message):
        """Process order-related events"""
        try:
            event_type = message.get('event_type', 'unknown')
            event_data = message.get('data', {})
            
            if event_type == 'order_placed':
                order_id = event_data.get('order_id', 'unknown')
                customer_id = event_data.get('customer_id', 'unknown')
                total = event_data.get('total', 0)
                
                print(f"  ORDER PROCESSED: {order_id} from {customer_id} (${total})")
                
                # Simulate order processing
                time.sleep(0.1)
                return True
            else:
                print(f"  Unknown order event: {event_type}")
                return False
                
        except Exception as e:
            print(f"  Error processing order: {e}")
            return False
    
    def process_payment_event(self, key, message):
        """Process payment-related events"""
        try:
            event_type = message.get('event_type', 'unknown')
            event_data = message.get('data', {})
            
            if event_type == 'payment_processed':
                payment_id = event_data.get('payment_id', 'unknown')
                order_id = event_data.get('order_id', 'unknown')
                amount = event_data.get('amount', 0)
                
                print(f"  PAYMENT PROCESSED: {payment_id} for order {order_id} (${amount})")
                
                # Simulate payment processing
                time.sleep(0.1)
                return True
            else:
                print(f"  Unknown payment event: {event_type}")
                return False
                
        except Exception as e:
            print(f"  Error processing payment: {e}")
            return False
    
    def process_inventory_event(self, key, message):
        """Process inventory-related events"""
        try:
            event_type = message.get('event_type', 'unknown')
            event_data = message.get('data', {})
            
            if event_type == 'inventory_updated':
                product_id = event_data.get('product_id', 'unknown')
                action = event_data.get('action', 'unknown')
                quantity = event_data.get('quantity', 0)
                
                print(f"  INVENTORY UPDATED: {product_id} {action} {quantity} units")
                
                # Simulate inventory processing
                time.sleep(0.1)
                return True
            else:
                print(f"  Unknown inventory event: {event_type}")
                return False
                
        except Exception as e:
            print(f"  Error processing inventory: {e}")
            return False
    
    def consume_topic_python(self, topics, processor_func, thread_name):
        """Consume messages from topics using Python client"""
        consumer = self.create_python_consumer(topics)
        if not consumer:
            print(f"{thread_name}: Failed to create consumer")
            return
        
        print(f"{thread_name}: Started consuming from {topics}")
        
        try:
            processed = 0
            
            for message in consumer:
                if not self.running:
                    break
                
                topic = message.topic
                partition = message.partition
                key = message.key
                value = message.value
                
                print(f"{thread_name}: Processing message from {topic} partition {partition} (key: {key})")
                
                if processor_func(key, value):
                    processed += 1
                
                # Show progress
                if processed % 10 == 0 and processed > 0:
                    print(f"{thread_name}: Processed {processed} messages")
        
        except Exception as e:
            print(f"{thread_name}: Consumer error: {e}")
        
        finally:
            consumer.close()
            print(f"{thread_name}: Consumer closed, processed {processed} total messages")
    
    def consume_topic_container(self, topic, processor_func, thread_name):
        """Consume messages using container commands"""
        print(f"{thread_name}: Starting container-based consumption of {topic}")
        
        try:
            cmd = [
                'podman', 'exec', 'kafka',
                '/opt/kafka/bin/kafka-console-consumer.sh',
                '--bootstrap-server', 'localhost:9092',
                '--topic', topic,
                '--from-beginning',
                '--property', 'print.key=true',
                '--property', 'key.separator=:'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            processed = 0
            
            while self.running:
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse key:value format
                    if ':' in line:
                        key, json_data = line.split(':', 1)
                        try:
                            message = json.loads(json_data)
                            
                            print(f"{thread_name}: Processing message (key: {key})")
                            
                            if processor_func(key, message):
                                processed += 1
                            
                            if processed % 5 == 0 and processed > 0:
                                print(f"{thread_name}: Processed {processed} messages")
                                
                        except json.JSONDecodeError:
                            print(f"{thread_name}: Failed to parse JSON: {json_data}")
                    
                except Exception as e:
                    print(f"{thread_name}: Error reading message: {e}")
                    break
            
            process.terminate()
            print(f"{thread_name}: Container consumer stopped, processed {processed} messages")
            
        except Exception as e:
            print(f"{thread_name}: Container consumer error: {e}")
    
    def start_consuming(self):
        """Start consuming all topics with separate threads"""
        self.running = True
        
        print("Starting multi-topic consumption...")
        print("=" * 50)
        
        # Define topic-processor mappings
        topic_processors = [
            (['ecommerce.orders'], self.process_order_event, 'ORDER-PROCESSOR'),
            (['ecommerce.payments'], self.process_payment_event, 'PAYMENT-PROCESSOR'),
            (['ecommerce.inventory'], self.process_inventory_event, 'INVENTORY-PROCESSOR')
        ]
        
        threads = []
        
        # Start consumer threads
        for topics, processor, thread_name in topic_processors:
            if self.use_container_fallback:
                # Container commands work with single topics
                for topic in topics:
                    thread = threading.Thread(
                        target=self.consume_topic_container,
                        args=(topic, processor, f"{thread_name}-{topic}")
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
            else:
                thread = threading.Thread(
                    target=self.consume_topic_python,
                    args=(topics, processor, thread_name)
                )
                thread.daemon = True
                thread.start()
                threads.append(thread)
        
        return threads
    
    def stop_consuming(self):
        """Stop all consumers"""
        print("\nStopping consumers...")
        self.running = False
        time.sleep(2)
        print("All consumers stopped")
    
    def show_partition_assignment(self):
        """Show which partitions are assigned to this consumer"""
        if self.use_container_fallback:
            print("Container mode: Partition assignment not available")
            return
        
        try:
            consumer = self.create_python_consumer(['ecommerce.orders', 'ecommerce.payments', 'ecommerce.inventory'])
            
            # Wait for partition assignment
            consumer.poll(timeout_ms=5000)
            
            assignment = consumer.assignment()
            
            print("\nPartition Assignment:")
            print("=" * 30)
            
            for tp in assignment:
                print(f"Topic: {tp.topic}, Partition: {tp.partition}")
            
            consumer.close()
            
        except Exception as e:
            print(f"Error getting partition assignment: {e}")

def main():
    print("Kafka Smart Event Consumer")
    print("=" * 30)
    
    consumer = SmartEventConsumer()
    
    print("\n1. Start consuming all topics")
    print("2. Show partition assignment")
    print("3. Consume for specific duration")
    
    choice = input("\nChoose option (1-3): ")
    
    try:
        if choice == "1":
            threads = consumer.start_consuming()
            
            print("\nPress Ctrl+C to stop consuming...")
            while True:
                time.sleep(1)
        
        elif choice == "2":
            consumer.show_partition_assignment()
        
        elif choice == "3":
            duration = int(input("Duration in seconds (default 30): ") or "30")
            
            threads = consumer.start_consuming()
            
            print(f"\nConsuming for {duration} seconds...")
            time.sleep(duration)
            
            consumer.stop_consuming()
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nStopping...")
        consumer.stop_consuming()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()