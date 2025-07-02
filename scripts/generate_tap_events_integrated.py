#!/usr/bin/env python3
"""
Integrated tap events generator for deployment pipeline
Generates varied tap events for realistic device health scores
"""

import sys
import os
import json
import random
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

def should_truncate():
    """Check if we should auto-truncate in Docker environment"""
    if os.environ.get('DOCKER_ENV', 'false').lower() == 'true':
        return True
    response = input("Do you want to truncate and regenerate? (y/N): ")
    return response.lower() == 'y'

def generate_tap_events():
    """Generate tap events with varied patterns for realistic health scores"""
    print("Generating tap events with varied activity patterns...")
    
    # Get active tap devices directly from database
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.location_id, d.created_at, a.id as account_id, l.business_type
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            JOIN raw.app_database_accounts a ON l.customer_id = a.id
            WHERE d.device_type = 'tap_controller' 
            AND d.status = 'Online'
            AND a.status = 'active'
            ORDER BY RANDOM()
            LIMIT 25000
        """)
        devices = cursor.fetchall()
    
    if not devices:
        print("No active tap devices found!")
        return 0
    
    print(f"Found {len(devices)} active tap devices")
    
    # Reset tap events ID allocator
    id_allocator.reset('tap_events')
    
    # Generate events for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    batch_size = 10000
    batch_events = []
    total_inserted = 0
    
    for idx, device_data in enumerate(devices):
        device_id, location_id, created_at, account_id, business_type = device_data
        
        # Skip if device was created recently
        if created_at > start_date:
            continue
        
        # Vary activity patterns to create health score diversity
        pattern = idx % 12
        
        # Determine activity characteristics
        if pattern <= 2:  # 25% - Very active, consistent
            active_days = random.randint(25, 30)
            events_per_day = random.randint(80, 150)
        elif pattern <= 5:  # 25% - Active, mostly consistent
            active_days = random.randint(20, 25)
            events_per_day = random.randint(50, 80)
        elif pattern <= 8:  # 25% - Moderate activity
            active_days = random.randint(12, 20)
            events_per_day = random.randint(30, 50)
        elif pattern <= 10:  # 17% - Low activity
            active_days = random.randint(5, 12)
            events_per_day = random.randint(10, 30)
        else:  # 8% - Very low activity
            active_days = random.randint(1, 5)
            events_per_day = random.randint(5, 10)
        
        # Generate random active days
        all_days = [(start_date + timedelta(days=i)) for i in range(31)]
        active_days_list = random.sample(all_days, min(active_days, len(all_days)))
        
        for event_date in active_days_list:
            # Vary events throughout the day
            for _ in range(events_per_day):
                # Random time during business hours (weighted)
                hour_weights = [1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 6, 8, 8, 7, 6, 8, 10, 10, 8, 6, 4, 3, 2]
                hour = random.choices(range(24), weights=hour_weights)[0]
                
                event_time = event_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
                
                # Generate metrics with some variation
                pour_ounces = round(random.gauss(16, 3), 1)
                volume_ml = round(pour_ounces * 29.5735, 1)
                duration_seconds = round(random.gauss(8, 2), 1)
                flow_rate_ml_per_sec = round(volume_ml / duration_seconds if duration_seconds > 0 else 20, 1)
                
                # Temperature with occasional anomalies
                if random.random() < 0.95:  # Normal temperature
                    temperature_c = round(random.gauss(4, 1), 1)
                else:  # Anomaly
                    temperature_c = round(random.gauss(8, 3), 1)
                
                # Pressure with occasional issues
                if random.random() < 0.90:  # Normal pressure
                    pressure_psi = round(random.gauss(12, 1), 1)
                else:  # Pressure issue
                    pressure_psi = round(random.gauss(18, 5), 1)
                
                event = {
                    'id': id_allocator.get_next_id('tap_events'),
                    'device_id': device_id,
                    'location_id': location_id,
                    'timestamp': event_time,
                    'event_type': 'pour',
                    'status': 'completed',
                    'metrics': json.dumps({
                        'pour_ounces': pour_ounces,
                        'volume_ml': volume_ml,
                        'duration_seconds': duration_seconds,
                        'flow_rate_ml_per_sec': flow_rate_ml_per_sec,
                        'temperature_c': temperature_c,
                        'temperature_f': round(temperature_c * 9/5 + 32, 1),
                        'pressure_psi': pressure_psi
                    }),
                    'device_category': 'tap',
                    'created_at': event_time
                }
                
                batch_events.append(event)
                
                # Insert batch when full
                if len(batch_events) >= batch_size:
                    inserted = db_helper.bulk_insert('app_database_tap_events', batch_events)
                    total_inserted += inserted
                    print(f"  Inserted batch: {inserted} events (Total: {total_inserted})")
                    batch_events = []
    
    # Insert remaining events
    if batch_events:
        inserted = db_helper.bulk_insert('app_database_tap_events', batch_events)
        total_inserted += inserted
        print(f"  Inserted final batch: {inserted} events (Total: {total_inserted})")
    
    return total_inserted

def main():
    """Main execution function"""
    print("=" * 60)
    print("Tap Events Generation for TapFlow Analytics Platform")
    print("Integrated version with varied activity patterns")
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
    
    # Generate tap events
    total_events = generate_tap_events()
    
    if total_events == 0:
        print("\n⚠️  No events generated. Check that devices exist and accounts are active.")
        return
    
    # Verify
    count = db_helper.get_row_count('app_database_tap_events')
    print(f"\n✓ Verification: {count:,} tap events in database")
    
    # Show distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT device_id) as devices_with_events,
                COUNT(DISTINCT DATE(timestamp)) as unique_days,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM raw.app_database_tap_events
        """)
        stats = cursor.fetchone()
        
        print(f"\nEvent Statistics:")
        print(f"  Devices with events: {stats[0]:,}")
        print(f"  Unique days: {stats[1]}")
        print(f"  Date range: {stats[2].date()} to {stats[3].date()}")
    
    print(f"\n✅ Successfully generated {total_events:,} tap events!")

if __name__ == "__main__":
    main()