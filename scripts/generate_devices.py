#!/usr/bin/env python3
"""
Generate deterministic devices data for the TapFlow Analytics platform.

This module creates devices with:
- Proper mapping to valid location IDs (1-1000)
- Device distribution based on account size
- Sequential IDs within reserved range (1-30000)
- Realistic device types, models, and status distribution
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

def generate_mac_address(seed):
    """Generate a deterministic MAC address based on seed"""
    random.seed(seed)
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: f"{x:02x}", mac))

def generate_ip_address(location_id, device_index):
    """Generate a deterministic private IP address"""
    # Use location_id for subnet, device_index for host
    subnet = 1 + (location_id % 254)
    host = 1 + (device_index % 254)
    return f"192.168.{subnet}.{host}"

def get_device_model(device_type, manufacturer):
    """Get device model based on type and manufacturer"""
    models = {
        'tap_controller': {
            'TapFlow Pro': ['TC-1000', 'TC-2000', 'TC-3000'],
            'SmartTap': ['ST-500', 'ST-700', 'ST-900'],
            'FlowMaster': ['FM-100', 'FM-200', 'FM-300']
        },
        'sensor': {
            'SensorTech': ['TS-100', 'TS-200', 'TS-300'],
            'IoTFlow': ['IF-50', 'IF-75', 'IF-100']
        },
        'gateway': {
            'NetFlow': ['GW-10', 'GW-20', 'GW-30'],
            'ConnectHub': ['CH-5', 'CH-10', 'CH-15']
        }
    }
    
    type_models = models.get(device_type, {})
    manufacturer_models = type_models.get(manufacturer, ['Generic-001'])
    return random.choice(manufacturer_models)

def get_firmware_version(model):
    """Get firmware version based on model age"""
    # Newer models have higher version numbers
    if '3000' in model or '900' in model or '300' in model:
        return random.choice(['3.0.0', '3.1.0', '3.1.1', '3.2.0'])
    elif '2000' in model or '700' in model or '200' in model:
        return random.choice(['2.5.0', '2.6.0', '2.7.0', '2.8.0'])
    else:
        return random.choice(['1.8.0', '1.9.0', '1.9.1', '2.0.0'])

def get_device_status():
    """Get device status based on operational distribution"""
    dist = config.get_device_config()['operational_distribution']
    rand = random.random()
    
    if rand < dist['online']:
        return 'Online'
    elif rand < dist['online'] + dist['offline']:
        return 'Offline'
    else:
        return 'Maintenance'

def get_last_seen_date(status, installation_date):
    """Get last seen date based on device status"""
    now = datetime.now()
    
    if status == 'Online':
        # Online devices were seen recently (within last 4 hours)
        hours_ago = random.randint(0, 4)
        return now - timedelta(hours=hours_ago)
    elif status == 'Offline':
        # Offline devices haven't been seen for days
        days_ago = random.randint(1, 30)
        return now - timedelta(days=days_ago)
    else:  # Maintenance
        # Maintenance devices were last seen when maintenance started
        days_ago = random.randint(1, 7)
        return now - timedelta(days=days_ago)

def generate_devices():
    """Generate deterministic device data"""
    # Load locations from the saved mapping
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_locations.json'
    )
    
    with open(mapping_file, 'r') as f:
        locations = json.load(f)
    
    # Load accounts to get size information
    account_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    
    with open(account_file, 'r') as f:
        accounts = json.load(f)
    
    # Create account lookup
    account_lookup = {acc['id']: acc for acc in accounts}
    
    devices = []
    device_config = config.get_device_config()
    
    print(f"Generating devices for {len(locations)} locations...")
    
    # Reset ID allocator for devices
    id_allocator.current_ids['devices'] = 1
    
    total_devices = 0
    
    for location in locations:
        # Get account size to determine device count
        account = account_lookup[location['account_id']]
        size = account['account_size']
        distribution = config.get_account_distribution()[size]
        
        # Determine number of devices for this location
        num_devices = random.randint(
            distribution['devices_per_location_min'],
            distribution['devices_per_location_max']
        )
        
        # Convert dates
        location_created = datetime.fromisoformat(location['created_at'])
        
        for device_index in range(num_devices):
            # Get device type based on distribution
            type_dist = device_config['types']
            rand = random.random()
            
            if rand < type_dist['tap_controller']['percentage']:
                device_type = 'tap_controller'
                type_info = type_dist['tap_controller']
            elif rand < type_dist['tap_controller']['percentage'] + type_dist['sensor']['percentage']:
                device_type = 'sensor'
                type_info = type_dist['sensor']
            else:
                device_type = 'gateway'
                type_info = type_dist['gateway']
            
            # Get manufacturer and model
            manufacturer = random.choice(type_info['manufacturers'])
            model = get_device_model(device_type, manufacturer)
            
            # Get sequential device ID
            device_id = id_allocator.get_next_id('devices')
            
            # Installation date is 1-30 days after location creation
            install_days_after = random.randint(1, 30)
            installation_date = location_created + timedelta(days=install_days_after)
            
            # Device properties
            status = get_device_status()
            firmware = get_firmware_version(model)
            
            # Serial number format: MODEL-YYYY-NNNNNN
            serial_number = f"{model}-{installation_date.year}-{device_id:06d}"
            
            # Warranty is 2-5 years after installation
            warranty_years = random.randint(2, 5)
            warranty_expiry = installation_date + timedelta(days=warranty_years * 365)
            
            # Purchase price based on device type and model
            if device_type == 'gateway':
                price = random.uniform(500, 1500)
            elif device_type == 'tap_controller':
                price = random.uniform(1000, 3000)
            else:  # sensor
                price = random.uniform(200, 800)
            
            # Add premium for newer models
            if '3000' in model or '900' in model or '300' in model:
                price *= 1.5
            
            device = {
                'id': device_id,
                'location_id': location['id'],
                'customer_id': location['account_id'],  # Include customer_id
                'device_type': device_type,
                'category': type_info['category'],
                'manufacturer': manufacturer,
                'model': model,
                'serial_number': serial_number,
                'firmware_version': firmware,
                'status': status,
                'install_date': installation_date,
                'warranty_expiry': warranty_expiry,
                'purchase_price': round(price, 2),
                'ip_address': generate_ip_address(location['id'], device_index),
                'mac_address': generate_mac_address(device_id),
                'usage_pattern': random.choice(['high', 'medium', 'low']),
                'expected_lifespan_years': random.randint(5, 10),
                'energy_consumption_watts': random.randint(50, 500),
                'network_connectivity': random.choice(['wifi', 'ethernet', 'cellular']),
                'last_seen_at': get_last_seen_date(status, installation_date),
                'created_at': installation_date,
                'updated_at': installation_date + timedelta(days=random.randint(0, 30))
            }
            
            devices.append(device)
            total_devices += 1
    
    print(f"  Generated {total_devices} total devices")
    print(f"  Average devices per location: {total_devices / len(locations):.2f}")
    
    return devices

def insert_devices(devices):
    """Insert devices into the database"""
    print(f"\nInserting {len(devices)} devices into database...")
    
    # Map our generated data to actual table columns
    mapped_devices = []
    for device in devices:
        mapped = {
            'id': device['id'],
            'location_id': device['location_id'],
            'customer_id': device['customer_id'],
            'device_type': device['device_type'],
            'category': device['category'],
            'manufacturer': device['manufacturer'],
            'model': device['model'],
            'serial_number': device['serial_number'],
            'install_date': device['install_date'].date(),
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
    serializable_devices = []
    for device in devices:
        device_copy = device.copy()
        device_copy['install_date'] = device_copy['install_date'].isoformat()
        device_copy['warranty_expiry'] = device_copy['warranty_expiry'].isoformat()
        device_copy['last_seen_at'] = device_copy['last_seen_at'].isoformat()
        device_copy['created_at'] = device_copy['created_at'].isoformat()
        device_copy['updated_at'] = device_copy['updated_at'].isoformat()
        serializable_devices.append(device_copy)
    
    with open(mapping_file, 'w') as f:
        json.dump(serializable_devices, f, indent=2)
    
    print(f"\n✓ Saved device mapping to {mapping_file}")

def verify_devices():
    """Verify the inserted devices"""
    count = db_helper.get_row_count('app_database_devices')
    print(f"\n✓ Verification: {count} devices in database")
    
    # Show distribution statistics
    with db_helper.config.get_cursor() as cursor:
        # Device type distribution
        cursor.execute("""
            SELECT device_type, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_devices
            GROUP BY device_type
            ORDER BY count DESC
        """)
        type_dist = cursor.fetchall()
        
        print("\nDevice type distribution:")
        for row in type_dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        # Status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_devices
            GROUP BY status
            ORDER BY count DESC
        """)
        status_dist = cursor.fetchall()
        
        print("\nDevice status distribution:")
        for row in status_dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        # Devices per location
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
        per_loc = cursor.fetchall()
        
        print("\nDevices per location distribution:")
        for row in per_loc:
            print(f"  {row[0]} devices: {row[1]} locations")
        
        # Verify all location_ids are valid
        cursor.execute("""
            SELECT COUNT(*) as orphaned_devices
            FROM raw.app_database_devices d
            LEFT JOIN raw.app_database_locations l ON d.location_id = l.id
            WHERE l.id IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        
        if orphaned == 0:
            print("\n✓ All devices have valid location references")
        else:
            print(f"\n⚠️  Warning: {orphaned} devices have invalid location_ids")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Device Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if devices already exist
    existing_count = db_helper.get_row_count('app_database_devices')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} devices already exist")
        if should_truncate():
            db_helper.truncate_table('app_database_devices')
        else:
            print("Aborting...")
            return
    
    # Generate devices
    devices = generate_devices()
    
    # Save mapping for other generators
    save_device_mapping(devices)
    
    # Insert into database
    inserted = insert_devices(devices)
    
    # Verify
    verify_devices()
    
    print(f"\n✅ Successfully generated {inserted} devices!")

if __name__ == "__main__":
    main()