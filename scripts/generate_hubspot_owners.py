#!/usr/bin/env python3
"""
Generate synthetic HubSpot owners data for the bar management SaaS platform.

This module creates HubSpot owner records representing sales and support team members:
- Sales representatives
- Customer success managers
- Support agents
- Team leads and managers
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# Owner configuration
OWNER_TYPES = [
    ('SALES_REP', 0.40),
    ('CUSTOMER_SUCCESS', 0.30),
    ('SUPPORT_AGENT', 0.20),
    ('MANAGER', 0.10)
]

TEAMS = [
    'Sales - East',
    'Sales - West', 
    'Sales - Central',
    'Customer Success',
    'Technical Support',
    'Enterprise Sales',
    'SMB Sales'
]

def generate_hubspot_owners():
    """Generate HubSpot owner records"""
    owners = []
    
    # Calculate number of owners based on company count
    # Roughly 1 owner per 100 companies for realistic ratios
    num_owners = max(50, current_env.hubspot_companies // 100)
    
    print(f"Generating {num_owners:,} HubSpot owners...")
    
    # Generate a realistic date range (company founded 5 years ago)
    company_start_date = datetime.now() - timedelta(days=5*365)
    
    for i in range(num_owners):
        owner_id = i + 1
        
        # Generate owner details
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@barmanagement.com"
        
        # Determine owner type
        owner_type = random.choices(
            [t[0] for t in OWNER_TYPES],
            [t[1] for t in OWNER_TYPES]
        )[0]
        
        # Assign to team based on type
        if owner_type == 'SALES_REP':
            team = random.choice([t for t in TEAMS if 'Sales' in t and 'Enterprise' not in t])
        elif owner_type == 'CUSTOMER_SUCCESS':
            team = 'Customer Success'
        elif owner_type == 'SUPPORT_AGENT':
            team = 'Technical Support'
        else:  # MANAGER
            team = random.choice(TEAMS)
        
        # Generate hire date (staggered over company lifetime)
        hire_date = company_start_date + timedelta(
            days=random.randint(0, (datetime.now() - company_start_date).days)
        )
        
        # Some owners might be inactive (left company)
        is_active = random.random() < 0.85  # 85% active
        
        owner = {
            'id': owner_id,
            'email': email,
            'type': 'PERSON',
            'first_name': first_name,
            'last_name': last_name,
            'user_id': owner_id * 1000,  # HubSpot user ID
            'created_at': hire_date,
            'updated_at': hire_date + timedelta(days=random.randint(1, 30)),
            'archived': not is_active,
            'teams': json.dumps([{
                'id': TEAMS.index(team) + 1,
                'name': team,
                'primary': True
            }]),
            'signature': f"Best regards,\n{first_name} {last_name}\n{owner_type.replace('_', ' ').title()}\nBar Management Solutions",
            'is_active': is_active,
            'metadata': json.dumps({
                'owner_type': owner_type,
                'team': team,
                'hire_date': hire_date.isoformat(),
                'quota': 50 if owner_type == 'SALES_REP' else None,
                'phone': fake.phone_number()
            })
        }
        
        owners.append(owner)
    
    # Create a few special owners for system/automation
    system_owner = {
        'id': num_owners + 1,
        'email': 'system@barmanagement.com',
        'type': 'SYSTEM',
        'first_name': 'System',
        'last_name': 'Automation',
        'user_id': 999999,
        'created_at': company_start_date,
        'updated_at': company_start_date,
        'archived': False,
        'teams': json.dumps([]),
        'signature': None,
        'is_active': True,
        'metadata': json.dumps({
            'owner_type': 'SYSTEM',
            'team': None,
            'description': 'Automated system processes'
        })
    }
    owners.append(system_owner)
    
    return owners

def insert_hubspot_owners(owners):
    """Insert HubSpot owners into the database"""
    print(f"\nInserting {len(owners):,} owners into database...")
    
    inserted = db_helper.bulk_insert('hubspot_owners', owners)
    
    return inserted

def verify_hubspot_owners():
    """Verify the inserted owners"""
    count = db_helper.get_row_count('hubspot_owners')
    print(f"\n✓ Verification: {count:,} owners in database")
    
    # Show team distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                metadata->>'team' as team,
                COUNT(*) as count
            FROM raw.hubspot_owners
            WHERE metadata->>'team' IS NOT NULL
            GROUP BY team
            ORDER BY count DESC
        """)
        team_dist = cursor.fetchall()
        
        print("\nOwner distribution by team:")
        for row in team_dist:
            print(f"  {row['team']}: {row['count']} owners")
        
        # Show owner type distribution
        cursor.execute("""
            SELECT 
                metadata->>'owner_type' as owner_type,
                COUNT(*) as count,
                COUNT(CASE WHEN is_active THEN 1 END) as active_count
            FROM raw.hubspot_owners
            GROUP BY owner_type
            ORDER BY count DESC
        """)
        type_dist = cursor.fetchall()
        
        print("\nOwner type distribution:")
        for row in type_dist:
            print(f"  {row['owner_type']}: {row['count']} total, {row['active_count']} active")
        
        # Show sample owners
        cursor.execute("""
            SELECT 
                first_name,
                last_name,
                email,
                metadata->>'owner_type' as owner_type,
                metadata->>'team' as team
            FROM raw.hubspot_owners
            WHERE type = 'PERSON'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample owners (most recent hires):")
        for owner in samples:
            print(f"  {owner['first_name']} {owner['last_name']} - {owner['owner_type']} - {owner['team']}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("HubSpot Owner Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if owners already exist
    existing_count = db_helper.get_row_count('hubspot_owners')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} owners already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('hubspot_owners')
        else:
            print("Aborting...")
            return
    
    # Generate owners
    owners = generate_hubspot_owners()
    
    # Insert into database
    inserted = insert_hubspot_owners(owners)
    
    # Verify
    verify_hubspot_owners()
    
    print(f"\n✅ Successfully generated {inserted:,} owners!")

if __name__ == "__main__":
    main()