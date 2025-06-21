#!/usr/bin/env python3
"""Quick database connection test"""

import psycopg2
import sys

def test_connection():
    """Test PostgreSQL connection"""
    config = {
        'host': 'localhost',
        'port': 15432,
        'database': 'saas_platform_dev',
        'user': 'saas_user',
        'password': 'saas_secure_password_2024'
    }
    
    try:
        print("Testing PostgreSQL connection...")
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ Connected successfully!")
        print(f"  PostgreSQL version: {version}")
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            LIMIT 10;
        """)
        tables = cur.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n⚠ No tables found (database might be empty)")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)