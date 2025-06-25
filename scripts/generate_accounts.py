#!/usr/bin/env python3
"""
Generate deterministic accounts data for the TapFlow Analytics platform.

This module creates accounts with:
- Deterministic distribution (70% small, 20% medium, 8% large, 2% enterprise)
- Industry distribution from configuration
- Sequential IDs (1-150)
- Realistic temporal distribution
"""

import sys
import os
import random
import json
from datetime import datetime, timedelta
from faker import Faker
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

# Initialize Faker with seed from config
fake = Faker()

# Company name patterns by industry
COMPANY_PATTERNS = {
    'restaurant': [
        "{} Kitchen", "{} Bistro", "{} Grill", "{} Cafe",
        "{} Restaurant", "{} Diner", "{} Eatery", "{} Table"
    ],
    'bar': [
        "{} Tavern", "{} Pub", "{} Lounge", "{} Bar",
        "{} Club", "{} Brewery", "{} Taproom", "{} Saloon"
    ],
    'stadium': [
        "{} Stadium", "{} Arena", "{} Field", "{} Center",
        "{} Park", "{} Coliseum", "{} Pavilion", "{} Complex"
    ],
    'hotel': [
        "{} Hotel", "{} Inn", "{} Resort", "{} Lodge",
        "{} Suites", "{} Plaza", "{} Arms", "{} House"
    ],
    'corporate': [
        "{} Corporation", "{} LLC", "{} Inc", "{} Group",
        "{} Solutions", "{} Enterprises", "{} Holdings", "{} Partners"
    ]
}

def generate_company_name(industry):
    """Generate a realistic company name based on industry"""
    pattern = random.choice(COMPANY_PATTERNS[industry])
    
    # Use various name generation strategies
    name_type = random.choice(['last_name', 'city', 'word', 'color'])
    
    if name_type == 'last_name':
        base_name = fake.last_name()
    elif name_type == 'city':
        base_name = fake.city().split()[0]  # First word of city name
    elif name_type == 'word':
        words = ['Golden', 'Silver', 'Royal', 'Grand', 'Elite',
                'Premier', 'Classic', 'Modern', 'Urban', 'Vintage']
        base_name = random.choice(words)
    else:
        base_name = fake.color_name().title()
    
    return pattern.format(base_name)

