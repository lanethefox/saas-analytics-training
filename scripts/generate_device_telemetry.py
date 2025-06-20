#!/usr/bin/env python3
"""
Generate synthetic device telemetry data for the bar management SaaS platform.

This script creates:
- 100,000 telemetry records from all device types
- CPU, memory, disk usage metrics
- Network connectivity stats
- Uptime and health scores
- Error logs and alerts
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_devices():
    """Load all devices with location info."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.location_id, d.device_type, d.status,
                   l.customer_id
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            ORDER BY d.id
        """)
        return [dict(zip(['id', 'location_id', 'device_type', 'status', 'customer_id'], row)) 
                for row in cursor.fetchall()]

def generate_device_telemetry(env_config):
    """Generate device telemetry data."""
    devices = load_devices()
    telemetry_records = []
    
    # Telemetry patterns by device type
    device_patterns = {
        'tap': {
            'cpu_base': 15,
            'memory_base': 30,
            'disk_base': 20,
            'network_kbps': 100,
            'error_rate': 0.02
        },
        'pos': {
            'cpu_base': 25,
            'memory_base': 45,
            'disk_base': 35,
            'network_kbps': 500,
            'error_rate': 0.03
        },
        'kiosk': {
            'cpu_base': 20,
            'memory_base': 40,
            'disk_base': 30,
            'network_kbps': 300,
            'error_rate': 0.025
        },
        'display': {
            'cpu_base': 10,
            'memory_base': 25,
            'disk_base': 15,
            'network_kbps': 200,
            'error_rate': 0.01
        }
    }
    
    # Common error types
    error_types = [
        'CONNECTION_TIMEOUT',
        'API_ERROR',
        'MEMORY_WARNING',
        'DISK_SPACE_LOW',
        'AUTHENTICATION_FAILED',
        'SENSOR_MALFUNCTION',
        'NETWORK_UNSTABLE',
        'FIRMWARE_UPDATE_FAILED'
    ]
    
    # Generate telemetry for each device
    total_records = 100000
    records_per_device = total_records // len(devices)
    
    for device in devices:
        device_type = device['device_type']
        pattern = device_patterns.get(device_type, device_patterns['pos'])
        
        # Device-specific characteristics
        if device['status'] == 'offline':
            # Offline devices have worse metrics
            pattern = {k: v * 1.5 if k != 'error_rate' else v * 3 for k, v in pattern.items()}
        elif device['status'] == 'maintenance':
            # Maintenance devices have irregular patterns
            pattern = {k: v * 1.2 if k != 'error_rate' else v * 2 for k, v in pattern.items()}
        
        # Generate telemetry over last 7 days
        for i in range(records_per_device):
            # Random time in last 7 days
            hours_ago = random.random() * 168  # 7 days * 24 hours
            timestamp = datetime.now() - timedelta(hours=hours_ago)
            
            # Time-based variations
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Peak hours have higher resource usage
            if 17 <= hour_of_day <= 22:  # Evening peak
                load_multiplier = 1.8
            elif 11 <= hour_of_day <= 14:  # Lunch peak
                load_multiplier = 1.5
            elif hour_of_day < 6:  # Night time
                load_multiplier = 0.5
            else:
                load_multiplier = 1.0
            
            # Weekend adjustment
            if day_of_week >= 5:  # Weekend
                load_multiplier *= 1.3
            
            # Generate metrics
            cpu_usage = max(0, min(100, pattern['cpu_base'] * load_multiplier + random.gauss(0, 10)))
            memory_usage = max(0, min(100, pattern['memory_base'] * load_multiplier + random.gauss(0, 8)))
            disk_usage = max(0, min(100, pattern['disk_base'] + random.gauss(0, 5)))  # Disk doesn't vary as much
            
            # Network metrics
            network_in = max(0, pattern['network_kbps'] * load_multiplier * random.uniform(0.8, 1.2))
            network_out = max(0, pattern['network_kbps'] * load_multiplier * random.uniform(0.5, 0.8))
            
            # Uptime (in seconds since last restart)
            if device['status'] == 'online':
                uptime_seconds = random.randint(86400, 2592000)  # 1 day to 30 days
            else:
                uptime_seconds = random.randint(0, 86400)  # Less than a day
            
            # Health score (0-100)
            health_factors = [
                100 - cpu_usage,
                100 - memory_usage,
                100 - disk_usage,
                100 if device['status'] == 'online' else 50,
                100 - (pattern['error_rate'] * 1000)
            ]
            health_score = sum(health_factors) / len(health_factors)
            
            # Error logs
            errors = []
            if random.random() < pattern['error_rate']:
                error_count = random.randint(1, 3)
                for _ in range(error_count):
                    errors.append({
                        'type': random.choice(error_types),
                        'severity': random.choice(['warning', 'error', 'critical']),
                        'message': fake.sentence(),
                        'timestamp': (timestamp - timedelta(minutes=random.randint(0, 60))).isoformat()
                    })
            
            # Temperature readings (for IoT devices)
            if device_type in ['tap', 'kiosk']:
                temperature_c = 25 + random.gauss(0, 5)  # Room temperature with variance
            else:
                temperature_c = 30 + random.gauss(0, 8)  # Higher for POS/display devices
            
            telemetry_data = {
                'cpu_usage_percent': round(cpu_usage, 2),
                'memory_usage_percent': round(memory_usage, 2),
                'disk_usage_percent': round(disk_usage, 2),
                'network_in_kbps': round(network_in, 2),
                'network_out_kbps': round(network_out, 2),
                'uptime_seconds': uptime_seconds,
                'health_score': round(health_score, 2),
                'temperature_celsius': round(temperature_c, 1),
                'errors': errors,
                'firmware_version': f"{device_type}_fw_v{random.choice(['2.1.0', '2.1.1', '2.2.0', '2.2.1'])}",
                'last_maintenance_hours_ago': random.randint(0, 720) if device['status'] == 'maintenance' else None
            }
            
            record = {
                'telemetry_id': str(uuid.uuid4()),
                'device_id': device['id'],
                'location_id': device['location_id'],
                'customer_id': device['customer_id'],
                'timestamp': timestamp.isoformat(),
                'metrics': json.dumps(telemetry_data),
                'device_type': device_type,
                'device_status': device['status'],
                'created_at': timestamp.isoformat()
            }
            
            telemetry_records.append(record)
    
    # Sort by timestamp
    telemetry_records.sort(key=lambda x: x['timestamp'])
    
    return telemetry_records[:100000]  # Ensure exactly 100,000

def save_telemetry_summary(records):
    """Save telemetry summary for future reference."""
    summary = {
        'total_records': len(records),
        'unique_devices': len(set(r['device_id'] for r in records)),
        'device_type_breakdown': {},
        'avg_health_score': 0,
        'error_count': 0,
        'critical_alerts': 0
    }
    
    health_scores = []
    
    for record in records:
        device_type = record['device_type']
        summary['device_type_breakdown'][device_type] = summary['device_type_breakdown'].get(device_type, 0) + 1
        
        metrics = json.loads(record['metrics'])
        health_scores.append(metrics['health_score'])
        
        if metrics.get('errors'):
            summary['error_count'] += len(metrics['errors'])
            for error in metrics['errors']:
                if error['severity'] == 'critical':
                    summary['critical_alerts'] += 1
    
    summary['avg_health_score'] = sum(health_scores) / len(health_scores)
    
    with open('data/device_telemetry_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved device telemetry summary to data/device_telemetry_summary.json")

def main():
    print("=== Generating Device Telemetry ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate telemetry
    print("\nGenerating device telemetry...")
    records = generate_device_telemetry(env_config)
    print(f"✓ Generated {len(records)} telemetry records")
    
    # Statistics
    unique_devices = len(set(r['device_id'] for r in records))
    device_types = {}
    total_errors = 0
    health_scores = []
    
    for record in records:
        device_type = record['device_type']
        device_types[device_type] = device_types.get(device_type, 0) + 1
        
        metrics = json.loads(record['metrics'])
        health_scores.append(metrics['health_score'])
        if metrics.get('errors'):
            total_errors += len(metrics['errors'])
    
    avg_health = sum(health_scores) / len(health_scores)
    
    print(f"\nTelemetry Statistics:")
    print(f"  - Unique Devices: {unique_devices}")
    print(f"  - Records per Device: {len(records) / unique_devices:.0f}")
    print(f"  - Average Health Score: {avg_health:.1f}/100")
    print(f"  - Total Errors Logged: {total_errors:,}")
    
    print("\nDevice Type Distribution:")
    for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(records)) * 100
        print(f"  - {device_type}: {count:,} ({percentage:.1f}%)")
    
    # Sample metrics
    sample_record = random.choice(records)
    sample_metrics = json.loads(sample_record['metrics'])
    print(f"\nSample Telemetry Record:")
    print(f"  - Device ID: {sample_record['device_id']}")
    print(f"  - CPU Usage: {sample_metrics['cpu_usage_percent']}%")
    print(f"  - Memory Usage: {sample_metrics['memory_usage_percent']}%")
    print(f"  - Health Score: {sample_metrics['health_score']}")
    print(f"  - Uptime: {sample_metrics['uptime_seconds'] / 3600:.1f} hours")
    
    # Save to file since table doesn't exist
    print("\nSaving telemetry data to file...")
    with open('data/device_telemetry_records.json', 'w') as f:
        # Save a subset to avoid huge file
        json.dump(records[:1000], f, indent=2)
    print("✓ Saved 1000 sample records to data/device_telemetry_records.json")
    
    # Save summary
    save_telemetry_summary(records)
    
    print(f"\n✓ Generated {len(records):,} telemetry records")
    print("Note: Telemetry table doesn't exist in database, data saved to file instead")

if __name__ == "__main__":
    main()