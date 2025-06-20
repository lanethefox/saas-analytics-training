#!/usr/bin/env python3
"""
Generate synthetic locations data for the bar management SaaS platform.

This module creates realistic location data with:
- 1-5 locations per account (weighted distribution)
- Geographic distribution across US states
- Location types (Main 40%, Branch 40%, Franchise 20%)
- Realistic addresses and zip codes
"""

import sys
import os
import random
import json
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker('en_US')
Faker.seed(42)
random.seed(42)

# Location configuration
LOCATION_TYPES = [
    ('main', 0.40),
    ('branch', 0.40),
    ('franchise', 0.20)
]

# Weighted location counts per account
LOCATIONS_PER_ACCOUNT = [
    (1, 0.40),  # 40% have 1 location
    (2, 0.30),  # 30% have 2 locations
    (3, 0.15),  # 15% have 3 locations
    (4, 0.10),  # 10% have 4 locations
    (5, 0.05),  # 5% have 5 locations
]
# Popular US states for business (weighted)
US_STATES = [
    ('CA', 0.15),  # California
    ('TX', 0.12),  # Texas
    ('NY', 0.10),  # New York
    ('FL', 0.08),  # Florida
    ('IL', 0.06),  # Illinois
    ('PA', 0.05),  # Pennsylvania
    ('OH', 0.04),  # Ohio
    ('GA', 0.04),  # Georgia
    ('NC', 0.04),  # North Carolina
    ('MI', 0.04),  # Michigan
]

# Add remaining states with equal small probability
other_states = ['AL', 'AK', 'AZ', 'AR', 'CO', 'CT', 'DE', 'HI', 'ID', 'IN', 
                'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MN', 'MS', 'MO',
                'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'OK', 'OR', 'RI', 'SC',
                'SD', 'TN', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

remaining_prob = 1.0 - sum(state[1] for state in US_STATES)
prob_per_state = remaining_prob / len(other_states)
US_STATES.extend([(state, prob_per_state) for state in other_states])

def weighted_choice(choices):
    """Make a weighted random choice"""
    population = [item[0] for item in choices]
    weights = [item[1] for item in choices]
    return random.choices(population, weights=weights)[0]

def load_accounts():
    """Load generated accounts from JSON file"""
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
    
    return accounts

def generate_location_name(company_name, location_type, index):
    """Generate location name based on company and type"""
    if location_type == 'main':
        return f"{company_name} - Main"
    elif location_type == 'franchise':
        return f"{company_name} - Franchise #{index}"
    else:  # branch
        return f"{company_name} - {fake.city()} Branch"

def generate_locations(accounts, total_locations):
    """Generate synthetic location data"""
    locations = []
    location_id = 1
    
    print(f"Generating {total_locations:,} locations for {len(accounts):,} accounts...")
    
    # Calculate locations per account to reach total
    locations_needed = total_locations
    account_locations = []
    
    # First pass: assign minimum locations
    for account in accounts:
        num_locations = weighted_choice(LOCATIONS_PER_ACCOUNT)
        account_locations.append((account, num_locations))
        locations_needed -= num_locations
    
    # Adjust if we need more locations
    while locations_needed > 0:
        # Add locations to random accounts
        idx = random.randint(0, len(account_locations) - 1)
        account, current_count = account_locations[idx]
        if current_count < 5:  # Max 5 locations per account
            account_locations[idx] = (account, current_count + 1)
            locations_needed -= 1
    
    # Generate locations for each account
    for account, num_locations in account_locations:
        # First location is always main
        location_types = ['main'] + [weighted_choice(LOCATION_TYPES) 
                                    for _ in range(num_locations - 1)]
        
        for i, loc_type in enumerate(location_types):
            state = weighted_choice(US_STATES)
            
            location = {
                'id': location_id,
                'account_id': account['id'],
                'name': generate_location_name(account['company_name'], loc_type, i + 1),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': state,
                'zip_code': fake.zipcode(),
                'phone': fake.phone_number(),
                'type': loc_type,
                'is_active': account['is_active'] and random.random() < 0.95,
                'created_at': account['created_at'] + timedelta(days=random.randint(0, 90)),
                'updated_at': account['created_at'] + timedelta(days=random.randint(90, 180))
            }
            
            locations.append(location)
            location_id += 1
    
    return locations

def insert_locations(locations):
    """Insert locations into the database"""
    print(f"\nInserting {len(locations):,} locations into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_locations'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.app_database_locations:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_locations = []
    for loc in locations:
        mapped = {
            'id': loc['id'],
            'customer_id': loc['account_id'],  # customer_id maps to account_id
            'name': loc['name'],
            'address': loc['address'],
            'city': loc['city'],
            'state': loc['state'],
            'zip_code': loc['zip_code'],
            'country': 'USA',  # All US locations
            'location_type': loc['type'],
            'business_type': 'bar',  # Default to bar
            'size': random.choice(['small', 'medium', 'large']),
            'expected_device_count': random.randint(2, 5),
            'install_date': loc['created_at'].date(),
            'created_at': loc['created_at'],
            'updated_at': loc['updated_at']
        }
        mapped_locations.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_locations', mapped_locations)
    
    # Update location count in accounts table
    print("\nUpdating location counts in accounts table...")
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            UPDATE raw.app_database_accounts a
            SET location_count = (
                SELECT COUNT(*)
                FROM raw.app_database_locations l
                WHERE l.customer_id = a.id
            )
        """)
        print("✓ Updated location counts")
    
    return inserted

def save_location_mapping(locations):
    """Save location mapping to JSON file for use by other generators"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_locations.json'
    )
    
    # Save the full location data
    with open(mapping_file, 'w') as f:
        # Convert datetime objects to strings
        serializable_locations = []
        for loc in locations:
            loc_copy = loc.copy()
            loc_copy['created_at'] = loc_copy['created_at'].isoformat()
            loc_copy['updated_at'] = loc_copy['updated_at'].isoformat()
            serializable_locations.append(loc_copy)
        
        json.dump(serializable_locations, f, indent=2)
    
    print(f"\n✓ Saved location mapping to {mapping_file}")

def verify_locations():
    """Verify the inserted locations"""
    count = db_helper.get_row_count('app_database_locations')
    print(f"\n✓ Verification: {count:,} locations in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT l.*, a.name as account_name
            FROM raw.app_database_locations l
            JOIN raw.app_database_accounts a ON l.customer_id = a.id
            ORDER BY l.created_at DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample locations (most recent):")
        for loc in samples:
            print(f"  {loc['name']} - {loc['address']} - Account: {loc['account_name']}")
    
    # Show distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT a.location_count, COUNT(*) as account_count
            FROM raw.app_database_accounts a
            GROUP BY a.location_count
            ORDER BY a.location_count
        """)
        dist = cursor.fetchall()
        
        print("\nLocations per account distribution:")
        for row in dist:
            print(f"  {row[0]} locations: {row[1]} accounts")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Location Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if locations already exist
    existing_count = db_helper.get_row_count('app_database_locations')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} locations already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_locations')
        else:
            print("Aborting...")
            return
    
    # Load accounts
    accounts = load_accounts()
    print(f"\n✓ Loaded {len(accounts):,} accounts")
    
    # Generate locations
    locations = generate_locations(accounts, current_env.locations)
    
    # Save mapping for other generators
    save_location_mapping(locations)
    
    # Insert into database
    inserted = insert_locations(locations)
    
    # Verify
    verify_locations()
    
    print(f"\n✅ Successfully generated {inserted:,} locations!")

if __name__ == "__main__":
    main()
