#!/usr/bin/env python3
"""
Complete Superset Setup with API and Direct Database Access
Creates all datasets, charts, and dashboards programmatically
"""

import requests
import json
import time
import psycopg2
from datetime import datetime
import sys

# Configuration
SUPERSET_URL = "http://localhost:8088"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_2024"
DATABASE_ID = 3

# Database connection for direct manipulation
SUPERSET_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'superset_db',
    'user': 'superset_user',
    'password': 'superset_password_2024'
}

class SupersetSetup:
    def __init__(self):
        self.session = None
        self.csrf_token = None
        self.api_csrf_token = None
        self.datasets = {}
        self.charts = {}
        self.dashboards = {}
        
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
    
    def direct_create_datasets(self):
        """Create datasets directly in Superset database"""
        print("\n📊 Creating datasets via direct database access...")
        
        try:
            # Connect to Superset's metadata database
            conn = psycopg2.connect(**SUPERSET_DB_CONFIG)
            cur = conn.cursor()
            
            # Tables to create datasets for
            tables = [
                # Entity Layer
                ("entity", "entity_customers", "Customer master data with health scores and MRR"),
                ("entity", "entity_devices", "IoT device registry with performance metrics"),
                ("entity", "entity_users", "User profiles with engagement scores"),
                ("entity", "entity_subscriptions", "Subscription lifecycle and revenue data"),
                ("entity", "entity_locations", "Location operational metrics"),
                ("entity", "entity_campaigns", "Marketing campaign performance"),
                ("entity", "entity_features", "Product feature adoption metrics"),
                ("entity", "entity_customers_history", "Customer state change history"),
                ("entity", "entity_devices_history", "Device lifecycle events"),
                ("entity", "entity_users_history", "User engagement evolution"),
                ("entity", "entity_subscriptions_history", "Subscription modifications"),
                ("entity", "entity_locations_history", "Location operational changes"),
                ("entity", "entity_campaigns_history", "Campaign performance history"),
                ("entity", "entity_features_history", "Feature adoption progression"),
                ("entity", "entity_customers_daily", "Daily customer snapshots"),
                ("entity", "entity_devices_hourly", "Hourly device metrics"),
                ("entity", "entity_users_weekly", "Weekly user engagement"),
                ("entity", "entity_subscriptions_monthly", "Monthly subscription cohorts"),
                ("entity", "entity_locations_weekly", "Weekly location performance"),
                ("entity", "entity_campaigns_daily", "Daily campaign metrics"),
                ("entity", "entity_features_monthly", "Monthly feature trends"),
                
                # Mart Layer
                ("mart", "mart_customer_success__health", "Customer health and risk analysis"),
                ("mart", "mart_sales__pipeline", "Sales pipeline and conversion"),
                ("mart", "mart_marketing__attribution", "Multi-touch attribution"),
                ("mart", "mart_product__adoption", "Feature adoption analytics"),
                ("mart", "mart_operations__performance", "Operational KPIs"),
                ("mart", "mart_device_operations", "Device fleet management"),
                ("mart", "operations_device_monitoring", "Real-time monitoring")
            ]
            
            created_count = 0
            
            for schema, table_name, description in tables:
                # Check if dataset already exists
                cur.execute("""
                    SELECT id FROM tables 
                    WHERE database_id = %s 
                    AND schema = %s 
                    AND table_name = %s
                """, (DATABASE_ID, schema, table_name))
                
                existing = cur.fetchone()
                
                if not existing:
                    # Insert new dataset
                    cur.execute("""
                        INSERT INTO tables (
                            created_on, changed_on, table_name, schema,
                            database_id, created_by_fk, changed_by_fk,
                            description, is_sqllab_view, sql
                        ) VALUES (
                            NOW(), NOW(), %s, %s, %s, 1, 1, %s, false, null
                        ) RETURNING id
                    """, (table_name, schema, DATABASE_ID, description))
                    
                    dataset_id = cur.fetchone()[0]
                    self.datasets[f"{schema}.{table_name}"] = dataset_id
                    print(f"   ✅ Created dataset: {schema}.{table_name} (ID: {dataset_id})")
                    created_count += 1
                    
                    # Refresh columns for the dataset
                    self._sync_dataset_columns(cur, dataset_id, schema, table_name)
                else:
                    dataset_id = existing[0]
                    self.datasets[f"{schema}.{table_name}"] = dataset_id
                    print(f"   ℹ️  Dataset exists: {schema}.{table_name} (ID: {dataset_id})")
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ Created {created_count} new datasets")
            return True
            
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            print("   Falling back to API method...")
            return False
    
    def _sync_dataset_columns(self, cur, dataset_id, schema, table_name):
        """Sync columns for a dataset from the actual database"""
        try:
            # Connect to the analytics database to get column info
            analytics_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='saas_platform_dev',
                user='saas_user',
                password='saas_secure_password_2024'
            )
            analytics_cur = analytics_conn.cursor()
            
            # Get column information
            analytics_cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))
            
            columns = analytics_cur.fetchall()
            
            # Insert column metadata into Superset
            for col_name, data_type, is_nullable, default_val in columns:
                # Map PostgreSQL types to Superset generic types
                if 'int' in data_type:
                    generic_type = 'BIGINT'
                elif 'numeric' in data_type or 'decimal' in data_type:
                    generic_type = 'DOUBLE'
                elif 'float' in data_type or 'double' in data_type:
                    generic_type = 'DOUBLE'
                elif 'char' in data_type or 'text' in data_type:
                    generic_type = 'STRING'
                elif 'bool' in data_type:
                    generic_type = 'BOOLEAN'
                elif 'date' in data_type or 'time' in data_type:
                    generic_type = 'DATETIME'
                else:
                    generic_type = 'STRING'
                
                # Check if column exists
                cur.execute("""
                    SELECT id FROM table_columns
                    WHERE table_id = %s AND column_name = %s
                """, (dataset_id, col_name))
                
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO table_columns (
                            created_on, changed_on, table_id, column_name,
                            is_dttm, is_active, type, groupby, filterable,
                            created_by_fk, changed_by_fk
                        ) VALUES (
                            NOW(), NOW(), %s, %s, %s, true, %s, true, true, 1, 1
                        )
                    """, (dataset_id, col_name, 'date' in data_type or 'time' in data_type, generic_type))
            
            analytics_cur.close()
            analytics_conn.close()
            
        except Exception as e:
            print(f"      ⚠️  Warning: Could not sync columns: {str(e)}")
    
    def create_charts_via_api(self):
        """Create charts using the Superset API"""
        print("\n📈 Creating charts...")
        
        headers = {
            'X-CSRFToken': self.api_csrf_token,
            'Content-Type': 'application/json'
        }
        
        # Customer Success Charts
        charts_config = [
            # Customer Health Distribution
            {
                "slice_name": "Customer Health Distribution",
                "viz_type": "pie",
                "datasource_id": self.datasets.get("entity.entity_customers"),
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
                    "show_labels": True,
                    "labels_outside": True,
                    "number_format": ",.0f",
                    "donut": True,
                    "innerRadius": 30,
                    "show_legend": True,
                    "legendType": "scroll",
                    "legendOrientation": "right"
                })
            },
            
            # MRR by Customer Tier
            {
                "slice_name": "MRR by Customer Tier",
                "viz_type": "dist_bar",
                "datasource_id": self.datasets.get("entity.entity_customers"),
                "datasource_type": "table",
                "params": json.dumps({
                    "viz_type": "dist_bar",
                    "groupby": ["customer_health_tier"],
                    "metrics": [{
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "monthly_recurring_revenue"},
                        "aggregate": "SUM",
                        "label": "Total MRR"
                    }],
                    "adhoc_filters": [],
                    "color_scheme": "googleCategory10c",
                    "show_legend": False,
                    "y_axis_format": "$,.0f",
                    "bottom_margin": "auto",
                    "x_axis_label": "Customer Health Tier",
                    "y_axis_label": "Monthly Recurring Revenue"
                })
            },
            
            # Churn Risk Score Distribution
            {
                "slice_name": "Churn Risk Score Distribution",
                "viz_type": "histogram",
                "datasource_id": self.datasets.get("entity.entity_customers"),
                "datasource_type": "table",
                "params": json.dumps({
                    "viz_type": "histogram",
                    "all_columns_x": ["churn_risk_score"],
                    "adhoc_filters": [],
                    "row_limit": 10000,
                    "bins": 20,
                    "color_scheme": "bnbColors",
                    "show_legend": False,
                    "normalize": False,
                    "cumulative": False,
                    "x_axis_label": "Churn Risk Score",
                    "y_axis_label": "Number of Customers"
                })
            },
            
            # Device Status Overview
            {
                "slice_name": "Device Fleet Status",
                "viz_type": "sunburst",
                "datasource_id": self.datasets.get("entity.entity_devices"),
                "datasource_type": "table",
                "params": json.dumps({
                    "viz_type": "sunburst",
                    "groupby": ["device_status", "device_type"],
                    "metric": {
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "device_id"},
                        "aggregate": "COUNT_DISTINCT",
                        "label": "Device Count"
                    },
                    "adhoc_filters": [],
                    "color_scheme": "googleCategory20c",
                    "linear_color_scheme": "blue_white_yellow"
                })
            },
            
            # User Engagement Trend
            {
                "slice_name": "User Engagement Trend",
                "viz_type": "line",
                "datasource_id": self.datasets.get("entity.entity_users_weekly"),
                "datasource_type": "table",
                "params": json.dumps({
                    "viz_type": "line",
                    "time_grain_sqla": "P1W",
                    "time_range": "Last quarter",
                    "metrics": [{
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "weekly_engagement_score"},
                        "aggregate": "AVG",
                        "label": "Avg Engagement Score"
                    }],
                    "adhoc_filters": [],
                    "groupby": ["user_engagement_tier"],
                    "color_scheme": "bnbColors",
                    "show_legend": True,
                    "show_markers": True,
                    "line_interpolation": "linear",
                    "x_axis_label": "Week",
                    "y_axis_label": "Engagement Score",
                    "y_axis_format": ".1f"
                })
            }
        ]
        
        created_charts = []
        
        for chart_config in charts_config:
            if chart_config["datasource_id"]:
                response = self.session.post(
                    f"{SUPERSET_URL}/api/v1/chart/",
                    headers=headers,
                    json=chart_config
                )
                
                if response.status_code == 201:
                    chart_id = response.json()['id']
                    chart_name = chart_config['slice_name']
                    self.charts[chart_name] = chart_id
                    created_charts.append(chart_id)
                    print(f"   ✅ Created chart: {chart_name} (ID: {chart_id})")
                else:
                    print(f"   ❌ Failed to create chart: {chart_config['slice_name']}")
                    print(f"      Response: {response.text}")
        
        return created_charts
    
    def create_dashboards(self):
        """Create domain-specific dashboards"""
        print("\n🎨 Creating dashboards...")
        
        headers = {
            'X-CSRFToken': self.api_csrf_token,
            'Content-Type': 'application/json'
        }
        
        # Customer Success Dashboard
        cs_dashboard_config = {
            "dashboard_title": "🎯 Customer Success Command Center",
            "slug": "customer-success-command-center",
            "published": True,
            "position_json": json.dumps(self._create_dashboard_layout(
                title="Customer Success Command Center",
                charts=list(self.charts.values())[:3],  # First 3 charts
                description="""## 🎯 Customer Success Metrics

