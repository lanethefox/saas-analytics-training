#!/usr/bin/env python3
"""
Load the newly generated 1000-customer synthetic data into PostgreSQL
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

# Base directory for synthetic data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic')

def load_hubspot_companies(cursor, conn):
    """Load HubSpot companies as accounts"""
    print("Loading HubSpot companies as accounts...")
    
    # First truncate existing data
    cursor.execute("TRUNCATE TABLE raw.app_database_accounts CASCADE")
    
    # Load companies
    with open(os.path.join(DATA_DIR, 'hubspot', 'companies.json'), 'r') as f:
        companies = json.load(f)
    
    # Convert to accounts format
    accounts = []
    for company in companies:
        accounts.append((
            company['id'],
            company['account_id'],
            company['name'],
            company.get('properties', {}).get('industry', 'Unknown'),
            company.get('customer_tier', 4),
            company.get('customer_status', 'active'),
            company.get('created_at'),
            company.get('updated_at')
        ))
    
    # Insert
    insert_query = """
        INSERT INTO raw.app_database_accounts 
        (id, account_id, company_name, industry, customer_tier, customer_status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """
    
    execute_batch(cursor, insert_query, accounts, page_size=1000)
    conn.commit()
    
    count = cursor.rowcount
    print(f"✅ Loaded {len(accounts)} accounts")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
    actual_count = cursor.fetchone()[0]
    print(f"   Verified: {actual_count} accounts in database")

def main():
    """Main execution"""
    conn = None
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Load the companies as accounts
        load_hubspot_companies(cursor, conn)
        
        # Run dbt to refresh entity tables
        print("\nRefreshing entity tables with dbt...")
        os.system("cd /Users/lane/Development/Active/data-platform && dbt run --models entity.entity_customers")
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM entity.entity_customers")
        entity_count = cursor.fetchone()[0]
        print(f"\n✅ Entity customers table now has {entity_count} records")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
