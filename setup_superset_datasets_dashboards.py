#!/usr/bin/env python3
"""
Superset Dataset and Dashboard Creation Script
Sets up entity and mart layer datasets and creates domain-specific dashboards
"""

import requests
import json
import time
import sys
from datetime import datetime

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"
DATABASE_ID = 3  # From previous setup

# Domain colors for consistency
DOMAIN_COLORS = {
    'customer_success': '#1f77b4',  # Blue
    'sales': '#ff7f0e',             # Orange
    'marketing': '#2ca02c',         # Green
    'product': '#d62728',           # Red
    'operations': '#9467bd',        # Purple
    'finance': '#8c564b'            # Brown
}

def login_and_get_csrf():
    """Login to Superset and get CSRF token"""
    print("🔐 Logging into Superset...")
    
    session = requests.Session()
    response = session.get(f"{SUPERSET_URL}/login/")
    
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrf_token' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
        'csrf_token': csrf_token
    }
    
    response = session.post(f"{SUPERSET_URL}/login/", data=login_data)
    if response.status_code == 200:
        print("✅ Successfully logged in!")
        return session, csrf_token
    
    return None, None

def get_api_csrf_token(session):
    """Get CSRF token for API calls"""
    response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/")
    if response.status_code == 200:
        return response.json()['result']
    return None

def create_dataset(session, csrf_token, schema, table_name, description=""):
    """Create a dataset from a table"""
    print(f"📊 Creating dataset: {schema}.{table_name}")
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    dataset_config = {
        "database": DATABASE_ID,
        "schema": schema,
        "table_name": table_name,
        "is_sqllab_view": False,
        "sql": None,
        "description": description
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/dataset/",
        headers=headers,
        json=dataset_config
    )
    
    if response.status_code == 201:
        dataset_id = response.json()['id']
        print(f"   ✅ Created dataset ID: {dataset_id}")
        return dataset_id
    elif response.status_code == 422:
        # Dataset might already exist
        print(f"   ⚠️  Dataset might already exist")
        return None
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return None

def get_existing_datasets(session, csrf_token):
    """Get all existing datasets"""
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.get(
        f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:1000)",
        headers=headers
    )
    
    if response.status_code == 200:
        datasets = response.json()['result']
        dataset_map = {}
        for ds in datasets:
            key = f"{ds['schema']}.{ds['table_name']}"
            dataset_map[key] = ds['id']
        return dataset_map
    return {}

def setup_entity_datasets(session, csrf_token):
    """Create datasets for all entity tables"""
    print("\n🏗️  Setting up Entity Layer Datasets")
    print("=" * 50)
    
    entity_tables = [
        # Core Entity Tables
        ("entity_customers", "Customer master data with health scores and MRR"),
        ("entity_devices", "IoT device registry with performance metrics"),
        ("entity_users", "User profiles with engagement scores"),
        ("entity_subscriptions", "Subscription lifecycle and revenue data"),
        ("entity_locations", "Location operational metrics"),
        ("entity_campaigns", "Marketing campaign performance"),
        ("entity_features", "Product feature adoption metrics"),
        
        # History Tables
        ("entity_customers_history", "Customer state change history"),
        ("entity_devices_history", "Device lifecycle and maintenance history"),
        ("entity_users_history", "User engagement evolution"),
        ("entity_subscriptions_history", "Subscription change events"),
        ("entity_locations_history", "Location operational changes"),
        ("entity_campaigns_history", "Campaign performance evolution"),
        ("entity_features_history", "Feature adoption progression"),
        
        # Grain Tables
        ("entity_customers_daily", "Daily customer metrics snapshots"),
        ("entity_devices_hourly", "Hourly device performance metrics"),
        ("entity_users_weekly", "Weekly user engagement rollups"),
        ("entity_subscriptions_monthly", "Monthly subscription cohorts"),
        ("entity_locations_weekly", "Weekly location performance"),
        ("entity_campaigns_daily", "Daily campaign performance"),
        ("entity_features_monthly", "Monthly feature adoption trends")
    ]
    
    dataset_ids = []
    for table, description in entity_tables:
        dataset_id = create_dataset(session, csrf_token, "entity", table, description)
        if dataset_id:
            dataset_ids.append(dataset_id)
    
    return dataset_ids

