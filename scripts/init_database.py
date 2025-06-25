#!/usr/bin/env python3
"""
Initialize PostgreSQL database for the SaaS platform.
Creates database and user if they don't exist.
"""

import psycopg2
from psycopg2 import sql
import os
import sys
import argparse

# Database configuration
ADMIN_DB = 'postgres'  # Default admin database
TARGET_DB = os.getenv('POSTGRES_DB', 'saas_platform_dev')
DB_USER = os.getenv('POSTGRES_USER', 'saas_user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'saas_secure_password_2024')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

# Admin credentials (for creating database/user)
ADMIN_USER = os.getenv('POSTGRES_ADMIN_USER', 'postgres')
ADMIN_PASSWORD = os.getenv('POSTGRES_ADMIN_PASSWORD', 'postgres')

def check_database_exists(cursor, dbname):
    """Check if database exists"""
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (dbname,)
    )
    return cursor.fetchone() is not None

def check_user_exists(cursor, username):
    """Check if user exists"""
    cursor.execute(
        "SELECT 1 FROM pg_user WHERE usename = %s",
        (username,)
    )
    return cursor.fetchone() is not None

def create_database(cursor, dbname):
    """Create database"""
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier(dbname)
    ))
    print(f"✅ Created database: {dbname}")

def create_user(cursor, username, password):
    """Create user with password"""
    cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
        sql.Identifier(username)
    ), (password,))
    print(f"✅ Created user: {username}")

def grant_privileges(cursor, dbname, username):
    """Grant all privileges on database to user"""
    cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
        sql.Identifier(dbname),
        sql.Identifier(username)
    ))
    print(f"✅ Granted privileges on {dbname} to {username}")

def test_connection(dbname, username, password, host, port):
    """Test connection with created credentials"""
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=username,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect with new credentials: {e}")
        return False

def main():
    """Initialize database"""
    parser = argparse.ArgumentParser(description='Initialize PostgreSQL database')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check if database exists, don\'t create')
    args = parser.parse_args()
    
    print("🔧 PostgreSQL Database Initialization")
    print("=" * 50)
    print(f"Target database: {TARGET_DB}")
    print(f"Target user: {DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("=" * 50)
    
    # Connect as admin user
    try:
        print(f"\n📡 Connecting as admin user '{ADMIN_USER}'...")
        admin_conn = psycopg2.connect(
            dbname=ADMIN_DB,
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        admin_conn.autocommit = True
        cursor = admin_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect as admin: {e}")
        print("\nMake sure PostgreSQL is running and admin credentials are correct:")
        print(f"  POSTGRES_ADMIN_USER={ADMIN_USER}")
        print(f"  POSTGRES_ADMIN_PASSWORD=***")
        sys.exit(1)
    
    try:
        # Check if database exists
        db_exists = check_database_exists(cursor, TARGET_DB)
        user_exists = check_user_exists(cursor, DB_USER)
        
        if args.check_only:
            # Check-only mode
            if db_exists and user_exists:
                print(f"\n✅ Database '{TARGET_DB}' exists")
                print(f"✅ User '{DB_USER}' exists")
                sys.exit(0)
            else:
                if not db_exists:
                    print(f"\n❌ Database '{TARGET_DB}' does not exist")
                if not user_exists:
                    print(f"❌ User '{DB_USER}' does not exist")
                sys.exit(1)
        
        # Create user if needed
        if not user_exists:
            print(f"\n🔨 Creating user '{DB_USER}'...")
            create_user(cursor, DB_USER, DB_PASSWORD)
        else:
            print(f"\n✅ User '{DB_USER}' already exists")
        
        # Create database if needed
        if not db_exists:
            print(f"\n🔨 Creating database '{TARGET_DB}'...")
            create_database(cursor, TARGET_DB)
            
            # Grant privileges
            print(f"\n🔐 Granting privileges...")
            grant_privileges(cursor, TARGET_DB, DB_USER)
        else:
            print(f"\n✅ Database '{TARGET_DB}' already exists")
            
            # Ensure user has privileges even if database existed
            print(f"\n🔐 Ensuring privileges...")
            grant_privileges(cursor, TARGET_DB, DB_USER)
        
        # Test connection
        print(f"\n🧪 Testing connection with user credentials...")
        if test_connection(TARGET_DB, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
            print("✅ Successfully connected with user credentials")
        else:
            print("❌ Failed to connect with user credentials")
            sys.exit(1)
        
        print(f"\n🎉 Database initialization complete!")
        print(f"   Database: {TARGET_DB}")
        print(f"   User: {DB_USER}")
        print(f"   Ready for schema deployment")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        admin_conn.close()

if __name__ == "__main__":
    main()