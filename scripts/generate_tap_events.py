#!/usr/bin/env python3
"""
Generate synthetic tap events data for the bar management SaaS platform.

This script creates:
- 500,000 tap events from IoT-enabled beer tap devices
- Pour events with volume tracking
- Temperature and pressure readings
- Keg level monitoring
- Device health events
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
    """Load device data with location info."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.location_id, d.device_type, d.status,
                   l.customer_id
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            WHERE d.device_type = 'tap'
            ORDER BY d.id
        """)
        return [dict(zip(['id', 'location_id', 'device_type', 'status', 'customer_id'], row)) 
                for row in cursor.fetchall()]

def generate_tap_events(env_config):
    """Generate tap event data."""
    devices = load_devices()
    tap_devices = [d for d in devices if d['device_type'] == 'tap']
    events = []
    
    # Event types and their frequencies
    event_types = {
        'pour': 0.70,           # 70% - actual beer pours
        'temperature': 0.15,    # 15% - temperature readings
        'pressure': 0.10,       # 10% - pressure readings
        'keg_level': 0.04,      # 4% - keg level checks
        'cleaning': 0.01        # 1% - cleaning cycles
    }
    
    # Beer types with pour characteristics
    beer_types = [
        {'name': 'Lager', 'avg_pour_oz': 16, 'temp_f': 38, 'pressure_psi': 12},
        {'name': 'IPA', 'avg_pour_oz': 16, 'temp_f': 42, 'pressure_psi': 14},
        {'name': 'Stout', 'avg_pour_oz': 16, 'temp_f': 45, 'pressure_psi': 10},
        {'name': 'Pilsner', 'avg_pour_oz': 12, 'temp_f': 38, 'pressure_psi': 13},
        {'name': 'Wheat', 'avg_pour_oz': 16, 'temp_f': 40, 'pressure_psi': 12},
        {'name': 'Porter', 'avg_pour_oz': 16, 'temp_f': 44, 'pressure_psi': 11}
    ]
    
    # Time-based patterns
    def get_pour_probability(hour, day_of_week):
        """Get probability of pour based on time."""
        # Weekday patterns
        if day_of_week < 5:  # Monday-Friday
            if hour < 11:
                return 0.05
            elif hour < 14:
                return 0.3  # Lunch
            elif hour < 17:
                return 0.2
            elif hour < 20:
                return 0.7  # Happy hour
            elif hour < 23:
                return 0.5
            else:
                return 0.1
        else:  # Weekend
            if hour < 11:
                return 0.05
            elif hour < 14:
                return 0.4
            elif hour < 23:
                return 0.8  # Busy all day
            else:
                return 0.2
    
    # Generate events
    total_events = 500000
    events_per_device = total_events // len(tap_devices) if tap_devices else 0
    
    # Ensure we get enough events by increasing per-device count
    if len(tap_devices) > 0:
        events_per_device = max(events_per_device, 4100)  # At least 4100 per device
    
    for device in tap_devices:
        if device['status'] != 'online':
            # Offline devices generate fewer events
            device_events = events_per_device // 10
        else:
            device_events = events_per_device
        
        # Assign a beer type to this tap
        beer = random.choice(beer_types)
        
        # Track keg level for this device
        current_keg_level = 100.0  # Start with full keg
        keg_capacity_oz = 1984  # Standard 1/2 barrel keg
        
        # Generate events over last 30 days
        for i in range(device_events):
            # Random time in last 30 days
            days_ago = random.random() * 30
            event_time = datetime.now() - timedelta(days=days_ago)
            
            # Determine event type based on time and probability
            hour = event_time.hour
            day_of_week = event_time.weekday()
            
            # Choose event type
            rand_val = random.random()
            cumulative = 0
            event_type = 'pour'  # default
            
            for etype, prob in event_types.items():
                cumulative += prob
                if rand_val < cumulative:
                    event_type = etype
                    break
            
            # Adjust pour events based on time
            if event_type == 'pour':
                pour_prob = get_pour_probability(hour, day_of_week)
                if random.random() > pour_prob:
                    event_type = 'temperature'  # Convert to temperature reading instead
            
            # Generate event data based on type
            event_data = {}
            
            if event_type == 'pour':
                # Pour event
                pour_size = random.choice([8, 12, 16, 20, 24])  # Common pour sizes
                actual_pour = pour_size + random.uniform(-0.5, 0.5)  # Slight variance
                
                event_data = {
                    'pour_ounces': round(actual_pour, 2),
                    'pour_duration_seconds': round(actual_pour * 1.2 + random.uniform(-0.5, 0.5), 1),
                    'beer_type': beer['name'],
                    'temperature_f': beer['temp_f'] + random.uniform(-2, 2),
                    'foam_ratio': round(random.uniform(0.05, 0.20), 2)  # 5-20% foam
                }
                
                # Update keg level
                current_keg_level -= (actual_pour / keg_capacity_oz) * 100
                if current_keg_level < 0:
                    current_keg_level = 100.0  # New keg
                    
            elif event_type == 'temperature':
                # Temperature reading
                event_data = {
                    'temperature_f': beer['temp_f'] + random.uniform(-3, 3),
                    'target_temp_f': beer['temp_f'],
                    'is_in_range': True
                }
                
            elif event_type == 'pressure':
                # Pressure reading
                pressure = beer['pressure_psi'] + random.uniform(-1, 1)
                event_data = {
                    'pressure_psi': round(pressure, 1),
                    'target_pressure_psi': beer['pressure_psi'],
                    'is_in_range': abs(pressure - beer['pressure_psi']) < 2
                }
                
            elif event_type == 'keg_level':
                # Keg level check
                event_data = {
                    'keg_level_percent': round(current_keg_level, 1),
                    'estimated_pours_remaining': int((current_keg_level / 100) * keg_capacity_oz / 16),
                    'alert_low_level': current_keg_level < 15
                }
                
            elif event_type == 'cleaning':
                # Cleaning cycle
                event_data = {
                    'cleaning_type': random.choice(['quick_rinse', 'full_clean', 'sanitize']),
                    'duration_minutes': random.randint(5, 30),
                    'chemical_used': random.choice(['sanitizer_a', 'cleaner_b', 'rinse_only'])
                }
            
            event = {
                'id': str(uuid.uuid4()),
                'device_id': device['id'],
                'location_id': device['location_id'],
                'timestamp': event_time.isoformat(),
                'event_type': event_type,
                'status': 'completed' if event_type != 'cleaning' else 'in_progress',
                'metrics': json.dumps(event_data),
                'device_category': 'tap',
                'created_at': event_time.isoformat()
            }
            
            events.append(event)
    
    # Sort by timestamp
    events.sort(key=lambda x: x['timestamp'])
    
    return events[:500000]  # Ensure exactly 500,000

def save_tap_events_summary(events):
    """Save tap events summary for future reference."""
    summary = {
        'total_events': len(events),
        'unique_devices': len(set(e['device_id'] for e in events)),
        'events_by_type': {},
        'total_beer_poured_oz': 0,
        'avg_pour_size': 0,
        'peak_hours': {}
    }
    
    # Analyze events
    pour_events = []
    for event in events:
        event_type = event['event_type']
        summary['events_by_type'][event_type] = summary['events_by_type'].get(event_type, 0) + 1
        
        if event_type == 'pour':
            data = json.loads(event['metrics'])
            pour_events.append(data['pour_ounces'])
            summary['total_beer_poured_oz'] += data['pour_ounces']
        
        # Track hourly distribution
        hour = datetime.fromisoformat(event['timestamp']).hour
        summary['peak_hours'][hour] = summary['peak_hours'].get(hour, 0) + 1
    
    if pour_events:
        summary['avg_pour_size'] = sum(pour_events) / len(pour_events)
        summary['total_beer_poured_gallons'] = summary['total_beer_poured_oz'] / 128
    
    with open('data/tap_events_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved tap events summary to data/tap_events_summary.json")

def main():
    print("=== Generating Tap Events ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate tap events
    print("\nGenerating tap events...")
    events = generate_tap_events(env_config)
    print(f"✓ Generated {len(events)} tap events")
    
    # Statistics
    unique_devices = len(set(e['device_id'] for e in events))
    event_types = {}
    total_beer_oz = 0
    
    for event in events:
        event_type = event['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if event_type == 'pour':
            data = json.loads(event['metrics'])
            total_beer_oz += data['pour_ounces']
    
    print(f"\nTap Event Statistics:")
    print(f"  - Unique Devices: {unique_devices}")
    print(f"  - Events per Device: {len(events) / unique_devices:.0f}")
    
    print("\nEvent Type Distribution:")
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(events)) * 100
        print(f"  - {event_type}: {count:,} ({percentage:.1f}%)")
    
    if total_beer_oz > 0:
        print(f"\nBeer Pour Statistics:")
        print(f"  - Total Beer Poured: {total_beer_oz:,.0f} oz ({total_beer_oz/128:,.0f} gallons)")
        print(f"  - Average Pour Size: {total_beer_oz/event_types.get('pour', 1):.1f} oz")
        print(f"  - Estimated Revenue: ${total_beer_oz/16 * 6:.0f} (at $6/pint)")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('app_database_tap_events', events)
    
    # Save summary
    save_tap_events_summary(events)
    
    # Verify
    count = db_helper.get_row_count('app_database_tap_events')
    print(f"\n✓ Total tap events in database: {count:,}")

if __name__ == "__main__":
    main()