#!/usr/bin/env python3
"""
Generate synthetic Stripe customers data for the bar management SaaS platform.

This module creates Stripe customer records with:
- 1:1 mapping with accounts
- Matching email patterns
- Metadata containing account_id mapping
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

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
def generate_stripe_customers(accounts):
    """Generate Stripe customer records for all accounts"""
    stripe_customers = []
    
    print(f"Generating {len(accounts):,} Stripe customers...")
    
    for account in accounts:
        # Create Stripe customer ID format: cus_XXXXXXXXXXXXX
        stripe_id = f"cus_{account['internal_id'].replace('-', '')[:16]}"
        
        # Metadata as JSON
        metadata = {
            'account_id': str(account['id']),
            'company_name': account['company_name'],
            'tier': account['subscription_tier']
        }
        
        customer = {
            'id': account['id'],  # Use same ID as account
            'stripe_customer_id': stripe_id,
            'account_id': account['id'],
            'email': account['billing_email'],
            'name': account['company_name'],
            'description': f"{account['company_name']} - {account['industry']}",
            'phone': None,  # Will be populated from users
            'metadata': json.dumps(metadata),
            'currency': 'usd',
            'delinquent': False,  # Most customers are not delinquent
            'created_at': account['created_at'],
            'updated_at': account['updated_at']
        }
        
        stripe_customers.append(customer)
    
    return stripe_customers

def insert_stripe_customers(customers):
    """Insert Stripe customers into the database"""
    print(f"\nInserting {len(customers):,} Stripe customers into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'stripe_customers'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.stripe_customers:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_customers = []
    for customer in customers:
        mapped = {
            'id': customer['stripe_customer_id'],
            'email': customer['email'],
            'name': customer['name'],
            'description': customer['description'],
            'phone': customer['phone'],
            'address': json.dumps({}),  # Empty address for now
            'created': customer['created_at'],
            'currency': customer['currency'],
            'delinquent': customer['delinquent'],
            'invoice_prefix': customer['stripe_customer_id'][:8].upper(),
            'livemode': True,  # Assume production mode
            'metadata': customer['metadata'],
            'shipping': json.dumps({}),  # Empty shipping for now
            'tax_exempt': 'none',
            'created_at': customer['created_at']
        }
        mapped_customers.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('stripe_customers', mapped_customers)
    
    return inserted

def verify_stripe_customers():
    """Verify the inserted Stripe customers"""
    count = db_helper.get_row_count('stripe_customers')
    print(f"\n✓ Verification: {count:,} Stripe customers in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT * FROM raw.stripe_customers
            ORDER BY created DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample Stripe customers:")
        for customer in samples:
            print(f"  {customer['id']} - {customer['name']} - {customer['email']}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Customer Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if Stripe customers already exist
    existing_count = db_helper.get_row_count('stripe_customers')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} Stripe customers already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_customers')
        else:
            print("Aborting...")
            return
    
    # Load accounts
    accounts = load_accounts()
    print(f"\n✓ Loaded {len(accounts):,} accounts")
    
    # Generate Stripe customers
    stripe_customers = generate_stripe_customers(accounts)
    
    # Insert into database
    inserted = insert_stripe_customers(stripe_customers)
    
    # Verify
    verify_stripe_customers()
    
    print(f"\n✅ Successfully generated {inserted:,} Stripe customers!")

if __name__ == "__main__":
    main()
