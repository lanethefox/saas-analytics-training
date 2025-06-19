#!/usr/bin/env python3
"""
Convert HubSpot companies to app_database_accounts format and load
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

def convert_and_load_accounts():
    """Convert HubSpot companies to accounts and load"""
    
    # Load HubSpot companies
    with open(os.path.join(DATA_DIR, 'hubspot', 'companies.json'), 'r') as f:
        companies = json.load(f)
    
    # Convert to accounts format
    accounts = []
    for i, company in enumerate(companies):
        account = {
            'id': i,  # Use sequential IDs starting from 0
            'name': company['name'],
            'email': company.get('email', f'contact{i}@example.com'),
            'created_date': company.get('created_date', '2024-01-01'),
            'business_type': company.get('business_type', 'Bar'),
            'location_count': company.get('location_count', 1)
        }
        accounts.append(account)
    
    # Save as accounts.json
    accounts_path = os.path.join(DATA_DIR, 'devices', 'accounts.json')
    with open(accounts_path, 'w') as f:
        json.dump(accounts, f, indent=2)
    
    print(f"✅ Created {accounts_path} with {len(accounts)} accounts")
    
    # Now load into database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Truncate existing data
        cursor.execute("TRUNCATE TABLE raw.app_database_accounts CASCADE")
        
        # Prepare data for insertion
        values = []
        for acc in accounts:
            values.append((
                acc['id'],
                acc['name'],
                acc['email'],
                acc['created_date'],
                acc['business_type'],
                acc['location_count']
            ))
        
        # Insert
        insert_query = """
            INSERT INTO raw.app_database_accounts 
            (id, name, email, created_date, business_type, location_count)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        execute_batch(cursor, insert_query, values, page_size=1000)
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        count = cursor.fetchone()[0]
        print(f"✅ Loaded {count} accounts into raw.app_database_accounts")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    convert_and_load_accounts()
