import subprocess
import json
import time
from datetime import datetime
from collections import defaultdict

class KafkaClusterMonitor:
    def __init__(self):
        self.container_name = 'kafka'
        print("Kafka Cluster Monitor initialized")
    
    def run_kafka_command(self, command_args):
        """Run Kafka command via container"""
        try:
            cmd = ['podman', 'exec', self.container_name] + command_args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Command timed out")
            return None
        except Exception as e:
            print(f"Error running command: {e}")
            return None
    
    def get_topic_details(self):
        """Get detailed information about all topics"""
        print("Getting topic details...")
        
        # List all topics
        topics_output = self.run_kafka_command([
            '/opt/kafka/bin/kafka-topics.sh',
            '--bootstrap-server', 'localhost:9092',
            '--list'
        ])
        
        if not topics_output:
            print("Failed to get topics")
            return {}
        
        topics = [t for t in topics_output.split('\n') if t.strip()]
        ecommerce_topics = [t for t in topics if t.startswith('ecommerce.')]
        
        topic_details = {}
        
        for topic in ecommerce_topics:
            # Get detailed topic info
            describe_output = self.run_kafka_command([
                '/opt/kafka/bin/kafka-topics.sh',
                '--bootstrap-server', 'localhost:9092',
                '--describe', '--topic', topic
            ])
            
            if describe_output:
                topic_details[topic] = self.parse_topic_description(describe_output)
        
        return topic_details
    
    def parse_topic_description(self, output):
        """Parse topic description output"""
        lines = output.split('\n')
        topic_info = {'partitions': []}
        
        for line in lines:
            if line.startswith('Topic:'):
                # Parse main topic line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'PartitionCount:':
                        topic_info['partition_count'] = int(parts[i+1])
                    elif part == 'ReplicationFactor:':
                        topic_info['replication_factor'] = int(parts[i+1])
            
            elif line.startswith('\tPartition:'):
                # Parse partition info
                parts = line.split()
                partition_info = {}
                
                for i, part in enumerate(parts):
                    if part == 'Partition:':
                        partition_info['id'] = int(parts[i+1])
                    elif part == 'Leader:':
                        partition_info['leader'] = int(parts[i+1])
                    elif part == 'Replicas:':
                        partition_info['replicas'] = parts[i+1]
                
                topic_info['partitions'].append(partition_info)
        
        return topic_info
    
    def get_consumer_groups(self):
        """Get information about consumer groups"""
        print("Getting consumer group information...")
        
        # List consumer groups
        groups_output = self.run_kafka_command([
            '/opt/kafka/bin/kafka-consumer-groups.sh',
            '--bootstrap-server', 'localhost:9092',
            '--list'
        ])
        
        if not groups_output:
            return {}
        
        groups = [g for g in groups_output.split('\n') if g.strip()]
        group_details = {}
        
        for group in groups:
            if not group or group.startswith('Note:') or group.startswith('GROUP'):
                continue
            
            # Get group details
            detail_output = self.run_kafka_command([
                '/opt/kafka/bin/kafka-consumer-groups.sh',
                '--bootstrap-server', 'localhost:9092',
                '--describe', '--group', group
            ])
            
            if detail_output:
                group_details[group] = self.parse_consumer_group_output(detail_output)
        
        return group_details
    
    def parse_consumer_group_output(self, output):
        """Parse consumer group describe output"""
        lines = output.split('\n')
        group_info = {'members': []}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Consumer group') or line.startswith('GROUP'):
                continue
            
            # Parse member info
            parts = line.split()
            if len(parts) >= 7:
                member_info = {
                    'topic': parts[1],
                    'partition': parts[2],
                    'current_offset': parts[3],
                    'log_end_offset': parts[4],
                    'lag': parts[5],
                    'consumer_id': parts[6] if len(parts) > 6 else 'unknown'
                }
                group_info['members'].append(member_info)
        
        return group_info
    
    def get_topic_message_counts(self):
        """Get approximate message counts for topics"""
        print("Checking topic message counts...")
        
        ecommerce_topics = ['ecommerce.orders', 'ecommerce.payments', 'ecommerce.inventory']
        message_counts = {}
        
        for topic in ecommerce_topics:
            try:
                # Get high water marks for all partitions
                cmd = [
                    'podman', 'exec', self.container_name,
                    '/opt/kafka/bin/kafka-console-consumer.sh',
                    '--bootstrap-server', 'localhost:9092',
                    '--topic', topic,
                    '--from-beginning',
                    '--timeout-ms', '2000'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.stdout:
                    # Count non-empty lines
                    lines = [line for line in result.stdout.split('\n') if line.strip()]
                    message_counts[topic] = len(lines)
                else:
                    message_counts[topic] = 0
                    
            except subprocess.TimeoutExpired:
                # Timeout usually means there are many messages
                message_counts[topic] = "Many (timeout)"
            except Exception as e:
                message_counts[topic] = f"Error: {e}"
        
        return message_counts
    
    def calculate_throughput_stats(self, message_counts):
        """Calculate basic throughput statistics"""
        total_messages = 0
        
        for topic, count in message_counts.items():
            if isinstance(count, int):
                total_messages += count
        
        return {
            'total_messages': total_messages,
            'topics_monitored': len(message_counts),
            'avg_messages_per_topic': total_messages / len(message_counts) if message_counts else 0
        }
    
    def print_cluster_dashboard(self):
        """Print a comprehensive cluster dashboard"""
        print("\n" + "=" * 60)
        print("KAFKA CLUSTER DASHBOARD")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Topic Information
        print(f"\nTOPIC DETAILS")
        print("-" * 40)
        
        topic_details = self.get_topic_details()
        
        for topic, details in topic_details.items():
            print(f"\nTopic: {topic}")
            print(f"  Partitions: {details.get('partition_count', 'unknown')}")
            print(f"  Replication: {details.get('replication_factor', 'unknown')}")
            
            partitions = details.get('partitions', [])
            for partition in partitions:
                print(f"    Partition {partition.get('id', '?')}: Leader {partition.get('leader', '?')}")
        
        # Message Counts
        print(f"\nMESSAGE COUNTS")
        print("-" * 40)
        
        message_counts = self.get_topic_message_counts()
        for topic, count in message_counts.items():
            print(f"{topic}: {count}")
        
        # Throughput Stats
        throughput_stats = self.calculate_throughput_stats(message_counts)
        print(f"\nTHROUGHPUT STATISTICS")
        print("-" * 40)
        print(f"Total Messages: {throughput_stats['total_messages']}")
        print(f"Topics Monitored: {throughput_stats['topics_monitored']}")
        print(f"Avg Messages/Topic: {throughput_stats['avg_messages_per_topic']:.1f}")
        
        # Consumer Groups
        print(f"\nCONSUMER GROUPS")
        print("-" * 40)
        
        consumer_groups = self.get_consumer_groups()
        if consumer_groups:
            for group, details in consumer_groups.items():
                print(f"\nGroup: {group}")
                members = details.get('members', [])
                if members:
                    print(f"  Active consumers: {len(set(m.get('consumer_id', '') for m in members))}")
                    total_lag = sum(int(m.get('lag', 0)) for m in members if m.get('lag', '').isdigit())
                    print(f"  Total lag: {total_lag}")
                else:
                    print("  No active members")
        else:
            print("No consumer groups found")
        
        print("\n" + "=" * 60)
    
    def run_continuous_monitoring(self, interval=15):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.print_cluster_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    
    def test_cluster_connectivity(self):
        """Test basic cluster connectivity and health"""
        print("Testing Kafka cluster connectivity...")
        
        tests = [
            ("List topics", ['/opt/kafka/bin/kafka-topics.sh', '--bootstrap-server', 'localhost:9092', '--list']),
            ("Broker metadata", ['/opt/kafka/bin/kafka-broker-api-versions.sh', '--bootstrap-server', 'localhost:9092']),
        ]
        
        results = {}
        
        for test_name, command in tests:
            print(f"Running: {test_name}")
            result = self.run_kafka_command(command)
            
            if result is not None:
                results[test_name] = "PASS"
                print(f"  PASS")
            else:
                results[test_name] = "FAIL"
                print(f"  FAIL")
        
        print(f"\nConnectivity Test Results:")
        for test, status in results.items():
            print(f"  {test}: {status}")
        
        return all(status == "PASS" for status in results.values())

def main():
    print("Kafka Cluster Monitor")
    print("=" * 30)
    
    monitor = KafkaClusterMonitor()
    
    print("\n1. Show cluster dashboard")
    print("2. Test cluster connectivity") 
    print("3. Run continuous monitoring")
    
    choice = input("\nChoose option (1-3): ")
    
    try:
        if choice == "1":
            monitor.print_cluster_dashboard()
        
        elif choice == "2":
            monitor.test_cluster_connectivity()
        
        elif choice == "3":
            interval = int(input("Monitoring interval in seconds (default 15): ") or "15")
            monitor.run_continuous_monitoring(interval)
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()