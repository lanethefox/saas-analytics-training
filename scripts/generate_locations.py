#!/usr/bin/env python3
"""
Generate deterministic locations data for the TapFlow Analytics platform.

This module creates locations with:
- Proper distribution per account size (small: 1-2, medium: 3-10, large: 10-50, enterprise: 50-100)
- Sequential IDs within reserved range (1-1000)
- Geographic distribution from configuration
- Realistic temporal patterns
"""

import sys
import os
import random
import json
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
fake = Faker('en_US')

LOCATION_TYPES = ['main', 'branch', 'satellite', 'franchise']

def get_locations_for_account(account):
    """Determine number of locations based on account size"""
    size = account['account_size']
    distribution = config.get_account_distribution()[size]
    
    # Get the range for this account size
    min_locations = distribution['locations_min']
    max_locations = distribution['locations_max']
    
    # Use a weighted distribution within the range
    if size == 'small':
        # Most small accounts have minimum locations
        if random.random() < 0.7:
            return min_locations
        else:
            return random.randint(min_locations, max_locations)
    elif size == 'medium':
        # Medium accounts spread across range
        return random.randint(min_locations, max_locations)
    elif size == 'large':
        # Large accounts tend toward middle of range
        mid = (min_locations + max_locations) // 2
        return random.randint(mid - 5, mid + 5)
    else:  # enterprise
        # Enterprise accounts have many locations
        return random.randint(min_locations, max_locations)

def get_state_for_location(index, total_locations):
    """Assign state based on geographic distribution"""
    geo_dist = config.get_geographic_distribution()
    
    # Build weighted state list
    state_list = []
    for region, info in geo_dist.items():
        states = info['states']
        # Distribute region percentage across its states
        per_state = info['percentage'] / len(states)
        for state in states:
            state_list.append((state, per_state))
    
    # Make weighted choice
    states = [s[0] for s in state_list]
    weights = [s[1] for s in state_list]
    return random.choices(states, weights=weights)[0]

def generate_location_name(company_name, location_type, index, city):
    """Generate location name based on company and type"""
    if location_type == 'main' and index == 1:
        return f"{company_name} - Main"
    elif location_type == 'franchise':
        return f"{company_name} - Franchise #{index}"
    elif location_type == 'satellite':
        return f"{company_name} - {city} Satellite"
    else:  # branch
        return f"{company_name} - {city}"

def generate_locations():
    """Generate deterministic location data"""
    # Load accounts from the saved mapping
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    
    with open(mapping_file, 'r') as f:
        accounts = json.load(f)
    
    # Convert ISO strings back to datetime
    for acc in accounts:
        acc['created_at'] = datetime.fromisoformat(acc['created_at'])
        acc['updated_at'] = datetime.fromisoformat(acc['updated_at'])
    
    locations = []
    location_counts = {}  # Track locations per account
    
    print(f"Generating locations for {len(accounts)} accounts...")
    
    # Reset ID allocator for locations
    id_allocator.current_ids['locations'] = 1
    
    for account in accounts:
        num_locations = get_locations_for_account(account)
        location_counts[account['id']] = num_locations
        
        # First location is always main
        location_types = ['main']
        
        # Add other location types
        if num_locations > 1:
            # For multiple locations, mix of branches and other types
            for i in range(1, num_locations):
                if account['account_size'] == 'enterprise' and i % 10 == 0:
                    location_types.append('franchise')
                elif account['account_size'] in ['large', 'enterprise'] and i % 5 == 0:
                    location_types.append('satellite')
                else:
                    location_types.append('branch')
        
        for i, loc_type in enumerate(location_types):
            # Generate location details
            state = get_state_for_location(i, num_locations)
            fake.seed_instance(account['id'] * 1000 + i)  # Deterministic per location
            city = fake.city()
            
            # Get sequential location ID
            location_id = id_allocator.get_next_id('locations')
            
            # Create location a few days after account
            created_at = account['created_at'] + timedelta(days=random.randint(1, 30))
            
            location = {
                'id': location_id,
                'account_id': account['id'],
                'name': generate_location_name(account['name'], loc_type, i + 1, city),
                'address': fake.street_address(),
                'city': city,
                'state': state,
                'zip_code': fake.zipcode_in_state(state),
                'phone': fake.phone_number(),
                'type': loc_type,
                'is_active': account['is_active'] and random.random() < 0.95,
                'created_at': created_at,
                'updated_at': created_at + timedelta(days=random.randint(1, 60))
            }
            
            locations.append(location)
    
    print(f"  Generated {len(locations)} total locations")
    print(f"  Average locations per account: {len(locations) / len(accounts):.2f}")
    
    return locations, location_counts

