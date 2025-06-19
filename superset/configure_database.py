#!/usr/bin/env python3
"""
Superset Database Configuration Script
Automatically configures database connections for the SaaS Platform data
"""

import requests
import json
import time
import sys

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"

# Database connection details
DATABASE_CONFIG = {
    "database_name": "SaaS Platform Database",
    "sqlalchemy_uri": "postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev",
    "expose_in_sqllab": True,
    "allow_ctas": False,
    "allow_cvas": False,
    "allow_dml": False,
    "force_ctas_schema": "",
    "cache_timeout": 0,
    "extra": json.dumps({
        "metadata_params": {},
        "engine_params": {
            "pool_recycle": 3600
        },
        "metadata_cache_timeout": {},
        "schemas_allowed_for_file_upload": []
    })
}

def wait_for_superset():
    """Wait for Superset to be ready"""
    print("🔍 Checking if Superset is ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{SUPERSET_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Superset is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}: Waiting for Superset...")
        time.sleep(2)
    
    print("❌ Superset not ready after waiting")
    return False

def login_and_get_csrf():
    """Login to Superset and get CSRF token"""
    print("🔐 Logging into Superset...")
    
    # Create session
    session = requests.Session()
    
    # Get login page to get CSRF token
    response = session.get(f"{SUPERSET_URL}/login/")
    if response.status_code != 200:
        print(f"❌ Failed to get login page: {response.status_code}")
        return None, None
    
    # Extract CSRF token from response
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrf_token' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    if not csrf_token:
        print("❌ Could not find CSRF token")
        return None, None
    
    # Login
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
        'csrf_token': csrf_token
    }
    
    response = session.post(f"{SUPERSET_URL}/login/", data=login_data)
    if response.status_code == 200 and '/login/' not in response.url:
        print("✅ Successfully logged in!")
        return session, csrf_token
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None, None

def get_api_csrf_token(session):
    """Get CSRF token for API calls"""
    response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/")
    if response.status_code == 200:
        return response.json()['result']
    return None

def check_existing_database(session, csrf_token):
    """Check if database already exists"""
    print("🔍 Checking for existing database connections...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
    if response.status_code == 200:
        databases = response.json()['result']
        for db in databases:
            if db['database_name'] == DATABASE_CONFIG['database_name']:
                print(f"✅ Database '{DATABASE_CONFIG['database_name']}' already exists (ID: {db['id']})")
                return db['id']
    
    print("📝 No existing database found, will create new one")
    return None

def create_database_connection(session, csrf_token):
    """Create database connection in Superset"""
    print("🔗 Creating database connection...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/database/",
        headers=headers,
        json=DATABASE_CONFIG
    )
    
    if response.status_code == 201:
        db_id = response.json()['id']
        print(f"✅ Database connection created successfully (ID: {db_id})")
        return db_id
    else:
        print(f"❌ Failed to create database connection: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_database_connection(session, csrf_token, db_id):
    """Test the database connection"""
    print("🧪 Testing database connection...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    test_data = {
        "uri": DATABASE_CONFIG['sqlalchemy_uri'],
        "database_name": DATABASE_CONFIG['database_name']
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/database/test_connection",
        headers=headers,
        json=test_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('message') == 'OK':
            print("✅ Database connection test successful!")
            return True
        else:
            print(f"⚠️ Database connection test returned: {result}")
            return False
    else:
        print(f"❌ Database connection test failed: {response.status_code}")
        return False

def list_available_tables(session, csrf_token, db_id):
    """List available tables in the database"""
    print("📊 Discovering available tables...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    # Get schemas
    response = session.get(f"{SUPERSET_URL}/api/v1/database/{db_id}/schemas/", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get schemas")
        return []
    
    schemas = response.json()['result']
    if 'public' not in schemas:
        print("⚠️ Public schema not found")
        return []
    
    # Get tables in public schema
    response = session.get(f"{SUPERSET_URL}/api/v1/database/{db_id}/tables/?q=(schema_name:public)", headers=headers)
    if response.status_code == 200:
        tables = response.json()['result']['table_names']
        entity_tables = [t for t in tables if t.startswith('entity_')]
        
        print(f"✅ Found {len(tables)} total tables, {len(entity_tables)} entity tables")
        print("🎯 Key entity tables available:")
        for table in sorted(entity_tables)[:10]:  # Show first 10
            print(f"   • {table}")
        if len(entity_tables) > 10:
            print(f"   ... and {len(entity_tables) - 10} more entity tables")
        
        return tables
    else:
        print("❌ Failed to get tables")
        return []

def main():
    """Main configuration function"""
    print("🚀 Configuring Superset Database Connections")
    print("=" * 50)
    
    # Wait for Superset
    if not wait_for_superset():
        sys.exit(1)
    
    # Login and get session
    session, csrf_token = login_and_get_csrf()
    if not session:
        sys.exit(1)
    
    # Get API CSRF token
    api_csrf_token = get_api_csrf_token(session)
    if not api_csrf_token:
        print("❌ Failed to get API CSRF token")
        sys.exit(1)
    
    print(f"🔑 Got API CSRF token")
    
    # Check if database already exists
    existing_db_id = check_existing_database(session, api_csrf_token)
    
    if existing_db_id:
        db_id = existing_db_id
    else:
        # Create database connection
        db_id = create_database_connection(session, api_csrf_token)
        if not db_id:
            sys.exit(1)
    
    # Test connection
    if test_database_connection(session, api_csrf_token, db_id):
        # List available tables
        tables = list_available_tables(session, api_csrf_token, db_id)
        
        print("\n🎉 Database Configuration Complete!")
        print("=" * 50)
        print(f"✅ Database ID: {db_id}")
        print(f"✅ Connection Name: {DATABASE_CONFIG['database_name']}")
        print(f"✅ Tables Available: {len(tables)}")
        print("\n🎯 Next Steps:")
        print("   1. Go to http://localhost:8088")
        print("   2. Navigate to Datasets to see available tables")
        print("   3. Create charts using your entity tables")
        print("   4. Build dashboards with SaaS metrics")
        
        return True
    else:
        print("❌ Database configuration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
