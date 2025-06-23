#!/usr/bin/env python3
"""
Generate synthetic tap events data for the bar management SaaS platform.

This script creates:
- Tap events from IoT-enabled beer tap devices (based on environment scale)
- Pour events with volume tracking
- Temperature and pressure readings
- Keg level monitoring
- Device health events

Now with chunked generation for efficient handling of large datasets.
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
from scripts.environment_config import current_env
from scripts.chunked_generation import ChunkedGenerator, calculate_optimal_chunk_size

fake = Faker()
Faker.seed(42)
random.seed(42)

# Global variables for chunked generation
DEVICES = []
START_DATE = None
END_DATE = None
EVENT_TYPES = {
    'pour': 0.70,           # 70% - actual beer pours
    'temperature': 0.15,    # 15% - temperature readings
    'pressure': 0.08,       # 8% - pressure readings
    'keg_level': 0.04,      # 4% - keg level checks
    'cleaning': 0.02,       # 2% - cleaning cycles
    'health_check': 0.01    # 1% - device health checks
}

def load_devices():
    """Load device data with location info."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.location_id, d.device_type, d.status,
                   l.customer_id
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            WHERE d.device_type = 'tap'
            AND d.status = 'online'
            ORDER BY d.id
        """)
        return [dict(zip(['id', 'location_id', 'device_type', 'status', 'customer_id'], row)) 
                for row in cursor.fetchall()]

def generate_pour_event(device, event_time):
    """Generate a beer pour event."""
    return {
        'pour_ounces': round(random.gauss(16, 4), 1),  # Average pint with variation
        'duration_seconds': round(random.gauss(8, 2), 1),
        'beer_type': random.choice(['Lager', 'IPA', 'Stout', 'Wheat', 'Pilsner', 'Ale']),
        'keg_id': f"keg_{device['location_id']}_{random.randint(1, 6)}",
        'temperature_f': round(random.gauss(38, 2), 1),
        'flow_rate': round(random.uniform(0.8, 1.5), 2)
    }

def generate_temperature_event(device, event_time):
    """Generate a temperature reading event."""
    return {
        'temperature_f': round(random.gauss(38, 3), 1),
        'target_temp_f': 38,
        'ambient_temp_f': round(random.gauss(70, 5), 1),
        'cooling_active': random.choice([True, False])
    }

def generate_pressure_event(device, event_time):
    """Generate a pressure reading event."""
    return {
        'pressure_psi': round(random.gauss(12, 1), 1),
        'target_psi': 12,
        'co2_level': round(random.uniform(0.1, 1.0), 2),
        'alert': 'low_pressure' if random.random() < 0.05 else None
    }

def generate_keg_level_event(device, event_time):
    """Generate a keg level reading event."""
    return {
        'keg_id': f"keg_{device['location_id']}_{random.randint(1, 6)}",
        'level_percent': round(random.uniform(5, 95), 1),
        'volume_remaining_oz': round(random.uniform(100, 1800), 0),
        'estimated_pours_remaining': random.randint(5, 100)
    }

def generate_cleaning_event(device, event_time):
    """Generate a cleaning cycle event."""
    return {
        'cleaning_type': random.choice(['rinse', 'sanitize', 'deep_clean']),
        'duration_minutes': random.randint(5, 30),
        'chemical_used': random.choice(['sanitizer_a', 'cleaner_b', 'rinse_aid']),
        'operator_id': f"emp_{random.randint(1000, 9999)}"
    }

def generate_health_check_event(device, event_time):
    """Generate a device health check event."""
    return {
        'status': random.choices(['healthy', 'warning', 'error'], weights=[0.9, 0.08, 0.02])[0],
        'uptime_hours': random.randint(1, 720),
        'error_count': random.randint(0, 5),
        'last_maintenance': (event_time - timedelta(days=random.randint(1, 90))).isoformat(),
        'firmware_version': f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 99)}"
    }

def generate_single_tap_event(record_index):
    """Generate a single tap event for chunked generation."""
    global DEVICES, START_DATE, END_DATE
    
    # Select random device
    device = random.choice(DEVICES)
    
    # Generate random timestamp within range
    time_range = (END_DATE - START_DATE).total_seconds()
    random_seconds = random.random() * time_range
    event_time = START_DATE + timedelta(seconds=random_seconds)
    
    # Add time-based patterns
    hour = event_time.hour
    if 17 <= hour <= 23:  # Peak hours (5 PM - 11 PM)
        pour_weight = 0.85
    elif 11 <= hour <= 14:  # Lunch hours
        pour_weight = 0.75
    else:
        pour_weight = 0.50
    
    # Adjust event type probabilities
    adjusted_weights = EVENT_TYPES.copy()
    if hour >= 17:  # More pours during peak
        adjusted_weights['pour'] = pour_weight
    
    # Select event type
    event_type = random.choices(
        list(adjusted_weights.keys()),
        list(adjusted_weights.values())
    )[0]
    
    # Generate event data based on type
    event_generators = {
        'pour': generate_pour_event,
        'temperature': generate_temperature_event,
        'pressure': generate_pressure_event,
        'keg_level': generate_keg_level_event,
        'cleaning': generate_cleaning_event,
        'health_check': generate_health_check_event
    }
    
    event_data = event_generators[event_type](device, event_time)
    
    # Create event record
    event = {
        'id': str(uuid.uuid4()),
        'device_id': device['id'],
        'location_id': device['location_id'],
        'customer_id': device['customer_id'],
        'timestamp': event_time,
        'event_type': event_type,
        'status': 'completed' if event_type != 'cleaning' else 'in_progress',
        'metrics': json.dumps(event_data),
        'device_category': 'tap',
        'created_at': event_time
    }
    
    return event

def insert_tap_events_batch(events):
    """Insert a batch of tap events into the database."""
    return db_helper.bulk_insert('app_database_tap_events', events)

def save_tap_events_summary(total_events, devices_used):
    """Save tap events summary for future reference."""
    summary = {
        'total_events': total_events,
        'unique_devices': len(devices_used),
        'environment': current_env.name,
        'tap_events_expected': current_env.tap_events,
        'generation_complete': True,
        'timestamp': datetime.now().isoformat()
    }
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    with open('data/tap_events_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n✓ Saved tap events summary to data/tap_events_summary.json")

def main():
    print("=" * 60)
    print("Tap Events Generation (Chunked)")
    print(f"Environment: {current_env.name}")
    print(f"Target: {current_env.tap_events:,} events")
    print("=" * 60)
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Check existing data
    existing_count = db_helper.get_row_count('app_database_tap_events')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} tap events already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_tap_events')
        else:
            print("Aborting...")
            return
    
    # Load devices globally
    global DEVICES, START_DATE, END_DATE
    print("\nLoading tap devices...")
    DEVICES = load_devices()
    
    if not DEVICES:
        print("❌ No tap devices found. Please generate devices first.")
        return
    
    print(f"✓ Loaded {len(DEVICES):,} tap devices")
    
    # Set date range (last 30 days)
    END_DATE = datetime.now()
    START_DATE = END_DATE - timedelta(days=30)
    
    # Calculate optimal chunk size (tap events are small, ~200 bytes each)
    chunk_size = calculate_optimal_chunk_size(
        total_records=current_env.tap_events,
        record_size_bytes=200,
        max_memory_mb=100
    )
    
    # Create chunked generator
    generator = ChunkedGenerator(
        generator_name="tap_events",
        total_records=current_env.tap_events,
        chunk_size=chunk_size
    )
    
    # Generate events in chunks
    total_generated = generator.generate_chunks(
        record_generator=generate_single_tap_event,
        insert_function=insert_tap_events_batch,
        resume=True
    )
    
    # Save summary
    devices_used = set(d['id'] for d in DEVICES)
    save_tap_events_summary(total_generated, devices_used)
    
    # Verify
    final_count = db_helper.get_row_count('app_database_tap_events')
    print(f"\n✓ Verification: {final_count:,} tap events in database")
    
    # Show sample statistics
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                event_type,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_tap_events
            GROUP BY event_type
            ORDER BY count DESC
        """)
        event_dist = cursor.fetchall()
        
        print("\nEvent Type Distribution:")
        for row in event_dist:
            print(f"  {row['event_type']}: {row['count']:,} ({row['percentage']}%)")
        
        # Pour statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as pour_count,
                SUM((metrics->>'pour_ounces')::float) as total_ounces
            FROM raw.app_database_tap_events
            WHERE event_type = 'pour'
        """)
        pour_stats = cursor.fetchone()
        
        if pour_stats['pour_count'] > 0:
            total_oz = pour_stats['total_ounces']
            print(f"\nPour Statistics:")
            print(f"  Total Pours: {pour_stats['pour_count']:,}")
            print(f"  Total Beer: {total_oz:,.0f} oz ({total_oz/128:,.0f} gallons)")
            print(f"  Average Pour: {total_oz/pour_stats['pour_count']:.1f} oz")
            print(f"  Estimated Revenue: ${total_oz/16 * 6:,.0f} (at $6/pint)")

if __name__ == "__main__":
    main()