#!/usr/bin/env python3
"""
Load exactly 1000 accounts and proportional data
"""

import psycopg2
import os

def main():
    """Load small dataset with exactly 1000 accounts"""
    
    # Database connection
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'saas_platform_dev'),
        'user': os.getenv('DB_USER', 'saas_user'),
        'password': os.getenv('DB_PASSWORD', 'saas_secure_password_2024')
    }
    
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    try:
        print("🗑️  Wiping existing data...")
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Get all tables in raw schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Truncate all tables
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE raw.{table} CASCADE;")
        
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        
        print("✅ Data wiped successfully")
        
        # Now copy exactly 1000 accounts
        print("\n📊 Loading 1000 accounts...")
        cursor.execute("""
            INSERT INTO raw.app_database_accounts 
            SELECT * FROM (
                SELECT * FROM raw.app_database_accounts 
                ORDER BY id 
                LIMIT 1000
            ) accounts;
        """)
        
        # Get the account IDs
        cursor.execute("SELECT id FROM raw.app_database_accounts")
        account_ids = [row[0] for row in cursor.fetchall()]
        account_ids_str = ','.join(map(str, account_ids))
        
        print("📊 Loading related data...")
        
        # Load locations for these accounts
        cursor.execute(f"""
            INSERT INTO raw.app_database_locations
            SELECT * FROM raw.app_database_locations 
            WHERE account_id IN ({account_ids_str})
        """)
        
        # Load users for these accounts
        cursor.execute(f"""
            INSERT INTO raw.app_database_users
            SELECT * FROM raw.app_database_users 
            WHERE account_id IN ({account_ids_str})
        """)
        
        # Get location IDs
        cursor.execute("SELECT id FROM raw.app_database_locations")
        location_ids = [row[0] for row in cursor.fetchall()]
        location_ids_str = ','.join(map(str, location_ids))
        
        # Load devices for these locations
        cursor.execute(f"""
            INSERT INTO raw.app_database_devices
            SELECT * FROM raw.app_database_devices 
            WHERE location_id IN ({location_ids_str})
        """)
        
        # Load subscriptions for these accounts
        cursor.execute(f"""
            INSERT INTO raw.app_database_subscriptions
            SELECT * FROM raw.app_database_subscriptions 
            WHERE account_id IN ({account_ids_str})
        """)
        
        conn.commit()
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        accounts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_locations")
        locations_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_devices")
        devices_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_subscriptions")
        subscriptions_count = cursor.fetchone()[0]
        
        print(f"\n✅ Small dataset loaded successfully!")
        print(f"   - Accounts: {accounts_count:,}")
        print(f"   - Locations: {locations_count:,}")
        print(f"   - Users: {users_count:,}")
        print(f"   - Devices: {devices_count:,}")
        print(f"   - Subscriptions: {subscriptions_count:,}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()