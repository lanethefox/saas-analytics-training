#!/usr/bin/env python3
"""
Add serial numbers to all devices.

This script:
- Generates unique serial numbers for each device type
- Follows realistic serial number patterns
- Updates the devices table with serial number data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
import random
import string
from datetime import datetime, timedelta

# Serial number patterns by device type
SERIAL_PATTERNS = {
    'tap': {
        'prefix': 'TAP',
        'manufacturer_codes': ['BR', 'KG', 'DR'],  # BeerRight, KegMaster, DraftPro
        'year_format': True,
        'length': 8
    },
    'controller': {
        'prefix': 'CTL',
        'manufacturer_codes': ['SM', 'TC', 'IO'],  # SmartControl, TechCore, IOTech
        'year_format': True,
        'length': 8
    },
    'sensor': {
        'prefix': 'SNS',
        'manufacturer_codes': ['TM', 'EN', 'PR'],  # TempMaster, EnviroNet, ProSense
        'year_format': True,
        'length': 8
    },
    'display': {
        'prefix': 'DSP',
        'manufacturer_codes': ['VW', 'SC', 'DG'],  # ViewTech, ScreenCo, DigiDisplay
        'year_format': False,
        'length': 10
    },
    'pos': {
        'prefix': 'POS',
        'manufacturer_codes': ['SQ', 'CL', 'RP'],  # Like Square, Clover, RetailPro
        'year_format': False,
        'length': 12
    },
    'kiosk': {
        'prefix': 'KSK',
        'manufacturer_codes': ['TS', 'UI', 'KT'],  # TouchSystems, UITech, KioskTech
        'year_format': True,
        'length': 10
    }
}

def generate_serial_number(device_type, device_id, created_date):
    """Generate a serial number for a device."""
    pattern = SERIAL_PATTERNS.get(device_type, SERIAL_PATTERNS['controller'])
    
    # Start with prefix and manufacturer code
    manufacturer = random.choice(pattern['manufacturer_codes'])
    serial = f"{pattern['prefix']}-{manufacturer}"
    
    # Add year if applicable
    if pattern['year_format']:
        year = created_date.year % 100  # Last 2 digits of year
        week = created_date.isocalendar()[1]  # Week number
        serial += f"{year:02d}{week:02d}"
    
    # Add unique identifier
    remaining_length = pattern['length'] - len(serial.replace('-', ''))
    
    # Use a combination of device ID and random chars
    id_part = str(device_id).zfill(4)[-4:]  # Last 4 digits of ID
    random_length = max(1, remaining_length - len(id_part))
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random_length))
    
    serial += f"-{id_part}{random_part}"
    
    return serial

def add_serial_number_column():
    """Add serial_number column if it doesn't exist."""
    with db_helper.config.get_cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_devices'
            AND column_name = 'serial_number'
        """)
        
        if cursor.rowcount == 0:
            print("Adding serial_number column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_devices 
                ADD COLUMN serial_number VARCHAR(50) UNIQUE
            """)
            cursor.connection.commit()
            return True
        return False

def update_device_serial_numbers():
    """Update all devices with serial numbers."""
    with db_helper.config.get_cursor() as cursor:
        # Get all devices
        cursor.execute("""
            SELECT id, device_type, created_at
            FROM raw.app_database_devices
            ORDER BY id
        """)
        devices = cursor.fetchall()
        
        print(f"Generating serial numbers for {len(devices)} devices...")
        
        # Track generated serials to ensure uniqueness
        used_serials = set()
        updates = []
        type_counts = {}
        
        for device_id, device_type, created_at in devices:
            # Generate unique serial
            serial = None
            attempts = 0
            while attempts < 10:
                serial = generate_serial_number(device_type, device_id, created_at)
                if serial not in used_serials:
                    used_serials.add(serial)
                    break
                attempts += 1
            
            if serial:
                updates.append((serial, device_id))
                type_counts[device_type] = type_counts.get(device_type, 0) + 1
        
        # Batch update
        cursor.executemany("""
            UPDATE raw.app_database_devices
            SET serial_number = %s
            WHERE id = %s
        """, updates)
        
        cursor.connection.commit()
        
        return type_counts

def save_serial_number_summary():
    """Save summary of serial number distribution."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT device_type, 
                   COUNT(*) as device_count,
                   COUNT(serial_number) as with_serial,
                   SUBSTRING(serial_number FROM 1 FOR 3) as prefix,
                   COUNT(DISTINCT SUBSTRING(serial_number FROM 5 FOR 2)) as manufacturer_variants
            FROM raw.app_database_devices
            GROUP BY device_type, SUBSTRING(serial_number FROM 1 FOR 3)
            ORDER BY device_count DESC
        """)
        
        device_data = []
        for row in cursor.fetchall():
            device_data.append({
                'device_type': row[0],
                'device_count': row[1],
                'with_serial_number': row[2],
                'serial_prefix': row[3],
                'manufacturer_variants': row[4]
            })
        
        # Get sample serials
        cursor.execute("""
            SELECT device_type, serial_number
            FROM raw.app_database_devices
            WHERE serial_number IS NOT NULL
            ORDER BY device_type, id
            LIMIT 20
        """)
        
        samples = {}
        for device_type, serial in cursor.fetchall():
            if device_type not in samples:
                samples[device_type] = []
            if len(samples[device_type]) < 3:
                samples[device_type].append(serial)
        
        summary = {
            'total_devices': sum(d['device_count'] for d in device_data),
            'device_type_summary': device_data,
            'serial_patterns': SERIAL_PATTERNS,
            'sample_serials': samples
        }
        
        with open('data/device_serial_numbers_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✓ Saved serial number summary to data/device_serial_numbers_summary.json")

def main():
    print("=== Adding Device Serial Numbers ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Add serial_number column if needed
    column_added = add_serial_number_column()
    if column_added:
        print("✓ Added serial_number column to devices table")
    
    # Update serial numbers
    print("\nGenerating serial numbers...")
    type_counts = update_device_serial_numbers()
    
    print("\nSerial numbers generated by type:")
    for device_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {device_type}: {count} devices")
    
    # Save summary
    save_serial_number_summary()
    
    # Show samples
    with db_helper.config.get_cursor() as cursor:
        print("\nSample serial numbers:")
        for device_type in ['tap', 'pos', 'controller', 'sensor', 'display']:
            cursor.execute("""
                SELECT serial_number
                FROM raw.app_database_devices
                WHERE device_type = %s AND serial_number IS NOT NULL
                LIMIT 2
            """, (device_type,))
            
            serials = [row[0] for row in cursor.fetchall()]
            if serials:
                print(f"\n  {device_type.upper()}:")
                for serial in serials:
                    print(f"    • {serial}")
    
    # Verify all updated
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(serial_number) as with_serial,
                   COUNT(DISTINCT serial_number) as unique_serials
            FROM raw.app_database_devices
        """)
        total, with_serial, unique = cursor.fetchone()
        
        if total == with_serial == unique:
            print(f"\n✓ Successfully generated {total} unique serial numbers")
        else:
            print(f"\n⚠ Generated {with_serial} serial numbers ({unique} unique) out of {total} devices")
    
    print("\n✓ Task 35 complete!")

if __name__ == "__main__":
    main()