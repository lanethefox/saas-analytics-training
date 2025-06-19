#!/usr/bin/env python3
"""
Populate app_database_accounts from HubSpot companies data
"""

import psycopg2
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

def populate_accounts():
    """Copy HubSpot companies to app_database_accounts"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # First, clear any existing data
        cursor.execute("TRUNCATE TABLE raw.app_database_accounts CASCADE")
        
        # Insert from HubSpot companies
        cursor.execute("""
            INSERT INTO raw.app_database_accounts (
                id, 
                name, 
                email,
                created_date,
                business_type,
                location_count
            )
            SELECT 
                CAST(SUBSTRING(id FROM 2) AS INTEGER) as id,  -- Remove first char and cast
                COALESCE(properties->>'name', 'Unknown Company') as name,
                properties->>'email' as email,
                CAST(properties->>'createdate' AS DATE) as created_date,
                properties->>'business_type' as business_type,
                CAST(COALESCE(properties->>'location_count', '1') AS INTEGER) as location_count
            FROM raw.hubspot_companies
            ON CONFLICT (id) DO NOTHING
        """)
        
        conn.commit()
        
        # Get count
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        count = cursor.fetchone()[0]
        
        print(f"✅ Successfully populated app_database_accounts with {count} records")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_accounts()
