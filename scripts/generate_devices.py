#!/usr/bin/env python3
"""
Generate synthetic devices data for the bar management SaaS platform.

This module creates realistic IoT device data with:
- 2-5 devices per location
- Device models and firmware versions
- Installation dates after location creation
- Status distribution (online 85%, offline 10%, maintenance 5%)
- Last seen patterns based on status
"""

import sys
import os
import random
import json
import uuid
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# Device configuration
DEVICE_TYPES = ['tap', 'sensor', 'display', 'controller']
CATEGORIES = ['beverage', 'monitoring', 'interface', 'control']
MANUFACTURERS = ['TapFlow Inc', 'SmartBar Systems', 'IoT Solutions Co']

DEVICE_MODELS = [
    'TapFlow Pro v2',
    'TapFlow Pro v3',
    'TapFlow Enterprise',
    'SmartTap 5000',
    'SmartTap 7000'
]

FIRMWARE_VERSIONS = [
    '1.2.5',
    '1.3.0',
    '1.3.1',
    '2.0.0',
    '2.1.0'
]

DEVICE_STATUS = [
    ('online', 0.85),
    ('offline', 0.10),
    ('maintenance', 0.05)
]

USAGE_PATTERNS = ['high', 'medium', 'low']
NETWORK_CONNECTIVITY = ['wifi', 'ethernet', 'cellular']

# Devices per location
DEVICES_PER_LOCATION = [
    (2, 0.30),  # 30% have 2 devices
    (3, 0.40),  # 40% have 3 devices
    (4, 0.20),  # 20% have 4 devices
    (5, 0.10),  # 10% have 5 devices
]

def weighted_choice(choices):
    """Make a weighted random choice"""
    population = [item[0] for item in choices]
    weights = [item[1] for item in choices]
    return random.choices(population, weights=weights)[0]

def generate_mac_address():
    """Generate a random MAC address"""
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: f"{x:02x}", mac))

def generate_ip_address():
    """Generate a random private IP address"""
    # Use 192.168.x.x range
    return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"

