#!/usr/bin/env python3
"""
Wipe all data from the raw schema
"""

import psycopg2
from psycopg2 import sql
import os

def wipe_all_data():
    """Truncate all tables in the raw schema"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'saas_platform_dev'),
        'user': os.getenv('DB_USER', 'saas_user'),
        'password': os.getenv('DB_PASSWORD', 'saas_secure_password_2024')
    }
    
    # Get all tables dynamically
    temp_conn = psycopg2.connect(**db_params)
    cursor = temp_conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'raw' 
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    temp_conn.close()
    
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    try:
        # Try to disable foreign key checks if we have permission
        try:
            cursor.execute("SET session_replication_role = 'replica';")
            replica_mode = True
        except psycopg2.errors.InsufficientPrivilege:
            # If we don't have permission, we'll use CASCADE which handles dependencies
            replica_mode = False
            conn.rollback()  # Clear the error state
        
        # Truncate each table
        for table in tables:
            print(f"Truncating raw.{table}...")
            cursor.execute(f"TRUNCATE TABLE raw.{table} CASCADE;")
        
        # Re-enable foreign key checks if we disabled them
        if replica_mode:
            cursor.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        print("\n✅ All data wiped successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error wiping data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🗑️  Wiping all data from raw schema...")
    print("=" * 50)
    wipe_all_data()