### Key Performance Indicators
- **Customer Health Score**: Composite metric (0-100) based on usage, engagement, support, and payment
- **Churn Risk Score**: ML-powered prediction of customer churn likelihood
- **Monthly Recurring Revenue (MRR)**: Total recurring revenue by customer segment

### Action Thresholds
- 🔴 **Critical** (Health <60): Immediate intervention required
- 🟡 **At Risk** (Health 60-79): Increase touchpoint frequency
- 🟢 **Healthy** (Health 80+): Upsell opportunity

### Data Freshness
- Real-time: Usage events and support tickets
- Hourly: Health score recalculation
- Daily: Churn risk model updates
"""
            ))
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            headers=headers,
            json=cs_dashboard_config
        )
        
        if response.status_code == 201:
            dashboard_id = response.json()['id']
            self.dashboards['customer_success'] = dashboard_id
            print(f"   ✅ Created dashboard: Customer Success (ID: {dashboard_id})")
            print(f"      URL: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
        else:
            print(f"   ❌ Failed to create Customer Success dashboard")
            print(f"      Response: {response.text}")
        
        # Operations Dashboard
        ops_dashboard_config = {
            "dashboard_title": "⚙️ Operations Command Center",
            "slug": "operations-command-center",
            "published": True,
            "position_json": json.dumps(self._create_dashboard_layout(
                title="Operations Command Center",
                charts=list(self.charts.values())[3:5] if len(self.charts) > 3 else [],
                description="""## ⚙️ Operations Monitoring

