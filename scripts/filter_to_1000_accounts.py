#!/usr/bin/env python3
"""
Filter existing data down to exactly 1000 accounts
"""

import psycopg2
import os

def main():
    """Filter data to exactly 1000 accounts"""
    
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
        print("📊 Current data volumes:")
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        print(f"   - Accounts: {cursor.fetchone()[0]:,}")
        
        # Get the first 1000 account IDs
        print("\n🎯 Selecting first 1000 accounts...")
        cursor.execute("""
            SELECT id FROM raw.app_database_accounts 
            ORDER BY id 
            LIMIT 1000
        """)
        keep_account_ids = [row[0] for row in cursor.fetchall()]
        keep_account_ids_str = ','.join(map(str, keep_account_ids))
        
        # Get location IDs for these accounts
        cursor.execute(f"""
            SELECT id FROM raw.app_database_locations 
            WHERE customer_id IN ({keep_account_ids_str})
        """)
        keep_location_ids = [row[0] for row in cursor.fetchall()]
        keep_location_ids_str = ','.join(map(str, keep_location_ids)) if keep_location_ids else '0'
        
        # Get user IDs for these accounts
        cursor.execute(f"""
            SELECT id FROM raw.app_database_users 
            WHERE customer_id IN ({keep_account_ids_str})
        """)
        keep_user_ids = [row[0] for row in cursor.fetchall()]
        keep_user_ids_str = ','.join(map(str, keep_user_ids)) if keep_user_ids else '0'
        
        # Get device IDs for these locations
        cursor.execute(f"""
            SELECT id FROM raw.app_database_devices 
            WHERE location_id IN ({keep_location_ids_str})
        """)
        keep_device_ids = [row[0] for row in cursor.fetchall()]
        keep_device_ids_str = ','.join(map(str, keep_device_ids)) if keep_device_ids else '0'
        
        print(f"   - Keeping {len(keep_account_ids)} accounts")
        print(f"   - Keeping {len(keep_location_ids)} locations")
        print(f"   - Keeping {len(keep_user_ids)} users")
        print(f"   - Keeping {len(keep_device_ids)} devices")
        
        # Delete data not related to these 1000 accounts
        print("\n🗑️  Removing unrelated data...")
        
        # Disable foreign key checks
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Delete from child tables first
        print("   - Cleaning tap events...")
        cursor.execute(f"DELETE FROM raw.app_database_tap_events WHERE device_id NOT IN ({keep_device_ids_str})")
        
        print("   - Cleaning user sessions...")
        cursor.execute(f"DELETE FROM raw.app_database_user_sessions WHERE user_id NOT IN ({keep_user_ids_str})")
        
        print("   - Cleaning page views...")
        cursor.execute(f"DELETE FROM raw.app_database_page_views WHERE user_id NOT IN ({keep_user_ids_str})")
        
        print("   - Cleaning feature usage...")
        cursor.execute(f"DELETE FROM raw.app_database_feature_usage WHERE user_id NOT IN ({keep_user_ids_str})")
        
        # Delete from main tables
        print("   - Cleaning devices...")
        cursor.execute(f"DELETE FROM raw.app_database_devices WHERE location_id NOT IN ({keep_location_ids_str})")
        
        print("   - Cleaning subscriptions...")
        cursor.execute(f"DELETE FROM raw.app_database_subscriptions WHERE customer_id NOT IN ({keep_account_ids_str})")
        
        print("   - Cleaning users...")
        cursor.execute(f"DELETE FROM raw.app_database_users WHERE customer_id NOT IN ({keep_account_ids_str})")
        
        print("   - Cleaning locations...")
        cursor.execute(f"DELETE FROM raw.app_database_locations WHERE customer_id NOT IN ({keep_account_ids_str})")
        
        print("   - Cleaning accounts...")
        cursor.execute(f"DELETE FROM raw.app_database_accounts WHERE id NOT IN ({keep_account_ids_str})")
        
        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        
        # Print final summary
        print("\n✅ Data filtered successfully!")
        print("\n📊 Final data volumes:")
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        print(f"   - Accounts: {cursor.fetchone()[0]:,}")
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_locations")
        print(f"   - Locations: {cursor.fetchone()[0]:,}")
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_users")
        print(f"   - Users: {cursor.fetchone()[0]:,}")
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_devices")
        print(f"   - Devices: {cursor.fetchone()[0]:,}")
        
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_subscriptions")
        print(f"   - Subscriptions: {cursor.fetchone()[0]:,}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()