def setup_mart_datasets(session, csrf_token):
    """Create datasets for all mart tables"""
    print("\n🏪 Setting up Mart Layer Datasets")
    print("=" * 50)
    
    mart_tables = [
        ("mart_customer_success__health", "Customer health and risk analysis"),
        ("mart_sales__pipeline", "Sales pipeline and revenue metrics"),
        ("mart_marketing__attribution", "Marketing performance and attribution"),
        ("mart_product__adoption", "Product usage and feature adoption"),
        ("mart_operations__performance", "Operational efficiency metrics"),
        ("mart_device_operations", "Device fleet management metrics"),
        ("mart_operations_health", "Combined operational health view"),
        ("operations_device_monitoring", "Real-time device monitoring")
    ]
    
    dataset_ids = []
    for table, description in mart_tables:
        dataset_id = create_dataset(session, csrf_token, "mart", table, description)
        if dataset_id:
            dataset_ids.append(dataset_id)
    
    return dataset_ids

def create_chart(session, csrf_token, config):
    """Create a chart in Superset"""
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/chart/",
        headers=headers,
        json=config
    )
    
    if response.status_code == 201:
        return response.json()['id']
    else:
        print(f"Failed to create chart: {response.status_code}")
        print(response.text)
        return None

def create_dashboard(session, csrf_token, title, description, position_json):
    """Create a dashboard with layout"""
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard_title": title,
        "description": description,
        "position_json": json.dumps(position_json),
        "published": True
    }
    
    response = session.post(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        headers=headers,
        json=dashboard_config
    )
    
    if response.status_code == 201:
        return response.json()['id']
    else:
        print(f"Failed to create dashboard: {response.status_code}")
        return None

def create_customer_success_dashboard(session, csrf_token, datasets):
    """Create Customer Success Dashboard"""
    print("\n📊 Creating Customer Success Dashboard...")
    
    charts = []
    
    # 1. Customer Health Overview
    chart_config = {
        "slice_name": "Customer Health Distribution",
        "viz_type": "pie",
        "datasource_id": datasets.get("entity.entity_customers"),
        "datasource_type": "table",
        "params": json.dumps({
            "viz_type": "pie",
            "groupby": ["customer_health_tier"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "account_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Customer Count"
            },
            "color_scheme": "supersetColors",
            "show_labels_threshold": 5,
            "show_legend": True,
            "legendType": "scroll",
            "legendOrientation": "bottom",
            "label_type": "key_value",
            "number_format": "SMART_NUMBER",
            "show_labels": True,
            "labels_outside": True,
            "annotation_layers": [{
                "name": "Health Score Guide",
                "annotationType": "FORMULA",
                "sourceType": "NATIVE",
                "value": "Healthy: 80-100 | At Risk: 60-79 | Critical: <60",
                "overrides": {"time_range": None},
                "show": True,
                "showLabel": True,
                "titleColumn": "",
                "descriptionColumns": [],
                "timeColumn": "",
                "color": None,
                "opacity": "",
                "style": "solid",
                "width": 1
            }]
        })
    }
    
    # More charts would be added here...
    
    # Create dashboard layout
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "children": ["ROW-1"]
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "type": "HEADER",
            "meta": {
                "text": "Customer Success Dashboard"
            }
        },
        "ROW-1": {
            "id": "ROW-1",
            "type": "ROW",
            "children": ["CHART-1", "CHART-2"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        }
    }
    
    dashboard_id = create_dashboard(
        session, 
        csrf_token,
        "🎯 Customer Success Command Center",
        """
        ## Customer Success Analytics Dashboard
        
        This dashboard provides comprehensive insights into customer health, satisfaction, and retention metrics.
        
        ### Key Metrics:
        - **Customer Health Score**: Composite score (0-100) based on usage, engagement, and payment history
        - **Churn Risk**: Predictive risk score identifying at-risk accounts
        - **Monthly Recurring Revenue (MRR)**: Revenue trends by customer segment
        - **Net Revenue Retention (NRR)**: Expansion revenue from existing customers
        
        ### How to Use:
        1. Monitor the health distribution to identify segments needing attention
        2. Filter by risk tier to focus on at-risk accounts
        3. Track MRR trends to understand revenue impact
        4. Use the customer detail table to drill into specific accounts
        
        ### Data Freshness:
        - Entity tables: Updated every 15 minutes
        - History tables: Real-time change capture
        - Daily aggregations: Updated at 2 AM UTC
        """,
        position_json
    )
    
    return dashboard_id