def get_created_date(account_index, total_accounts):
    """Generate created date based on growth patterns"""
    growth = config.get_growth_patterns()['account_creation']
    time_ranges = config.get_time_ranges()
    
    start_date = datetime.strptime(time_ranges['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(time_ranges['end_date'], '%Y-%m-%d')
    
    # Determine which growth period this account belongs to
    if account_index < total_accounts * growth['established']:
        # 2+ years ago
        days_ago = random.randint(730, 1825)  # 2-5 years
    elif account_index < total_accounts * (growth['established'] + growth['growing']):
        # 1-2 years ago
        days_ago = random.randint(365, 730)
    elif account_index < total_accounts * (growth['established'] + growth['growing'] + growth['scaling']):
        # 6-12 months ago
        days_ago = random.randint(180, 365)
    else:
        # <6 months ago (new)
        days_ago = random.randint(1, 180)
    
    created_date = end_date - timedelta(days=days_ago)
    
    # Ensure date is within our time range
    if created_date < start_date:
        created_date = start_date + timedelta(days=random.randint(1, 30))
    
    return created_date

def get_account_size(account_id):
    """Determine account size based on ID range"""
    if account_id <= 105:
        return 'small'
    elif account_id <= 135:
        return 'medium'
    elif account_id <= 147:
        return 'large'
    else:
        return 'enterprise'

def generate_accounts():
    """Generate deterministic account data"""
    accounts = []
    total_accounts = config.get_total_accounts()
    industries = config.get_industries()
    
    print(f"Generating {total_accounts} accounts...")
    
    # Convert industry percentages to counts
    industry_list = []
    for industry, percentage in industries.items():
        count = int(total_accounts * percentage)
        industry_list.extend([industry] * count)
    
    # Shuffle for variety but keep deterministic
    random.shuffle(industry_list)
    
    # Ensure we have exactly the right number
    while len(industry_list) < total_accounts:
        industry_list.append(random.choice(list(industries.keys())))
    industry_list = industry_list[:total_accounts]
    
    for i in range(total_accounts):
        # Get sequential ID
        account_id = id_allocator.get_next_id('accounts')
        
        # Determine account properties
        industry = industry_list[i]
        size = get_account_size(account_id)
        company_name = generate_company_name(industry)
        
        # Generate temporal data
        created_at = get_created_date(i, total_accounts)
        
        # Account status - older accounts more likely to be active
        account_age_days = (datetime.now() - created_at).days
        if account_age_days > 365:
            is_active = random.random() < 0.95  # 95% active for old accounts
        elif account_age_days > 180:
            is_active = random.random() < 0.90  # 90% active for medium age
        else:
            is_active = random.random() < 0.85  # 85% active for new accounts
        
        # Generate domain from company name
        domain = company_name.lower().replace(' ', '').replace('.', '') + '.com'
        
        # Health metrics based on age and activity
        if is_active:
            if account_age_days > 365:
                health_score = random.randint(75, 100)
            else:
                health_score = random.randint(65, 95)
        else:
            health_score = random.randint(20, 60)
        
        account = {
            'id': account_id,
            'name': company_name,
            'email': f"admin@{domain}",
            'created_date': created_at.date(),
            'business_type': industry,
            'account_size': size,  # Store for reference
            'location_count': 0,  # Will be updated by location generator
            'is_active': is_active,
            'health_score': health_score,
            'created_at': created_at,
            'updated_at': created_at + timedelta(days=random.randint(0, 30))
        }
        
        accounts.append(account)
        
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1} accounts...")
    
    return accounts

def insert_accounts(accounts):
    """Insert accounts into the database"""
    print(f"\nInserting {len(accounts)} accounts into database...")
    
    # Map to database columns
    mapped_accounts = []
    for acc in accounts:
        mapped = {
            'id': acc['id'],
            'name': acc['name'],
            'email': acc['email'],
            'created_date': acc['created_date'],
            'business_type': acc['business_type'],
            'location_count': acc['location_count'],
            'created_at': acc['created_at'],
            'updated_at': acc['updated_at']
        }
        mapped_accounts.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_accounts', mapped_accounts)
    return inserted

def save_account_mapping(accounts):
    """Save account mapping to JSON file for use by other generators"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
    
    # Save the full account data with additional metadata
    serializable_accounts = []
    for acc in accounts:
        acc_copy = acc.copy()
        acc_copy['created_at'] = acc_copy['created_at'].isoformat()
        acc_copy['updated_at'] = acc_copy['updated_at'].isoformat()
        acc_copy['created_date'] = acc_copy['created_date'].isoformat()
        serializable_accounts.append(acc_copy)
    
    with open(mapping_file, 'w') as f:
        json.dump(serializable_accounts, f, indent=2)
    
    print(f"\n✓ Saved account mapping to {mapping_file}")

def verify_accounts():
    """Verify the inserted accounts"""
    count = db_helper.get_row_count('app_database_accounts')
    print(f"\n✓ Verification: {count} accounts in database")
    
    # Show distribution statistics
    with db_helper.config.get_cursor() as cursor:
        # Business type distribution
        cursor.execute("""
            SELECT business_type, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_accounts
            GROUP BY business_type
            ORDER BY count DESC
        """)
        dist = cursor.fetchall()
        
        print("\nBusiness type distribution:")
        for row in dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        # Size distribution (based on ID ranges)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN id <= 105 THEN 'small'
                    WHEN id <= 135 THEN 'medium'
                    WHEN id <= 147 THEN 'large'
                    ELSE 'enterprise'
                END as size,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_accounts
            GROUP BY size
            ORDER BY 
                CASE size
                    WHEN 'small' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'large' THEN 3
                    WHEN 'enterprise' THEN 4
                END
        """)
        size_dist = cursor.fetchall()
        
        print("\nAccount size distribution:")
        for row in size_dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Account Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if accounts already exist
    existing_count = db_helper.get_row_count('app_database_accounts')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} accounts already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_accounts')
        else:
            print("Aborting...")
            return
    
    # Generate accounts
    accounts = generate_accounts()
    
    # Save mapping for other generators
    save_account_mapping(accounts)
    
    # Insert into database
    inserted = insert_accounts(accounts)
    
    # Verify
    verify_accounts()
    
    print(f"\n✅ Successfully generated {inserted} accounts!")

if __name__ == "__main__":
    main()