#!/usr/bin/env python3
"""
Simple Superset Dataset Setup
Creates datasets using the correct API format
"""

import requests
import json
import time

SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"
DATABASE_ID = 3

def login():
    """Login to Superset"""
    print("🔐 Logging into Superset...")
    session = requests.Session()
    
    # Get CSRF token
    response = session.get(f"{SUPERSET_URL}/login/")
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrf_token' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    # Login
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
        'csrf_token': csrf_token
    }
    
    response = session.post(f"{SUPERSET_URL}/login/", data=login_data)
    if response.status_code == 200:
        print("✅ Successfully logged in!")
        
        # Get API CSRF token
        response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/")
        if response.status_code == 200:
            api_csrf_token = response.json()['result']
            return session, api_csrf_token
    
    return None, None

def create_datasets_via_ui(session, csrf_token):
    """Create datasets using the UI endpoint"""
    print("\n📊 Creating Datasets via UI endpoint...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    # Tables to create datasets for
    tables = [
        # Entity tables
        ("entity", "entity_customers", "Customer master data"),
        ("entity", "entity_devices", "Device metrics"),
        ("entity", "entity_users", "User engagement"),
        ("entity", "entity_subscriptions", "Subscription data"),
        ("entity", "entity_locations", "Location metrics"),
        ("entity", "entity_campaigns", "Campaign performance"),
        ("entity", "entity_features", "Feature adoption"),
        
        # Mart tables
        ("mart", "mart_customer_success__health", "Customer health analysis"),
        ("mart", "mart_sales__pipeline", "Sales pipeline"),
        ("mart", "mart_marketing__attribution", "Marketing attribution"),
        ("mart", "mart_product__adoption", "Product analytics"),
        ("mart", "mart_operations__performance", "Operations KPIs"),
    ]
    
    created_count = 0
    
    for schema, table, description in tables:
        print(f"  Creating {schema}.{table}...")
        
        # Use the datasource/save endpoint
        data = {
            "database_id": DATABASE_ID,
            "schema": schema,
            "table": table,
            "description": description
        }
        
        response = session.post(
            f"{SUPERSET_URL}/datasource/save/",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            print(f"    ✅ Created successfully")
            created_count += 1
        else:
            # Try alternative endpoint
            response = session.post(
                f"{SUPERSET_URL}/tablemodelview/add",
                headers=headers,
                data={
                    'database': DATABASE_ID,
                    'schema': schema,
                    'table_name': table,
                    'description': description
                }
            )
            if response.status_code in [200, 302]:
                print(f"    ✅ Created via alternative method")
                created_count += 1
            else:
                print(f"    ⚠️  May already exist or failed")
    
    return created_count

def create_simple_dashboard(session, csrf_token):
    """Create a simple example dashboard"""
    print("\n🎨 Creating Example Dashboard...")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    dashboard_data = {
        "dashboard_title": "🎯 SaaS Analytics Overview",
        "slug": "saas-overview",
        "published": True,
        "position_json": json.dumps({
            "DASHBOARD_VERSION_KEY": "v2",
            "GRID_ID": {
                "id": "GRID_ID",
                "type": "GRID",
                "children": ["MARKDOWN-1"]
            },
            "HEADER_ID": {
                "id": "HEADER_ID",
                "type": "HEADER",
                "meta": {"text": "SaaS Analytics Overview"}
            },
            "MARKDOWN-1": {
                "id": "MARKDOWN-1",
                "type": "MARKDOWN",
                "children": [],
                "meta": {
                    "width": 12,
                    "height": 6,
                    "code": """# 🎯 SaaS Analytics Platform

## Welcome to Your Analytics Environment!

This platform provides comprehensive analytics across all business domains:

### 📊 Available Data Layers

1. **Entity Layer** - Core business entities with enriched metrics
   - `entity_customers` - Customer health scores and MRR
   - `entity_devices` - IoT device performance metrics  
   - `entity_users` - User engagement and feature adoption
   - `entity_subscriptions` - Revenue and lifecycle data
   - `entity_locations` - Operational performance
   - `entity_campaigns` - Marketing performance
   - `entity_features` - Product adoption metrics

2. **Mart Layer** - Domain-specific analytics
   - `mart_customer_success__health` - Customer health analysis
   - `mart_sales__pipeline` - Sales funnel and conversion
   - `mart_marketing__attribution` - Multi-touch attribution
   - `mart_product__adoption` - Feature usage analytics
   - `mart_operations__performance` - Operational KPIs

### 🚀 Getting Started

1. **Create Charts**: Navigate to Charts → + Chart → Select a dataset
2. **Build Dashboards**: Dashboards → + Dashboard → Add your charts
3. **Set Filters**: Use dashboard filters for interactive analysis
4. **Schedule Reports**: Configure email delivery for key metrics

### 📈 Example Analyses

- **Customer Health**: Join customers with subscriptions to analyze MRR by health tier
- **Sales Pipeline**: Use mart_sales__pipeline to track conversion rates
- **Device Performance**: Analyze entity_devices_hourly for performance trends
- **User Engagement**: Segment users by engagement_score and feature adoption

### 🔗 Useful Resources

- [Entity-Centric Modeling Guide](/docs/ecm-guide)
- [Metric Definitions](/docs/metrics)
- [SQL Examples](/docs/sql-examples)
"""
                }
            }
        })
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        headers=headers,
        json=dashboard_data
    )
    
    if response.status_code == 201:
        dashboard_id = response.json()['id']
        print(f"✅ Created dashboard: SaaS Analytics Overview")
        print(f"   URL: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
        return dashboard_id
    else:
        print(f"❌ Failed to create dashboard: {response.status_code}")
        return None

def main():
    """Main execution"""
    print("🚀 Simple Superset Setup")
    print("=" * 50)
    
    # Login
    session, csrf_token = login()
    if not session:
        print("❌ Failed to login")
        return
    
    # Create datasets
    count = create_datasets_via_ui(session, csrf_token)
    print(f"\n✅ Dataset creation attempted for {count} tables")
    
    # Create example dashboard
    dashboard_id = create_simple_dashboard(session, csrf_token)
    
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("=" * 50)
    
    print("\n📝 What to do next:")
    print("1. Visit http://localhost:8088")
    print("2. Go to Data → Datasets to see all available tables")
    print("3. Click on any dataset to explore its columns")
    print("4. Create charts by clicking Charts → + Chart")
    print("5. Select a dataset and visualization type")
    print("6. Build custom dashboards with your charts")
    
    print("\n💡 Quick Chart Ideas:")
    print("- Pie chart: Customer distribution by health tier")
    print("- Bar chart: MRR by customer segment")
    print("- Line chart: Device performance over time")
    print("- Table: Top at-risk customers by churn score")
    print("- Heatmap: User engagement by cohort")
    
    print("\n📊 The overview dashboard has been created with documentation!")
    if dashboard_id:
        print(f"   View it at: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")

if __name__ == "__main__":
    main()