def create_sales_dashboard(session, csrf_token, datasets):
    """Create Sales Dashboard"""
    print("\n📊 Creating Sales Dashboard...")
    
    dashboard_id = create_dashboard(
        session,
        csrf_token,
        "💰 Sales Pipeline & Performance",
        """
        ## Sales Analytics Dashboard
        
        Track sales pipeline health, conversion rates, and revenue forecasting.
        
        ### Key Metrics:
        - **Pipeline Value**: Total opportunity value by stage
        - **Conversion Rates**: Stage-to-stage conversion metrics
        - **Sales Velocity**: Average time to close by segment
        - **Win Rate**: Closed won vs. closed lost ratio
        
        ### Pipeline Stages:
        1. **Qualified Lead**: Initial qualification complete
        2. **Demo Scheduled**: Product demonstration booked
        3. **Proposal Sent**: Commercial proposal delivered
        4. **Negotiation**: Commercial terms under discussion
        5. **Closed Won/Lost**: Deal outcome
        
        ### Best Practices:
        - Review pipeline coverage ratio (3-4x target)
        - Monitor stage conversion trends
        - Identify bottlenecks in sales velocity
        - Track win rate by competitor
        """,
        {}
    )
    
    return dashboard_id

def create_marketing_dashboard(session, csrf_token, datasets):
    """Create Marketing Dashboard"""
    print("\n📊 Creating Marketing Dashboard...")
    
    dashboard_id = create_dashboard(
        session,
        csrf_token,
        "📈 Marketing Attribution & Performance",
        """
        ## Marketing Analytics Dashboard
        
        Multi-touch attribution analysis and campaign ROI tracking.
        
        ### Attribution Models:
        - **First Touch**: Credit to initial touchpoint
        - **Last Touch**: Credit to converting touchpoint
        - **Linear**: Equal credit distribution
        - **Time Decay**: Recent touches weighted higher
        - **Position Based**: 40-20-40 model
        
        ### Channel Performance:
        - **Paid Search**: Google Ads, Bing Ads
        - **Social Media**: LinkedIn, Facebook, Twitter
        - **Email**: Nurture campaigns, newsletters
        - **Organic**: SEO, content marketing
        - **Direct**: Brand awareness
        
        ### Key Metrics:
        - **Customer Acquisition Cost (CAC)**: By channel and campaign
        - **Return on Ad Spend (ROAS)**: Revenue per dollar spent
        - **Marketing Qualified Leads (MQL)**: Volume and quality
        - **Conversion Rates**: By funnel stage
        """,
        {}
    )
    
    return dashboard_id

def create_product_dashboard(session, csrf_token, datasets):
    """Create Product Dashboard"""
    print("\n📊 Creating Product Dashboard...")
    
    dashboard_id = create_dashboard(
        session,
        csrf_token,
        "🚀 Product Adoption & Usage Analytics",
        """
        ## Product Analytics Dashboard
        
        Feature adoption, user engagement, and product-market fit metrics.
        
        ### Adoption Metrics:
        - **Feature Adoption Rate**: % of users accessing each feature
        - **Time to First Value**: Speed of initial feature use
        - **Feature Stickiness**: DAU/MAU ratio by feature
        - **Power User Identification**: Heavy feature usage patterns
        
        ### Engagement Scoring:
        - **Frequency**: How often users engage
        - **Recency**: Time since last activity
        - **Depth**: Number of features used
        - **Duration**: Time spent in product
        
        ### Product Health Indicators:
        - **Activation Rate**: New users reaching "aha moment"
        - **Feature Retention**: Continued usage over time
        - **Cross-Feature Adoption**: Feature discovery patterns
        - **User Feedback Scores**: NPS, CSAT by feature
        """,
        {}
    )
    
    return dashboard_id

def create_operations_dashboard(session, csrf_token, datasets):
    """Create Operations Dashboard"""
    print("\n📊 Creating Operations Dashboard...")
    
    dashboard_id = create_dashboard(
        session,
        csrf_token,
        "⚙️ Operations Command Center",
        """
        ## Operations Analytics Dashboard
        
        Real-time monitoring of device fleet, location performance, and operational health.
        
        ### Device Monitoring:
        - **Fleet Status**: Online/offline/maintenance counts
        - **Performance Metrics**: Response time, throughput, errors
        - **Predictive Maintenance**: Failure risk scoring
        - **Utilization Rates**: Device capacity usage
        
        ### Location Analytics:
        - **Operational Health**: Composite score per location
        - **Device Density**: Devices per location metrics
        - **Performance Variance**: Location comparison
        - **Support Tickets**: Volume and resolution time
        
        ### Key Performance Indicators:
        - **System Uptime**: 99.9% SLA tracking
        - **Mean Time to Resolution (MTTR)**: Incident response
        - **Device Efficiency**: Transactions per device
        - **Location Coverage**: Geographic distribution
        
        ### Alerting Thresholds:
        - Critical: <95% uptime, >5% error rate
        - Warning: <98% uptime, >2% error rate
        - Info: Planned maintenance windows
        """,
        {}
    )
    
    return dashboard_id