def insert_locations(locations):
    """Insert locations into the database"""
    print(f"\nInserting {len(locations)} locations into database...")
    
    # Map our generated data to actual table columns
    mapped_locations = []
    for loc in locations:
        # Determine expected device count based on account size
        # We'll look this up from the account data
        account_id = loc['account_id']
        
        # Load account data to get size
        mapping_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'data', 
            'generated_accounts.json'
        )
        with open(mapping_file, 'r') as f:
            accounts = json.load(f)
        
        account = next(a for a in accounts if a['id'] == account_id)
        size = account['account_size']
        distribution = config.get_account_distribution()[size]
        
        # Set expected device count based on size
        expected_devices = random.randint(
            distribution['devices_per_location_min'],
            distribution['devices_per_location_max']
        )
        
        mapped = {
            'id': loc['id'],
            'customer_id': loc['account_id'],
            'name': loc['name'],
            'address': loc['address'],
            'city': loc['city'],
            'state': loc['state'],
            'zip_code': loc['zip_code'],
            'country': 'USA',
            'location_type': loc['type'],
            'business_type': account['business_type'],  # Use account's business type
            'size': size,  # Use account size
            'expected_device_count': expected_devices,
            'install_date': loc['created_at'].date(),
            'created_at': loc['created_at'],
            'updated_at': loc['updated_at']
        }
        mapped_locations.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_locations', mapped_locations)
    return inserted

def update_account_location_counts(location_counts):
    """Update location counts in accounts table"""
    print("\nUpdating location counts in accounts table...")
    
    with db_helper.config.get_cursor() as cursor:
        for account_id, count in location_counts.items():
            cursor.execute("""
                UPDATE raw.app_database_accounts 
                SET location_count = %s
                WHERE id = %s
            """, (count, str(account_id)))
        
        cursor.connection.commit()
        print(f"✓ Updated location counts for {len(location_counts)} accounts")

def save_location_mapping(locations):
    """Save location mapping to JSON file for use by other generators"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_locations.json'
    )
    
    # Save the full location data
    serializable_locations = []
    for loc in locations:
        loc_copy = loc.copy()
        loc_copy['created_at'] = loc_copy['created_at'].isoformat()
        loc_copy['updated_at'] = loc_copy['updated_at'].isoformat()
        serializable_locations.append(loc_copy)
    
    with open(mapping_file, 'w') as f:
        json.dump(serializable_locations, f, indent=2)
    
    print(f"\n✓ Saved location mapping to {mapping_file}")

def verify_locations():
    """Verify the inserted locations"""
    count = db_helper.get_row_count('app_database_locations')
    print(f"\n✓ Verification: {count} locations in database")
    
    # Show distribution statistics
    with db_helper.config.get_cursor() as cursor:
        # Locations per account
        cursor.execute("""
            SELECT location_count, COUNT(*) as account_count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_accounts
            WHERE location_count > 0
            GROUP BY location_count
            ORDER BY location_count
        """)
        dist = cursor.fetchall()
        
        print("\nLocations per account distribution:")
        for row in dist:
            print(f"  {row[0]} locations: {row[1]} accounts ({row[2]}%)")
        
        # State distribution
        cursor.execute("""
            SELECT state, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_locations
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """)
        state_dist = cursor.fetchall()
        
        print("\nTop 10 states by location count:")
        for row in state_dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        # Location types
        cursor.execute("""
            SELECT location_type, COUNT(*) as count
            FROM raw.app_database_locations
            GROUP BY location_type
            ORDER BY count DESC
        """)
        type_dist = cursor.fetchall()
        
        print("\nLocation type distribution:")
        for row in type_dist:
            print(f"  {row[0]}: {row[1]}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Location Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if locations already exist
    existing_count = db_helper.get_row_count('app_database_locations')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} locations already exist")
        if should_truncate():
            db_helper.truncate_table('app_database_locations')
        else:
            print("Aborting...")
            return
    
    # Generate locations
    locations, location_counts = generate_locations()
    
    # Save mapping for other generators
    save_location_mapping(locations)
    
    # Insert into database
    inserted = insert_locations(locations)
    
    # Update account location counts
    update_account_location_counts(location_counts)
    
    # Verify
    verify_locations()
    
    print(f"\n✅ Successfully generated {inserted} locations!")

if __name__ == "__main__":
    main()