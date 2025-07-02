#!/usr/bin/env python3
"""
Quick tap events generator - generates minimal events for testing
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

def generate_quick_tap_events():
    """Generate minimal tap events for device health calculations"""
    print("Generating quick tap events...")
    
    # Get a sample of tap devices
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.location_id, d.created_at, a.id as account_id
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            JOIN raw.app_database_accounts a ON l.customer_id = a.id
            WHERE d.device_type = 'tap_controller' 
            AND d.status = 'Online'
            AND a.status = 'active'
            LIMIT 5000
        """)
        devices = cursor.fetchall()
    
    print(f"Found {len(devices)} devices to process")
    
    events = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Just last 7 days
    
    # Reset tap events ID
    id_allocator.reset('tap_events')
    
    for device in devices:
        device_id, location_id, created_at, account_id = device
        
        # Generate ~100 events per device over 7 days
        current_date = start_date
        while current_date <= end_date:
            # Generate 10-20 events per day
            num_events = random.randint(10, 20)
            
            for _ in range(num_events):
                event_time = current_date + timedelta(
                    hours=random.randint(9, 22),
                    minutes=random.randint(0, 59)
                )
                
                event = {
                    'id': id_allocator.get_next_id('tap_events'),
                    'device_id': device_id,
                    'location_id': location_id,
                    'timestamp': event_time,
                    'event_type': 'pour',
                    'status': 'completed',
                    'metrics': json.dumps({
                        'pour_ounces': round(random.uniform(12, 20), 1),
                        'duration_seconds': round(random.uniform(5, 12), 1),
                        'temperature_f': round(random.uniform(36, 40), 1)
                    }),
                    'device_category': 'tap',
                    'created_at': event_time
                }
                events.append(event)
            
            current_date += timedelta(days=1)
    
    return events

def main():
    print("Quick Tap Events Generation")
    print("=" * 40)
    
    # Truncate existing
    if db_helper.get_row_count('app_database_tap_events') > 0:
        db_helper.truncate_table('app_database_tap_events')
    
    # Generate events
    events = generate_quick_tap_events()
    print(f"Generated {len(events)} events")
    
    # Insert in batches
    batch_size = 10000
    total_inserted = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        inserted = db_helper.bulk_insert('app_database_tap_events', batch)
        total_inserted += inserted
        print(f"Inserted batch: {inserted} events")
    
    print(f"\n✅ Total inserted: {total_inserted} tap events")
    
    # Verify
    count = db_helper.get_row_count('app_database_tap_events')
    print(f"✓ Verification: {count} events in database")

if __name__ == "__main__":
    main()