def load_locations():
    """Load generated locations from JSON file"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_locations.json'
    )
    
    with open(mapping_file, 'r') as f:
        locations = json.load(f)
    
    # Convert ISO strings back to datetime
    for loc in locations:
        loc['created_at'] = datetime.fromisoformat(loc['created_at'])
        loc['updated_at'] = datetime.fromisoformat(loc['updated_at'])
    
    return locations

def get_last_seen_date(status, installation_date):
    """Get last seen date based on device status"""
    if status == 'online':
        # Online devices were seen recently (within last 24 hours)
        hours_ago = random.randint(0, 24)
        return datetime.now() - timedelta(hours=hours_ago)
    elif status == 'offline':
        # Offline devices haven't been seen for days
        days_ago = random.randint(1, 30)
        return datetime.now() - timedelta(days=days_ago)
    else:  # maintenance
        # Maintenance devices were last seen when maintenance started
        days_ago = random.randint(1, 7)
        return datetime.now() - timedelta(days=days_ago)

def generate_devices(locations, total_devices):
    """Generate synthetic device data"""
    devices = []
    device_id = 1
    
    print(f"Generating {total_devices:,} devices for {len(locations):,} locations...")
    
    # Calculate devices per location
    devices_needed = total_devices
    location_devices = []
    
    for location in locations:
        num_devices = weighted_choice(DEVICES_PER_LOCATION)
        location_devices.append((location, num_devices))
        devices_needed -= num_devices
    
    # Adjust if we need more devices
    while devices_needed > 0:
        idx = random.randint(0, len(location_devices) - 1)
        location, current_count = location_devices[idx]
        if current_count < 5:  # Max 5 devices per location
            location_devices[idx] = (location, current_count + 1)
            devices_needed -= 1
    
    # Adjust if we have too many devices
    while devices_needed < 0:
        idx = random.randint(0, len(location_devices) - 1)
        location, current_count = location_devices[idx]
        if current_count > 2:  # Min 2 devices per location
            location_devices[idx] = (location, current_count - 1)
            devices_needed += 1
    
    # Generate devices for each location
    for location, num_devices in location_devices:
        for i in range(num_devices):
            # Device details
            device_type = random.choice(DEVICE_TYPES)
            category = random.choice(CATEGORIES)
            manufacturer = random.choice(MANUFACTURERS)
            model = random.choice(DEVICE_MODELS)
            firmware = random.choice(FIRMWARE_VERSIONS)
            status = weighted_choice(DEVICE_STATUS)
            
            # Installation date is after location creation
            install_days_after = random.randint(1, 60)
            installation_date = location['created_at'] + timedelta(days=install_days_after)
            
            # Warranty is 2-5 years after installation
            warranty_years = random.randint(2, 5)
            warranty_expiry = installation_date + timedelta(days=warranty_years * 365)
            
            # Purchase price based on model
            if 'Enterprise' in model:
                price = random.uniform(2000, 5000)
            elif 'Pro' in model:
                price = random.uniform(1000, 2000)
            else:
                price = random.uniform(500, 1000)
            
            # Serial number format: MODEL-YYYY-NNNNNN
            serial_number = f"{model.replace(' ', '').upper()[:5]}-{installation_date.year}-{random.randint(100000, 999999)}"
            
            device = {
                'id': device_id,
                'location_id': location['id'],
                'account_id': location['account_id'],
                'device_type': device_type,
                'category': category,
                'manufacturer': manufacturer,
                'serial_number': serial_number,
                'model': model,
                'firmware_version': firmware,
                'status': status,
                'installation_date': installation_date,
                'warranty_expiry': warranty_expiry,
                'purchase_price': round(price, 2),
                'ip_address': generate_ip_address(),
                'mac_address': generate_mac_address(),
                'usage_pattern': random.choice(USAGE_PATTERNS),
                'expected_lifespan_years': random.randint(5, 10),
                'energy_consumption_watts': random.randint(50, 500),
                'network_connectivity': random.choice(NETWORK_CONNECTIVITY),
                'last_seen_at': get_last_seen_date(status, installation_date),
                'uptime_percentage': random.uniform(95.0, 99.9) if status == 'online' else random.uniform(80.0, 95.0),
                'created_at': installation_date,
                'updated_at': installation_date + timedelta(days=random.randint(0, 30))
            }
            
            devices.append(device)
            device_id += 1
    
    return devices

def insert_devices(devices):
    """Insert devices into the database"""
    print(f"\nInserting {len(devices):,} devices into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_devices'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.app_database_devices:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_devices = []
    for device in devices:
        mapped = {
            'id': device['id'],
            'location_id': device['location_id'],
            'device_type': device['device_type'],
            'category': device['category'],
            'manufacturer': device['manufacturer'],
            'model': device['model'],
            'serial_number': device['serial_number'],
            'install_date': device['installation_date'].date(),
            'warranty_expiry': device['warranty_expiry'].date(),
            'purchase_price': device['purchase_price'],
            'firmware_version': device['firmware_version'],
            'ip_address': device['ip_address'],
            'mac_address': device['mac_address'],
            'status': device['status'],
            'usage_pattern': device['usage_pattern'],
            'expected_lifespan_years': device['expected_lifespan_years'],
            'energy_consumption_watts': device['energy_consumption_watts'],
            'network_connectivity': device['network_connectivity'],
            'created_at': device['created_at'],
            'updated_at': device['updated_at']
        }
        mapped_devices.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_devices', mapped_devices)
    
    return inserted

def save_device_mapping(devices):
    """Save device mapping to JSON file for use by other generators"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_devices.json'
    )
    
    # Save the full device data
    with open(mapping_file, 'w') as f:
        # Convert datetime objects to strings
        serializable_devices = []
        for device in devices:
            device_copy = device.copy()
            device_copy['installation_date'] = device_copy['installation_date'].isoformat()
            device_copy['warranty_expiry'] = device_copy['warranty_expiry'].isoformat()
            device_copy['last_seen_at'] = device_copy['last_seen_at'].isoformat()
            device_copy['created_at'] = device_copy['created_at'].isoformat()
            device_copy['updated_at'] = device_copy['updated_at'].isoformat()
            serializable_devices.append(device_copy)
        
        json.dump(serializable_devices, f, indent=2)
    
    print(f"\n✓ Saved device mapping to {mapping_file}")

def verify_devices():
    """Verify the inserted devices"""
    count = db_helper.get_row_count('app_database_devices')
    print(f"\n✓ Verification: {count:,} devices in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT d.*, l.name as location_name
            FROM raw.app_database_devices d
            JOIN raw.app_database_locations l ON d.location_id = l.id
            ORDER BY d.created_at DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample devices (most recent):")
        for device in samples:
            print(f"  {device['serial_number']} - {device['model']} - Status: {device['status']} - Location: {device['location_name']}")
    
    # Show status distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT status, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_devices
            GROUP BY status
            ORDER BY count DESC
        """)
        dist = cursor.fetchall()
        
        print("\nStatus distribution:")
        for row in dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
    
    # Show devices per location statistics
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT device_count, COUNT(*) as location_count
            FROM (
                SELECT location_id, COUNT(*) as device_count
                FROM raw.app_database_devices
                GROUP BY location_id
            ) dc
            GROUP BY device_count
            ORDER BY device_count
        """)
        dist = cursor.fetchall()
        
        print("\nDevices per location distribution:")
        for row in dist:
            print(f"  {row[0]} devices: {row[1]} locations")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Device Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if devices already exist
    existing_count = db_helper.get_row_count('app_database_devices')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} devices already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_devices')
        else:
            print("Aborting...")
            return
    
    # Load locations
    locations = load_locations()
    print(f"\n✓ Loaded {len(locations):,} locations")
    
    # Generate devices
    devices = generate_devices(locations, current_env.devices)
    
    # Save mapping for other generators
    save_device_mapping(devices)
    
    # Insert into database
    inserted = insert_devices(devices)
    
    # Verify
    verify_devices()
    
    print(f"\n✅ Successfully generated {inserted:,} devices!")

if __name__ == "__main__":
    main()
