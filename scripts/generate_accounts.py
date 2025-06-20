#!/usr/bin/env python3
"""
Generate synthetic accounts data for the bar management SaaS platform.

This module creates realistic customer accounts with:
- Industry distribution (Restaurant 40%, Bar 30%, Hotel 20%, Other 10%)
- Subscription tiers (Basic 50%, Pro 35%, Enterprise 15%)
- MRR values correlated with tier
- Employee counts based on tier
- Created dates spanning 5 years with growth curve
"""

import sys
import os
import random
import uuid
import json
from datetime import datetime, timedelta
from faker import Faker
import psycopg2.extras

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducibility
random.seed(42)

# Business configuration
INDUSTRIES = [
    ('Restaurant', 0.40),
    ('Bar', 0.30),
    ('Hotel', 0.20),
    ('Retail', 0.05),
    ('Other', 0.05)
]

SUBSCRIPTION_TIERS = [
    ('basic', 0.50, 299, 999),      # tier, probability, min_mrr, max_mrr
    ('pro', 0.35, 999, 2999),
    ('enterprise', 0.15, 2999, 9999)
]

# Company name patterns by industry
COMPANY_PATTERNS = {
    'Restaurant': [
        "{} Kitchen", "{} Bistro", "{} Grill", "{} Cafe",
        "{} Restaurant", "{} Diner", "{} Eatery", "{} Table"
    ],
    'Bar': [
        "{} Tavern", "{} Pub", "{} Lounge", "{} Bar",
        "{} Club", "{} Brewery", "{} Taproom", "{} Saloon"
    ],
    'Hotel': [
        "{} Hotel", "{} Inn", "{} Resort", "{} Lodge",
        "{} Suites", "{} Plaza", "{} Arms", "{} House"
    ],
    'Retail': [
        "{} Store", "{} Market", "{} Shop", "{} Emporium",
        "{} Boutique", "{} Outlet", "{} Gallery", "{} Trading"
    ],
    'Other': [
        "{} LLC", "{} Inc", "{} Group", "{} Services",
        "{} Solutions", "{} Company", "{} Enterprises", "{} Associates"
    ]
}

def weighted_choice(choices):
    """Make a weighted random choice"""
    population = [item[0] for item in choices]
    weights = [item[1] for item in choices]
    return random.choices(population, weights=weights)[0]

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

def get_employee_count(tier):
    """Get employee count based on subscription tier"""
    if tier == 'basic':
        return random.randint(5, 50)
    elif tier == 'pro':
        return random.randint(25, 150)
    else:  # enterprise
        return random.randint(100, 500)

def get_created_date():
    """Generate created date with growth curve over 5 years"""
    # More recent accounts are more likely (exponential growth)
    days_ago = int(random.expovariate(1/365) * 5)  # Lambda = 1/365 for ~1 year average
    days_ago = min(days_ago, 5 * 365)  # Cap at 5 years
    return datetime.now() - timedelta(days=days_ago)

def generate_accounts(num_accounts):
    """Generate synthetic account data"""
    accounts = []
    
    print(f"Generating {num_accounts:,} accounts...")
    
    for i in range(num_accounts):
        # Generate base account data
        account_id = i + 1  # Sequential ID for DB
        internal_id = str(uuid.uuid4())  # Keep for reference
        industry = weighted_choice(INDUSTRIES)
        company_name = generate_company_name(industry)
        
        # Subscription and financial data
        tier_data = weighted_choice([(t[0], t[1]) for t in SUBSCRIPTION_TIERS])
        tier = tier_data
        tier_info = next(t for t in SUBSCRIPTION_TIERS if t[0] == tier)
        mrr = random.randint(tier_info[2], tier_info[3])
        
        # Account details
        created_at = get_created_date()
        is_active = random.random() < 0.90  # 90% active accounts
        employee_count = get_employee_count(tier)
        
        # Generate domain from company name
        domain = company_name.lower().replace(' ', '').replace('.', '') + '.com'
        
        # Health metrics (more complex logic could be added)
        health_score = random.randint(60, 100) if is_active else random.randint(20, 60)
        
        account = {
            'id': account_id,
            'internal_id': internal_id,
            'company_name': company_name,
            'industry': industry,
            'subscription_tier': tier,
            'monthly_recurring_revenue': mrr,
            'employee_count': employee_count,
            'created_at': created_at,
            'is_active': is_active,
            'health_score': health_score,
            'primary_contact_email': f"admin@{domain}",
            'billing_email': f"billing@{domain}",
            'website': f"https://www.{domain}",
            'updated_at': created_at + timedelta(days=random.randint(0, 30))
        }
        
        accounts.append(account)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1:,} accounts...")
    
    return accounts

def insert_accounts(accounts):
    """Insert accounts into the database"""
    print(f"\nInserting {len(accounts):,} accounts into database...")
    
    # First, let's check the actual table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_accounts'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.app_database_accounts:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to the actual table columns
    mapped_accounts = []
    for i, acc in enumerate(accounts):
        mapped = {
            'id': i + 1,  # Sequential ID starting from 1
            'name': acc['company_name'],
            'email': acc['primary_contact_email'],
            'created_date': acc['created_at'].date(),
            'business_type': acc['industry'],
            'location_count': random.randint(1, 5),  # Will be updated when we create locations
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
    
    # Save the full account data
    with open(mapping_file, 'w') as f:
        # Convert datetime objects to strings
        serializable_accounts = []
        for acc in accounts:
            acc_copy = acc.copy()
            acc_copy['created_at'] = acc_copy['created_at'].isoformat()
            acc_copy['updated_at'] = acc_copy['updated_at'].isoformat()
            serializable_accounts.append(acc_copy)
        
        json.dump(serializable_accounts, f, indent=2)
    
    print(f"\n✓ Saved account mapping to {mapping_file}")

def verify_accounts():
    """Verify the inserted accounts"""
    count = db_helper.get_row_count('app_database_accounts')
    print(f"\n✓ Verification: {count:,} accounts in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT * FROM raw.app_database_accounts 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample accounts (most recent):")
        for acc in samples:
            print(f"  {acc['name']} - {acc['business_type']} - {acc['location_count']} locations")
    
    # Show distribution statistics
    with db_helper.config.get_cursor() as cursor:
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

def main():
    """Main execution function"""
    print("=" * 60)
    print("Account Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if accounts already exist
    existing_count = db_helper.get_row_count('app_database_accounts')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} accounts already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_accounts')
        else:
            print("Aborting...")
            return
    
    # Generate accounts
    accounts = generate_accounts(current_env.accounts)
    
    # Save mapping for other generators
    save_account_mapping(accounts)
    
    # Insert into database
    inserted = insert_accounts(accounts)
    
    # Verify
    verify_accounts()
    
    print(f"\n✅ Successfully generated {inserted:,} accounts!")

if __name__ == "__main__":
    main()
