from kafka.admin import KafkaAdminClient, NewTopic
import time

class TopicManager:
    def __init__(self, bootstrap_servers='localhost:9092'):
        print("Connecting to Kafka...")
        
        # Try different configurations
        configs = [
            {'bootstrap_servers': bootstrap_servers, 'api_version': 'auto'},
            {'bootstrap_servers': bootstrap_servers, 'api_version': (2, 8, 0)},
            {'bootstrap_servers': bootstrap_servers, 'api_version': (3, 0, 0)},
        ]
        
        self.admin_client = None
        
        for i, config in enumerate(configs):
            try:
                print(f"Trying connection config {i+1}...")
                self.admin_client = KafkaAdminClient(**config)
                
                # Test the connection
                topics = self.admin_client.list_topics(timeout=5)
                print(f"Connected! Found {len(topics)} existing topics")
                return
                
            except Exception as e:
                print(f"Config {i+1} failed: {e}")
                continue
        
        raise Exception("All connection attempts failed")
    
    def create_ecommerce_topics(self):
        """Create e-commerce topics"""
        if not self.admin_client:
            print("No connection to Kafka")
            return
        
        topics = [
            NewTopic(name="ecommerce.orders", num_partitions=3, replication_factor=1),
            NewTopic(name="ecommerce.payments", num_partitions=3, replication_factor=1),
            NewTopic(name="ecommerce.inventory", num_partitions=2, replication_factor=1)
        ]
        
        print("Creating e-commerce topics...")
        
        try:
            result = self.admin_client.create_topics(topics, validate_only=False)
            
            for topic_name, future in result.items():
                try:
                    future.result(timeout=10)
                    print(f"Created: {topic_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"Already exists: {topic_name}")
                    else:
                        print(f"Failed {topic_name}: {e}")
            
            time.sleep(2)
            self.list_topics()
            
        except Exception as e:
            print(f"Error creating topics: {e}")
    
    def list_topics(self):
        """List topics"""
        if not self.admin_client:
            print("No connection to Kafka")
            return
            
        try:
            all_topics = self.admin_client.list_topics(timeout=5)
            ecommerce_topics = [t for t in all_topics if t.startswith('ecommerce.')]
            
            print(f"\nFound {len(all_topics)} total topics")
            
            if ecommerce_topics:
                print("E-commerce topics:")
                for topic in ecommerce_topics:
                    print(f"  - {topic}")
            else:
                print("No e-commerce topics found")
                
        except Exception as e:
            print(f"Error listing topics: {e}")

def test_with_container_commands():
    """Test using direct container commands"""
    print("Testing with container commands...")
    
    import subprocess
    
    try:
        # List topics using container command
        result = subprocess.run([
            'podman', 'exec', 'kafka', 
            '/opt/kafka/bin/kafka-topics.sh', 
            '--bootstrap-server', 'localhost:9092', 
            '--list'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            topics = result.stdout.strip().split('\n') if result.stdout.strip() else []
            print(f"Container command works! Found {len(topics)} topics")
            if topics and topics[0]:  # Check if not empty
                for topic in topics:
                    print(f"  - {topic}")
            return True
        else:
            print(f"Container command failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Container command timed out")
        return False
    except Exception as e:
        print(f"Container command error: {e}")
        return False

def create_topics_with_container():
    """Create topics using container commands"""
    print("Creating topics with container commands...")
    
    import subprocess
    
    topics_to_create = [
        ("ecommerce.orders", 3),
        ("ecommerce.payments", 3), 
        ("ecommerce.inventory", 2)
    ]
    
    for topic_name, partitions in topics_to_create:
        try:
            result = subprocess.run([
                'podman', 'exec', 'kafka',
                '/opt/kafka/bin/kafka-topics.sh',
                '--bootstrap-server', 'localhost:9092',
                '--create', '--topic', topic_name,
                '--partitions', str(partitions),
                '--replication-factor', '1'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"Created: {topic_name}")
            else:
                if "already exists" in result.stderr.lower():
                    print(f"Already exists: {topic_name}")
                else:
                    print(f"Failed {topic_name}: {result.stderr}")
                    
        except Exception as e:
            print(f"Error creating {topic_name}: {e}")

def main():
    print("Kafka Topic Manager")
    print("=" * 30)
    
    print("\n1. Create topics (Python client)")
    print("2. List topics (Python client)")
    print("3. Test container commands")
    print("4. Create topics (container commands)")
    
    choice = input("\nChoose option (1-4): ")
    
    if choice == "1":
        try:
            manager = TopicManager()
            manager.create_ecommerce_topics()
        except Exception as e:
            print(f"Python client failed: {e}")
            print("Try option 4 (container commands) instead")
    
    elif choice == "2":
        try:
            manager = TopicManager()
            manager.list_topics()
        except Exception as e:
            print(f"Python client failed: {e}")
    
    elif choice == "3":
        test_with_container_commands()
    
    elif choice == "4":
        create_topics_with_container()
        # Verify with container command
        test_with_container_commands()
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()