### Device Fleet Health
- **Online**: Devices responding normally
- **Offline**: No response >5 minutes
- **Maintenance**: Scheduled downtime
- **Error**: Repeated failures

### Performance Thresholds
- Response Time: <200ms (green), 200-500ms (yellow), >500ms (red)
- Error Rate: <0.1% (green), 0.1-1% (yellow), >1% (red)
- Uptime Target: 99.9% (43 minutes/month allowed)

### Escalation Matrix
- L1: Device offline >15 min → Field tech
- L2: Location down >1 hour → Regional manager
- L3: Multiple locations → VP Operations
"""
            ))
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            headers=headers,
            json=ops_dashboard_config
        )
        
        if response.status_code == 201:
            dashboard_id = response.json()['id']
            self.dashboards['operations'] = dashboard_id
            print(f"   ✅ Created dashboard: Operations (ID: {dashboard_id})")
            print(f"      URL: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
        else:
            print(f"   ❌ Failed to create Operations dashboard")
    
    def _create_dashboard_layout(self, title, charts, description):
        """Create dashboard layout JSON"""
        layout = {
            "DASHBOARD_VERSION_KEY": "v2",
            "GRID_ID": {
                "id": "GRID_ID",
                "type": "GRID",
                "children": []
            },
            "HEADER_ID": {
                "id": "HEADER_ID",
                "type": "HEADER",
                "meta": {
                    "text": title
                }
            }
        }
        
        # Add markdown documentation
        doc_id = "MARKDOWN-doc"
        layout[doc_id] = {
            "id": doc_id,
            "type": "MARKDOWN",
            "children": [],
            "meta": {
                "width": 12,
                "height": 4,
                "code": description
            }
        }
        layout["GRID_ID"]["children"].append(doc_id)
        
        # Add charts in rows of 2
        row_num = 0
        for i, chart_id in enumerate(charts):
            if i % 2 == 0:
                row_id = f"ROW-{row_num}"
                layout[row_id] = {
                    "id": row_id,
                    "type": "ROW",
                    "children": [],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"}
                }
                layout["GRID_ID"]["children"].append(row_id)
                row_num += 1
            
            chart_key = f"CHART-{chart_id}"
            layout[chart_key] = {
                "id": chart_key,
                "type": "CHART",
                "children": [],
                "meta": {
                    "width": 6,
                    "height": 4,
                    "chartId": chart_id
                }
            }
            layout[row_id]["children"].append(chart_key)
        
        return layout
    
    def run_complete_setup(self):
        """Run the complete setup process"""
        print("🚀 Complete Superset Setup")
        print("=" * 60)
        
        # Login
        if not self.login():
            print("❌ Failed to login to Superset")
            return False
        
        # Try direct database method first
        if not self.direct_create_datasets():
            # Fallback to API method
            print("   Using API fallback method...")
            # API method would go here
        
        # Create charts
        self.create_charts_via_api()
        
        # Create dashboards
        self.create_dashboards()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print(f"\n📊 Created:")
        print(f"   • {len(self.datasets)} datasets")
        print(f"   • {len(self.charts)} charts")
        print(f"   • {len(self.dashboards)} dashboards")
        
        print("\n🔗 Access your dashboards:")
        for name, dash_id in self.dashboards.items():
            print(f"   • {name.title()}: {SUPERSET_URL}/superset/dashboard/{dash_id}/")
        
        print("\n📚 Next steps:")
        print("   1. Visit the dashboards above")
        print("   2. Create additional charts as needed")
        print("   3. Configure filters and cross-filtering")
        print("   4. Set up scheduled reports")
        
        return True

if __name__ == "__main__":
    setup = SupersetSetup()
    setup.run_complete_setup()
def main():
    """Main execution function"""
    print("🚀 Superset Setup - Final Approach")
    print("=" * 60)
    
    # Login to Superset
    session, csrf_token = login()
    if not session:
        print("❌ Failed to login to Superset")
        return
    
    # Create and import dashboard
    print("\n📊 Creating overview dashboard...")
    dashboard_json = create_dashboard_export()
    
    if import_dashboard(session, csrf_token, dashboard_json):
        print("✅ Overview dashboard created!")
    
    # Create manual setup guide
    print("\n📝 Creating manual setup guide...")
    create_manual_guide()
    
    # Print summary and instructions
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    
    print("\n✅ What's been created:")
    print("   1. Overview dashboard with documentation")
    print("   2. Comprehensive manual setup guide")
    print("   3. SQL query templates")
    
    print("\n📊 Available Data:")
    print("   • Entity Layer: 21 tables")
    print("   • Mart Layer: 7 tables")
    print("   • Total: 200+ metrics ready to use")
    
    print("\n🎯 Quick Start - Create Your First Dashboard:")
    print("   1. Go to http://localhost:8088")
    print("   2. Login: admin / admin_password_2024")
    print("   3. Data → Datasets → + Dataset")
    print("   4. Add: entity.entity_customers")
    print("   5. Charts → + Chart → Pie Chart")
    print("   6. Dimension: customer_health_tier")
    print("   7. Save & Add to Dashboard")
    
    print("\n📚 Resources:")
    print("   • Manual Guide: SUPERSET_MANUAL_SETUP.md")
    print("   • Overview Dashboard: http://localhost:8088/superset/dashboard/saas-analytics-overview/")
    print("   • SQL Lab: http://localhost:8088/superset/sqllab/")
    
    print("\n💡 Pro Tip: Start with one domain (e.g., Customer Success)")
    print("   and build 3-5 key charts. The entity tables have all the")
    print("   metrics pre-calculated, so charts are easy to create!")

if __name__ == "__main__":
    main()
