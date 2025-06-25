#!/usr/bin/env python3
"""
Generate deterministic tap events data for the TapFlow Analytics platform.

This module creates tap events with:
- Temporal consistency with device creation dates
- Respect for account active/inactive status
- Realistic patterns based on business hours and days
- Sequential IDs within reserved range
- Proper foreign key relationships
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

import os

def should_truncate():
    """Check if we should auto-truncate in Docker environment"""
    if os.environ.get('DOCKER_ENV', 'false').lower() == 'true':
        return True
    response = input("Do you want to truncate and regenerate? (y/N): ")
    return response.lower() == 'y'

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

# Initialize Faker with seed from config
fake = Faker()

# Event type distribution
EVENT_TYPES = {
    'pour': 0.70,           # 70% - actual beer pours
    'temperature': 0.15,    # 15% - temperature readings
    'pressure': 0.08,       # 8% - pressure readings
    'keg_level': 0.04,      # 4% - keg level checks
    'cleaning': 0.02,       # 2% - cleaning cycles
    'health_check': 0.01    # 1% - device health checks
}

def load_device_mappings():
    """Load devices and related data from mapping files"""
    # Load devices
    device_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_devices.json'
    )
    with open(device_file, 'r') as f:
        devices = json.load(f)
    
    # Load accounts to check active status
    account_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    with open(account_file, 'r') as f:
        accounts = json.load(f)
    
    # Create account lookup
    account_lookup = {acc['id']: acc for acc in accounts}
    
    # Filter devices - only tap devices from active accounts
    tap_devices = []
    for device in devices:
        if (device['device_type'] == 'tap' and 
            device['status'] == 'Online' and
            account_lookup[device['customer_id']]['is_active']):
            # Convert dates
            device['created_at'] = datetime.fromisoformat(device['created_at'])
            device['account_created'] = datetime.fromisoformat(
                account_lookup[device['customer_id']]['created_at']
            )
            tap_devices.append(device)
    
    return tap_devices

def get_pour_frequency(hour, day_of_week):
    """Get expected pours per hour based on time and day"""
    # Weekday vs weekend
    is_weekend = day_of_week >= 5
    
    # Base rates by hour
    if 17 <= hour <= 23:  # Peak evening hours
        base_rate = 30 if is_weekend else 20
    elif 14 <= hour <= 17:  # Happy hour
        base_rate = 25 if is_weekend else 15
    elif 11 <= hour <= 14:  # Lunch
        base_rate = 15 if is_weekend else 10
    elif 9 <= hour <= 11:   # Morning
        base_rate = 5
    elif hour >= 0 and hour < 2:  # Late night
        base_rate = 10 if is_weekend else 5
    else:  # Closed/minimal hours
        base_rate = 1
    
    return base_rate

def generate_pour_event(device, event_time):
    """Generate a beer pour event"""
    return {
        'pour_ounces': round(random.gauss(16, 4), 1),  # Average pint with variation
        'duration_seconds': round(random.gauss(8, 2), 1),
        'beer_type': random.choice(['Lager', 'IPA', 'Stout', 'Wheat', 'Pilsner', 'Ale']),
        'keg_id': f"keg_{device['location_id']}_{random.randint(1, 6)}",
        'temperature_f': round(random.gauss(38, 2), 1),
        'flow_rate': round(random.uniform(0.8, 1.5), 2)
    }

def generate_temperature_event(device, event_time):
    """Generate a temperature reading event"""
    return {
        'temperature_f': round(random.gauss(38, 3), 1),
        'target_temp_f': 38,
        'ambient_temp_f': round(random.gauss(70, 5), 1),
        'cooling_active': random.choice([True, False])
    }

def generate_pressure_event(device, event_time):
    """Generate a pressure reading event"""
    return {
        'pressure_psi': round(random.gauss(12, 1), 1),
        'target_psi': 12,
        'co2_level': round(random.uniform(0.1, 1.0), 2),
        'alert': 'low_pressure' if random.random() < 0.05 else None
    }

def generate_keg_level_event(device, event_time):
    """Generate a keg level reading event"""
    return {
        'keg_id': f"keg_{device['location_id']}_{random.randint(1, 6)}",
        'level_percent': round(random.uniform(5, 95), 1),
        'volume_remaining_oz': round(random.uniform(100, 1800), 0),
        'estimated_pours_remaining': random.randint(5, 100)
    }

def generate_cleaning_event(device, event_time):
    """Generate a cleaning cycle event"""
    return {
        'cleaning_type': random.choice(['rinse', 'sanitize', 'deep_clean']),
        'duration_minutes': random.randint(5, 30),
        'chemical_used': random.choice(['sanitizer_a', 'cleaner_b', 'rinse_aid']),
        'operator_id': f"emp_{random.randint(1000, 9999)}"
    }

def generate_health_check_event(device, event_time):
    """Generate a device health check event"""
    uptime_hours = int((event_time - device['created_at']).total_seconds() / 3600)
    return {
        'status': random.choices(['healthy', 'warning', 'error'], weights=[0.9, 0.08, 0.02])[0],
        'uptime_hours': min(uptime_hours, 8760),  # Cap at 1 year
        'error_count': random.randint(0, 5),
        'last_maintenance': (event_time - timedelta(days=random.randint(1, 90))).isoformat(),
        'firmware_version': f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 99)}"
    }

def generate_tap_events():
    """Generate deterministic tap event data"""
    # Load device mappings
    devices = load_device_mappings()
    
    if not devices:
        print("No active tap devices found!")
        return []
    
    print(f"Generating events for {len(devices)} active tap devices...")
    
    events = []
    time_config = config.config['simulation']['time_range']
    end_date = datetime.fromisoformat(time_config['end'])
    
    # Generate events for each device
    for device in devices:
        # Start from device creation or configured start, whichever is later
        device_start = max(
            device['created_at'] + timedelta(days=1),  # Day after installation
            datetime.fromisoformat(time_config['start'])
        )
        
        # Skip if device was created after end date
        if device_start > end_date:
            continue
        
        # Generate events for each day
        current_date = device_start
        while current_date <= end_date:
            # Get day of week (0=Monday, 6=Sunday)
            day_of_week = current_date.weekday()
            
            # Skip some days for maintenance/closure (5% chance)
            if random.random() < 0.05:
                current_date += timedelta(days=1)
                continue
            
            # Generate events throughout the day
            for hour in range(24):
                # Get expected pour frequency
                pour_freq = get_pour_frequency(hour, day_of_week)
                
                # Generate pour events
                num_pours = random.poisson(pour_freq)
                for _ in range(num_pours):
                    # Random minute within the hour
                    event_time = current_date.replace(hour=hour) + timedelta(
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59)
                    )
                    
                    # Skip if beyond end date
                    if event_time > end_date:
                        continue
                    
                    event_id = id_allocator.get_next_id('tap_events')
                    event = {
                        'id': event_id,
                        'device_id': device['id'],
                        'location_id': device['location_id'],
                        'timestamp': event_time,
                        'event_type': 'pour',
                        'status': 'completed',
                        'metrics': json.dumps(generate_pour_event(device, event_time)),
                        'device_category': 'tap',
                        'created_at': event_time
                    }
                    events.append(event)
                
                # Generate other event types with lower frequency
                # Temperature readings every 4 hours
                if hour % 4 == 0 and random.random() < 0.9:
                    event_time = current_date.replace(hour=hour) + timedelta(
                        minutes=random.randint(0, 59)
                    )
                    if event_time <= end_date:
                        event_id = id_allocator.get_next_id('tap_events')
                        event = {
                            'id': event_id,
                            'device_id': device['id'],
                            'location_id': device['location_id'],
                            'timestamp': event_time,
                            'event_type': 'temperature',
                            'status': 'completed',
                            'metrics': json.dumps(generate_temperature_event(device, event_time)),
                            'device_category': 'tap',
                            'created_at': event_time
                        }
                        events.append(event)
                
                # Pressure readings twice daily
                if hour in [8, 20] and random.random() < 0.8:
                    event_time = current_date.replace(hour=hour) + timedelta(
                        minutes=random.randint(0, 30)
                    )
                    if event_time <= end_date:
                        event_id = id_allocator.get_next_id('tap_events')
                        event = {
                            'id': event_id,
                            'device_id': device['id'],
                            'location_id': device['location_id'],
                            'timestamp': event_time,
                            'event_type': 'pressure',
                            'status': 'completed',
                            'metrics': json.dumps(generate_pressure_event(device, event_time)),
                            'device_category': 'tap',
                            'created_at': event_time
                        }
                        events.append(event)
                
                # Keg level checks once daily
                if hour == 6 and random.random() < 0.9:
                    event_time = current_date.replace(hour=hour) + timedelta(
                        minutes=random.randint(0, 30)
                    )
                    if event_time <= end_date:
                        event_id = id_allocator.get_next_id('tap_events')
                        event = {
                            'id': event_id,
                            'device_id': device['id'],
                            'location_id': device['location_id'],
                            'timestamp': event_time,
                            'event_type': 'keg_level',
                            'status': 'completed',
                            'metrics': json.dumps(generate_keg_level_event(device, event_time)),
                            'device_category': 'tap',
                            'created_at': event_time
                        }
                        events.append(event)
            
            # Weekly cleaning (Sunday mornings)
            if day_of_week == 6 and random.random() < 0.85:
                event_time = current_date.replace(hour=5) + timedelta(
                    minutes=random.randint(0, 120)
                )
                if event_time <= end_date:
                    event_id = id_allocator.get_next_id('tap_events')
                    event = {
                        'id': event_id,
                        'device_id': device['id'],
                        'location_id': device['location_id'],
                        'timestamp': event_time,
                        'event_type': 'cleaning',
                        'status': 'completed',
                        'metrics': json.dumps(generate_cleaning_event(device, event_time)),
                        'device_category': 'tap',
                        'created_at': event_time
                    }
                    events.append(event)
            
            # Daily health check
            if random.random() < 0.95:
                event_time = current_date.replace(hour=3) + timedelta(
                    minutes=random.randint(0, 30)
                )
                if event_time <= end_date:
                    event_id = id_allocator.get_next_id('tap_events')
                    event = {
                        'id': event_id,
                        'device_id': device['id'],
                        'location_id': device['location_id'],
                        'timestamp': event_time,
                        'event_type': 'health_check',
                        'status': 'completed',
                        'metrics': json.dumps(generate_health_check_event(device, event_time)),
                        'device_category': 'tap',
                        'created_at': event_time
                    }
                    events.append(event)
            
            current_date += timedelta(days=1)
    
    # Sort events by timestamp for realistic ordering
    events.sort(key=lambda x: x['timestamp'])
    
    print(f"  Generated {len(events)} total events")
    print(f"  Event types distribution:")
    event_type_counts = {}
    for event in events:
        event_type_counts[event['event_type']] = event_type_counts.get(event['event_type'], 0) + 1
    for event_type, count in sorted(event_type_counts.items()):
        print(f"    {event_type}: {count} ({count/len(events)*100:.1f}%)")
    
    return events

def insert_tap_events(events):
    """Insert tap events into the database in batches"""
    print(f"\nInserting {len(events)} tap events into database...")
    
    # Convert timestamps for database
    for event in events:
        event['timestamp'] = event['timestamp']
        event['created_at'] = event['created_at']
    
    # Insert in batches of 10000
    batch_size = 10000
    total_inserted = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        inserted = db_helper.bulk_insert('app_database_tap_events', batch)
        total_inserted += inserted
        print(f"  Inserted batch {i//batch_size + 1}/{(len(events) + batch_size - 1)//batch_size}: {inserted} events")
    
    return total_inserted

def save_tap_events_summary(events):
    """Save tap events summary for reference"""
    summary_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'tap_events_summary.json'
    )
    
    # Calculate summary statistics
    device_event_counts = {}
    event_type_counts = {}
    daily_counts = {}
    
    for event in events:
        # Device counts
        device_event_counts[event['device_id']] = device_event_counts.get(event['device_id'], 0) + 1
        
        # Event type counts
        event_type_counts[event['event_type']] = event_type_counts.get(event['event_type'], 0) + 1
        
        # Daily counts
        date_str = event['timestamp'].date().isoformat()
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    summary = {
        'total_events': len(events),
        'unique_devices': len(device_event_counts),
        'event_types': event_type_counts,
        'avg_events_per_device': sum(device_event_counts.values()) / len(device_event_counts) if device_event_counts else 0,
        'avg_events_per_day': sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0,
        'date_range': {
            'start': min(event['timestamp'] for event in events).isoformat() if events else None,
            'end': max(event['timestamp'] for event in events).isoformat() if events else None
        },
        'generation_timestamp': datetime.now().isoformat()
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Saved tap events summary to {summary_file}")

def verify_tap_events():
    """Verify the inserted tap events"""
    count = db_helper.get_row_count('app_database_tap_events')
    print(f"\n✓ Verification: {count} tap events in database")
    
    # Show event type distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT event_type, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_tap_events
            GROUP BY event_type
            ORDER BY count DESC
        """)
        event_dist = cursor.fetchall()
        
        print("\nEvent type distribution:")
        for row in event_dist:
            print(f"  {row[0]}: {row[1]:,} ({row[2]}%)")
        
        # Show daily average
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT DATE(timestamp)) as days,
                COUNT(*) as total_events,
                ROUND(COUNT(*)::numeric / COUNT(DISTINCT DATE(timestamp)), 1) as avg_per_day
            FROM raw.app_database_tap_events
        """)
        daily_stats = cursor.fetchone()
        
        print(f"\nDaily statistics:")
        print(f"  Total days: {daily_stats[0]}")
        print(f"  Average events per day: {daily_stats[2]:,.1f}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Tap Events Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if tap events already exist
    existing_count = db_helper.get_row_count('app_database_tap_events')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} tap events already exist")
        if should_truncate():
            db_helper.truncate_table('app_database_tap_events')
        else:
            print("Aborting...")
            return
    
    # Reset ID allocator for tap events
    id_allocator.current_ids['tap_events'] = 1
    
    # Generate tap events
    events = generate_tap_events()
    
    if not events:
        print("\n⚠️  No events generated. Check that devices exist and accounts are active.")
        return
    
    # Save summary
    save_tap_events_summary(events)
    
    # Insert into database
    inserted = insert_tap_events(events)
    
    # Verify
    verify_tap_events()
    
    print(f"\n✅ Successfully generated {inserted:,} tap events!")

if __name__ == "__main__":
    main()