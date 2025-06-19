#!/usr/bin/env python3
"""
Enhanced Superset Setup - Part 1: Core Functions and Dataset Creation
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"
DATABASE_ID = 3

class SupersetClient:
    def __init__(self):
        self.session = None
        self.csrf_token = None
        self.api_csrf_token = None
        self.datasets = {}
        
    def login(self):
        """Login to Superset and get CSRF tokens"""
        print("🔐 Logging into Superset...")
        
        self.session = requests.Session()
        response = self.session.get(f"{SUPERSET_URL}/login/")
        
        # Extract CSRF token
        for line in response.text.split('\n'):
            if 'csrf_token' in line and 'value=' in line:
                self.csrf_token = line.split('value="')[1].split('"')[0]
                break
        
        # Login
        login_data = {
            'username': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD,
            'csrf_token': self.csrf_token
        }
        
        response = self.session.post(f"{SUPERSET_URL}/login/", data=login_data)
        if response.status_code == 200:
            print("✅ Successfully logged in!")
            
            # Get API CSRF token
            response = self.session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/")
            if response.status_code == 200:
                self.api_csrf_token = response.json()['result']
                return True
        
        return False
    
    def get_or_create_dataset(self, schema, table_name, description=""):
        """Get existing dataset or create new one"""
        dataset_key = f"{schema}.{table_name}"
        
        # Check if already processed
        if dataset_key in self.datasets:
            return self.datasets[dataset_key]
        
        # Check existing datasets
        headers = {
            'X-CSRFToken': self.api_csrf_token,
            'Content-Type': 'application/json'
        }
        
        # Search for existing dataset
        response = self.session.get(
            f"{SUPERSET_URL}/api/v1/dataset/",
            headers=headers,
            params={
                'q': json.dumps({
                    'filters': [
                        {'col': 'schema', 'opr': 'eq', 'value': schema},
                        {'col': 'table_name', 'opr': 'eq', 'value': table_name}
                    ]
                })
            }
        )
        
        if response.status_code == 200 and response.json()['count'] > 0:
            dataset_id = response.json()['result'][0]['id']
            self.datasets[dataset_key] = dataset_id
            print(f"   ✅ Found existing dataset: {dataset_key} (ID: {dataset_id})")
            return dataset_id
        
        # Create new dataset
        print(f"📊 Creating dataset: {dataset_key}")
        
        dataset_config = {
            "database": DATABASE_ID,
            "schema": schema,
            "table_name": table_name,
            "description": description
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            headers=headers,
            json=dataset_config
        )
        
        if response.status_code == 201:
            dataset_id = response.json()['id']
            self.datasets[dataset_key] = dataset_id
            print(f"   ✅ Created dataset ID: {dataset_id}")
            
            # Refresh columns for the dataset
            self.refresh_dataset_columns(dataset_id)
            
            return dataset_id
        else:
            print(f"   ❌ Failed to create dataset: {response.status_code}")
            return None
    
    def refresh_dataset_columns(self, dataset_id):
        """Refresh dataset columns from database"""
        headers = {
            'X-CSRFToken': self.api_csrf_token,
            'Content-Type': 'application/json'
        }
        
        response = self.session.put(
            f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}/refresh",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ Refreshed columns for dataset {dataset_id}")
        
    def create_chart(self, config):
        """Create a chart in Superset"""
        headers = {
            'X-CSRFToken': self.api_csrf_token,
            'Content-Type': 'application/json'
        }
        
        # Ensure params is a string if it's a dict
        if 'params' in config and isinstance(config['params'], dict):
            config['params'] = json.dumps(config['params'])
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/chart/",
            headers=headers,
            json=config
        )
        
        if response.status_code == 201:
            chart_id = response.json()['id']
            print(f"   ✅ Created chart: {config['slice_name']} (ID: {chart_id})")
            return chart_id
        else:
            print(f"   ❌ Failed to create chart: {config['slice_name']}")
            print(f"      Status: {response.status_code}")
            print(f"      Response: {response.text}")
            return None
    
    def setup_all_datasets(self):
        """Create all required datasets"""
        print("\n🏗️  Setting up All Datasets")
        print("=" * 50)
        
        # Entity Layer Datasets
        entity_tables = [
            ("entity_customers", "Customer master with health scores, MRR, and engagement metrics"),
            ("entity_devices", "IoT devices with performance and health metrics"),
            ("entity_users", "User profiles with engagement and feature adoption"),
            ("entity_subscriptions", "Subscription lifecycle with revenue metrics"),
            ("entity_locations", "Location operational metrics and performance"),
            ("entity_campaigns", "Marketing campaign performance and attribution"),
            ("entity_features", "Product feature adoption and usage metrics"),
            ("entity_customers_history", "Complete customer change history"),
            ("entity_devices_history", "Device lifecycle and maintenance events"),
            ("entity_users_history", "User behavior and engagement changes"),
            ("entity_subscriptions_history", "Subscription modifications and events"),
            ("entity_customers_daily", "Daily customer metric snapshots"),
            ("entity_devices_hourly", "Hourly device performance metrics"),
            ("entity_users_weekly", "Weekly user engagement summaries"),
            ("entity_subscriptions_monthly", "Monthly subscription cohorts")
        ]
        
        # Mart Layer Datasets
        mart_tables = [
            ("mart_customer_success__health", "Customer health scores and risk analysis"),
            ("mart_sales__pipeline", "Sales pipeline stages and conversion metrics"),
            ("mart_marketing__attribution", "Multi-touch attribution and campaign ROI"),
            ("mart_product__adoption", "Feature adoption and user engagement"),
            ("mart_operations__performance", "Operational KPIs and efficiency metrics"),
            ("mart_device_operations", "Device fleet management dashboard"),
            ("operations_device_monitoring", "Real-time device monitoring metrics")
        ]
        
        # Create Entity datasets
        print("\n📦 Entity Layer:")
        for table, desc in entity_tables:
            self.get_or_create_dataset("entity", table, desc)
        
        # Create Mart datasets
        print("\n🏪 Mart Layer:")
        for table, desc in mart_tables:
            self.get_or_create_dataset("mart", table, desc)
        
        print(f"\n✅ Total datasets configured: {len(self.datasets)}")

def main():
    """Main setup function - Part 1"""
    print("🚀 Superset Setup - Part 1: Datasets")
    print("=" * 50)
    
    # Initialize client
    client = SupersetClient()
    
    # Login
    if not client.login():
        print("❌ Failed to login to Superset")
        sys.exit(1)
    
    # Setup all datasets
    client.setup_all_datasets()
    
    # Save dataset mappings for Part 2
    with open('/tmp/superset_datasets.json', 'w') as f:
        json.dump(client.datasets, f)
    
    print("\n✅ Part 1 Complete - Datasets created")
    print("🎯 Run Part 2 to create charts and dashboards")

if __name__ == "__main__":
    main()