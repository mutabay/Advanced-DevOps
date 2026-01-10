import redis
import json
from datetime import datetime

class DLQMonitor:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def get_dlq_stats(self):
        dlq_streams = ['dlq:ecommerce:orders', 'dlq:ecommerce:payments']
        stats = {}
        
        for stream in dlq_streams:
            try:
                length = self.client.xlen(stream)
                stats[stream] = length
            except:
                stats[stream] = 0
                
        return stats
    
    def show_dlq_messages(self, stream_name, count=5):
        try:
            messages = self.client.xrange(stream_name, count=count)
            print(f"\n=== {stream_name} ===")
            for msg_id, fields in messages:
                print(f"ID: {msg_id}")
                print(f"Error: {fields.get('error_reason', 'Unknown')}")
                print(f"Event: {fields.get('event_type', 'Unknown')}")
                print("-" * 30)
        except Exception as e:
            print(f"Error reading {stream_name}: {e}")
    
    def replay_dlq_message(self, dlq_stream, message_id):
        # Move message back to main stream
        original_stream = dlq_stream.replace('dlq:', '')
        try:
            # Get message from DLQ
            messages = self.client.xrange(dlq_stream, min=message_id, max=message_id)
            if messages:
                _, fields = messages[0]
                # Remove DLQ metadata
                clean_fields = {k: v for k, v in fields.items() 
                              if not k.startswith('dlq_') and k != 'error_reason'}
                # Republish to main stream
                self.client.xadd(original_stream, clean_fields)
                print(f"Replayed message {message_id} to {original_stream}")
            else:
                print(f"Message {message_id} not found")
        except Exception as e:
            print(f"Error replaying message: {e}")

def main():
    monitor = DLQMonitor()
    
    # Show stats
    stats = monitor.get_dlq_stats()
    print("DLQ Statistics:")
    print("-" * 40)
    for stream, count in stats.items():
        print(f"{stream:25} | Messages: {count}")
    
    # Show DLQ messages
    for stream in stats.keys():
        if stats[stream] > 0:
            monitor.show_dlq_messages(stream)

if __name__ == "__main__":
    main()