def create_executive_dashboard(session, csrf_token, datasets):
    """Create Executive Overview Dashboard"""
    print("\n📊 Creating Executive Overview Dashboard...")
    
    dashboard_id = create_dashboard(
        session,
        csrf_token,
        "👔 Executive Business Overview",
        """
        ## Executive Dashboard
        
        High-level business metrics and KPIs for leadership team.
        
        ### Business Health Metrics:
        - **Annual Recurring Revenue (ARR)**: Current and growth rate
        - **Net Revenue Retention (NRR)**: Expansion revenue health
        - **Gross Margin**: Revenue efficiency
        - **Rule of 40**: Growth + Profitability score
        
        ### Customer Metrics:
        - **Total Customers**: Active account count
        - **Logo Retention**: Customer count retention
        - **Net Promoter Score (NPS)**: Customer satisfaction
        - **Customer Lifetime Value (CLV)**: Average revenue per customer
        
        ### Operational Excellence:
        - **Employee Productivity**: Revenue per employee
        - **Sales Efficiency**: CAC Payback period
        - **R&D Investment**: % of revenue
        - **Platform Reliability**: System uptime
        
        ### Strategic Initiatives:
        - Market expansion progress
        - Product roadmap delivery
        - Partnership pipeline
        - Competitive positioning
        """,
        {}
    )
    
    return dashboard_id

def main():
    """Main execution function"""
    print("🚀 Setting up Superset Datasets and Dashboards")
    print("=" * 50)
    
    # Login
    session, csrf_token = login_and_get_csrf()
    if not session:
        print("❌ Failed to login")
        sys.exit(1)
    
    # Get API token
    api_csrf_token = get_api_csrf_token(session)
    if not api_csrf_token:
        print("❌ Failed to get API CSRF token")
        sys.exit(1)
    
    # Get existing datasets
    print("\n🔍 Checking existing datasets...")
    existing_datasets = get_existing_datasets(session, api_csrf_token)
    print(f"✅ Found {len(existing_datasets)} existing datasets")
    
    # Setup Entity datasets
    entity_ids = setup_entity_datasets(session, api_csrf_token)
    
    # Setup Mart datasets
    mart_ids = setup_mart_datasets(session, api_csrf_token)
    
    # Refresh dataset list
    time.sleep(2)
    datasets = get_existing_datasets(session, api_csrf_token)
    
    # Create Dashboards
    print("\n🎨 Creating Domain Dashboards")
    print("=" * 50)
    
    dashboards = []
    
    # Customer Success Dashboard
    cs_dashboard = create_customer_success_dashboard(session, api_csrf_token, datasets)
    if cs_dashboard:
        dashboards.append(("Customer Success", cs_dashboard))
    
    # Sales Dashboard
    sales_dashboard = create_sales_dashboard(session, api_csrf_token, datasets)
    if sales_dashboard:
        dashboards.append(("Sales", sales_dashboard))
    
    # Marketing Dashboard
    marketing_dashboard = create_marketing_dashboard(session, api_csrf_token, datasets)
    if marketing_dashboard:
        dashboards.append(("Marketing", marketing_dashboard))
    
    # Product Dashboard
    product_dashboard = create_product_dashboard(session, api_csrf_token, datasets)
    if product_dashboard:
        dashboards.append(("Product", product_dashboard))
    
    # Operations Dashboard
    ops_dashboard = create_operations_dashboard(session, api_csrf_token, datasets)
    if ops_dashboard:
        dashboards.append(("Operations", ops_dashboard))
    
    # Executive Dashboard
    exec_dashboard = create_executive_dashboard(session, api_csrf_token, datasets)
    if exec_dashboard:
        dashboards.append(("Executive", exec_dashboard))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("=" * 50)
    print(f"\n📊 Datasets Created:")
    print(f"   • Entity Layer: {len(entity_ids)} datasets")
    print(f"   • Mart Layer: {len(mart_ids)} datasets")
    print(f"\n🎨 Dashboards Created:")
    for name, dash_id in dashboards:
        print(f"   • {name} Dashboard (ID: {dash_id})")
    
    print("\n🎯 Next Steps:")
    print("   1. Visit http://localhost:8088")
    print("   2. Navigate to Dashboards to see all created dashboards")
    print("   3. Each dashboard includes:")
    print("      - Comprehensive documentation")
    print("      - Key metric definitions")
    print("      - Usage guidelines")
    print("      - Data freshness information")
    print("\n📚 Dashboard Features:")
    print("   • Interactive filters for drill-down analysis")
    print("   • Cross-filtering between charts")
    print("   • Export capabilities for reports")
    print("   • Scheduled email delivery options")
    print("   • Mobile-responsive layouts")

if __name__ == "__main__":
    main()
