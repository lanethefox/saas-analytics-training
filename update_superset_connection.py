#!/usr/bin/env python3
"""
Update Superset Database Connection Script
Updates the existing database connection to use the correct credentials
"""

import requests
import json
import time
import sys

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"

# Updated database connection details for Docker container
DATABASE_CONFIG = {
    "database_name": "SaaS Platform Analytics",
    "sqlalchemy_uri": "postgresql://saas_user:saas_secure_password_2024@host.docker.internal:5432/saas_platform_dev",
    "expose_in_sqllab": True,
    "allow_ctas": True,
    "allow_cvas": True,
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

def get_all_databases(session, csrf_token):
    """Get all existing database connections"""
    print("🔍 Getting all database connections...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
    if response.status_code == 200:
        databases = response.json()['result']
        print(f"✅ Found {len(databases)} database connections")
        for db in databases:
            print(f"   • ID: {db['id']}, Name: {db['database_name']}")
        return databases
    
    print("❌ Failed to get databases")
    return []

def delete_database(session, csrf_token, db_id):
    """Delete a database connection"""
    print(f"🗑️  Deleting database ID: {db_id}...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.delete(f"{SUPERSET_URL}/api/v1/database/{db_id}", headers=headers)
    if response.status_code == 200:
        print(f"✅ Deleted database ID: {db_id}")
        return True
    else:
        print(f"❌ Failed to delete database: {response.status_code}")
        return False

def create_database_connection(session, csrf_token):
    """Create database connection in Superset"""
    print("🔗 Creating new database connection...")
    
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

def test_database_connection(session, csrf_token):
    """Test the database connection"""
    print("🧪 Testing database connection...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    test_data = {
        "engine": "postgresql",
        "driver": "psycopg2",
        "username": "saas_user",
        "password": "saas_secure_password_2024",
        "host": "host.docker.internal",
        "port": 5432,
        "database": "saas_platform_dev"
    }
    
    response = session.post(
        f"{SUPERSET_URL}/superset/testconn",
        headers=headers,
        json=test_data
    )
    
    if response.status_code == 200:
        print("✅ Database connection test successful!")
        return True
    else:
        print(f"❌ Database connection test failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def list_schemas_and_tables(session, csrf_token, db_id):
    """List schemas and tables in the database"""
    print("📊 Discovering schemas and tables...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    # Get schemas
    response = session.get(f"{SUPERSET_URL}/api/v1/database/{db_id}/schemas/", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get schemas")
        return
    
    schemas = response.json()['result']
    print(f"✅ Found {len(schemas)} schemas:")
    for schema in sorted(schemas):
        if schema not in ['information_schema', 'pg_catalog']:
            print(f"   • {schema}")
    
    # Get tables in key schemas
    for schema in ['raw', 'staging', 'intermediate', 'entity', 'mart']:
        if schema in schemas:
            params = {'schema_name': schema}
            response = session.get(
                f"{SUPERSET_URL}/api/v1/database/{db_id}/tables/",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                tables = response.json().get('tables', [])
                print(f"\n📁 Schema '{schema}' has {len(tables)} tables")

def main():
    """Main configuration function"""
    print("🚀 Updating Superset Database Connection")
    print("=" * 50)
    
    # Login and get session
    session, csrf_token = login_and_get_csrf()
    if not session:
        sys.exit(1)
    
    # Get API CSRF token
    api_csrf_token = get_api_csrf_token(session)
    if not api_csrf_token:
        print("❌ Failed to get API CSRF token")
        sys.exit(1)
    
    # Get all existing databases
    databases = get_all_databases(session, api_csrf_token)
    
    # Delete existing connections (optional - clean slate approach)
    for db in databases:
        if 'SaaS' in db['database_name'] or 'saas' in db['database_name'].lower():
            delete_database(session, api_csrf_token, db['id'])
    
    # Create new connection with correct settings
    db_id = create_database_connection(session, api_csrf_token)
    if not db_id:
        sys.exit(1)
    
    # List available schemas and tables
    list_schemas_and_tables(session, api_csrf_token, db_id)
    
    print("\n🎉 Database Configuration Complete!")
    print("=" * 50)
    print(f"✅ Database ID: {db_id}")
    print(f"✅ Connection Name: {DATABASE_CONFIG['database_name']}")
    print(f"✅ Connection String: postgresql://saas_user:****@host.docker.internal:5432/saas_platform_dev")
    print("\n🎯 Next Steps:")
    print("   1. Go to http://localhost:8088")
    print("   2. Login with admin/admin_password_2024")
    print("   3. Navigate to Data > Databases to see the connection")
    print("   4. Go to Data > Datasets to add tables")
    print("   5. Create charts and dashboards!")

if __name__ == "__main__":
    main()
