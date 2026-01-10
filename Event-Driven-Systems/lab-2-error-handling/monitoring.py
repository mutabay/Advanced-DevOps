import redis
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

class SystemMonitor:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.metrics = defaultdict(int)
        self.last_check = datetime.now()
    
    def get_stream_stats(self):
        """Get current stream statistics"""
        streams = [
            'ecommerce:orders',
            'ecommerce:payments',
            'retry:ecommerce:orders', 
            'retry:ecommerce:payments',
            'dlq:ecommerce:orders',
            'dlq:ecommerce:payments'
        ]
        
        stats = {}
        for stream in streams:
            try:
                length = self.client.xlen(stream)
                stats[stream] = length
            except:
                stats[stream] = 0
        
        return stats
    
    def get_consumer_group_stats(self):
        """Get consumer group information"""
        streams = ['ecommerce:orders', 'ecommerce:payments']
        group_name = 'error_handling_group'
        
        group_stats = {}
        for stream in streams:
            try:
                groups = self.client.xinfo_groups(stream)
                for group in groups:
                    if group['name'] == group_name:
                        pending = self.client.xpending(stream, group_name)
                        group_stats[stream] = {
                            'consumers': group['consumers'],
                            'pending': pending[0] if pending else 0,
                            'last_delivered': group.get('last-delivered-id', 'N/A')
                        }
            except:
                group_stats[stream] = {'consumers': 0, 'pending': 0, 'last_delivered': 'N/A'}
        
        return group_stats
    
    def calculate_error_rates(self, stats):
        """Calculate error rates based on DLQ vs main stream sizes"""
        rates = {}
        
        for main_stream in ['ecommerce:orders', 'ecommerce:payments']:
            dlq_stream = f"dlq:{main_stream}"
            retry_stream = f"retry:{main_stream}"
            
            main_count = stats.get(main_stream, 0)
            dlq_count = stats.get(dlq_stream, 0)
            retry_count = stats.get(retry_stream, 0)
            
            total_processed = main_count + dlq_count + retry_count
            if total_processed > 0:
                error_rate = (dlq_count / total_processed) * 100
                retry_rate = (retry_count / total_processed) * 100
            else:
                error_rate = 0
                retry_rate = 0
            
            rates[main_stream] = {
                'error_rate': round(error_rate, 2),
                'retry_rate': round(retry_rate, 2),
                'total_processed': total_processed
            }
        
        return rates
    
    def check_health(self, stats, group_stats, error_rates):
        """Determine system health status"""
        issues = []
        
        # Check for high DLQ counts
        for stream, count in stats.items():
            if 'dlq:' in stream and count > 10:
                issues.append(f"High DLQ count in {stream}: {count}")
        
        # Check for high error rates
        for stream, rates in error_rates.items():
            if rates['error_rate'] > 20:
                issues.append(f"High error rate in {stream}: {rates['error_rate']}%")
            if rates['retry_rate'] > 50:
                issues.append(f"High retry rate in {stream}: {rates['retry_rate']}%")
        
        # Check for stuck messages
        for stream, group in group_stats.items():
            if group['pending'] > 5:
                issues.append(f"High pending messages in {stream}: {group['pending']}")
        
        if not issues:
            return "HEALTHY", []
        elif len(issues) <= 2:
            return "WARNING", issues
        else:
            return "CRITICAL", issues
    
    def print_dashboard(self):
        """Print a real-time monitoring dashboard"""
        stats = self.get_stream_stats()
        group_stats = self.get_consumer_group_stats()
        error_rates = self.calculate_error_rates(stats)
        health_status, issues = self.check_health(stats, group_stats, error_rates)
        
        print(f"\n{'='*60}")
        print(f"EVENT SYSTEM MONITOR - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Health Status
        status_color = {"HEALTHY": "✓", "WARNING": "⚠", "CRITICAL": "✗"}
        print(f"\nSYSTEM HEALTH: {status_color.get(health_status, '?')} {health_status}")
        
        if issues:
            print("\nISSUES:")
            for issue in issues:
                print(f"  - {issue}")
        
        # Stream Statistics
        print(f"\nSTREAM STATISTICS:")
        print(f"{'Stream':<30} {'Messages':<10} {'Status'}")
        print("-" * 50)
        
        for stream, count in stats.items():
            status = "OK" if count < 100 else "HIGH"
            if 'dlq:' in stream and count > 0:
                status = "ALERT"
            print(f"{stream:<30} {count:<10} {status}")
        
        # Error Rates
        print(f"\nERROR RATES:")
        print(f"{'Stream':<25} {'Error%':<8} {'Retry%':<8} {'Total'}")
        print("-" * 50)
        
        for stream, rates in error_rates.items():
            print(f"{stream:<25} {rates['error_rate']:<8} {rates['retry_rate']:<8} {rates['total_processed']}")
        
        # Consumer Group Status
        print(f"\nCONSUMER GROUPS:")
        print(f"{'Stream':<25} {'Consumers':<10} {'Pending':<8}")
        print("-" * 45)
        
        for stream, group in group_stats.items():
            print(f"{stream:<25} {group['consumers']:<10} {group['pending']:<8}")
    
    def run_continuous_monitoring(self, interval=10):
        """Run continuous monitoring with specified interval"""
        try:
            while True:
                self.print_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n\nMonitoring stopped.")
    
    def export_metrics(self, filename=None):
        """Export current metrics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
        
        stats = self.get_stream_stats()
        group_stats = self.get_consumer_group_stats()
        error_rates = self.calculate_error_rates(stats)
        health_status, issues = self.check_health(stats, group_stats, error_rates)
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'health_status': health_status,
            'issues': issues,
            'stream_stats': stats,
            'consumer_groups': group_stats,
            'error_rates': error_rates
        }
        
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Metrics exported to {filename}")

def main():
    monitor = SystemMonitor()
    
    print("System Monitoring Options:")
    print("1. Show current dashboard")
    print("2. Run continuous monitoring")
    print("3. Export metrics to file")
    
    choice = input("Choose option (1-3): ")
    
    if choice == "1":
        monitor.print_dashboard()
    elif choice == "2":
        interval = int(input("Monitoring interval in seconds (default 10): ") or "10")
        monitor.run_continuous_monitoring(interval)
    elif choice == "3":
        monitor.export_metrics()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()