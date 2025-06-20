#!/usr/bin/env python3
"""
Create Sales Dashboard in Apache Superset
This script creates a comprehensive sales dashboard with charts and filters
"""

import json
import requests
from datetime import datetime
import time

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin_password_2024"

class SupersetDashboardCreator:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        self.access_token = None
        
    def login(self):
        """Login to Superset and get access token"""
        # Get CSRF token
        login_page = self.session.get(f"{SUPERSET_URL}/login/")
        
        # Login
        login_data = {
            "username": USERNAME,
            "password": PASSWORD,
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/login/",
            data=login_data,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            print("✓ Successfully logged in to Superset")
            return True
        else:
            print("✗ Failed to login to Superset")
            return False
    
    def get_database_id(self):
        """Get the PostgreSQL database ID"""
        response = self.session.get(f"{SUPERSET_URL}/api/v1/database/")
        if response.status_code == 200:
            databases = response.json()
            for db in databases.get('result', []):
                if 'postgres' in db['database_name'].lower():
                    return db['id']
        return None
    
    def create_dataset(self, table_name, schema_name='public'):
        """Create a dataset (table) in Superset"""
        db_id = self.get_database_id()
        if not db_id:
            print("✗ Could not find database")
            return None
            
        dataset_data = {
            "database": db_id,
            "schema": schema_name,
            "table_name": table_name,
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            json=dataset_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            dataset_id = response.json()['id']
            print(f"✓ Created dataset: {schema_name}.{table_name} (ID: {dataset_id})")
            return dataset_id
        else:
            print(f"✗ Failed to create dataset: {table_name}")
            return None
    
    def create_chart(self, chart_config):
        """Create a chart in Superset"""
        chart_data = {
            "slice_name": chart_config["slice_name"],
            "viz_type": chart_config["viz_type"],
            "datasource_type": "table",
            "datasource_id": chart_config["dataset_id"],
            "params": json.dumps(chart_config["params"]),
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/chart/",
            json=chart_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            chart_id = response.json()['id']
            print(f"✓ Created chart: {chart_config['slice_name']} (ID: {chart_id})")
            return chart_id
        else:
            print(f"✗ Failed to create chart: {chart_config['slice_name']}")
            return None
    
    def create_dashboard(self):
        """Create the complete sales dashboard"""
        print("\n=== Creating Sales Performance Dashboard ===\n")
        
        # Create datasets
        datasets = {
            "metrics_sales": self.create_dataset("metrics_sales", "public"),
            "mart_sales_pipeline": self.create_dataset("mart_sales__pipeline", "mart"),
            "entity_customers_daily": self.create_dataset("entity_customers_daily", "entity"),
            "marketing_mqls": self.create_dataset("marketing_qualified_leads", "marketing"),
        }
        
        # Define charts
        charts = [
            {
                "slice_name": "Total Revenue (YTD)",
                "viz_type": "big_number_total",
                "dataset_id": datasets["metrics_sales"],
                "params": {
                    "metric": "total_revenue",
                    "subheader": "Year to Date",
                    "y_axis_format": "$,.0f",
                }
            },
            {
                "slice_name": "Pipeline Value",
                "viz_type": "big_number_total",
                "dataset_id": datasets["metrics_sales"],
                "params": {
                    "metric": "pipeline_value",
                    "subheader": "Open Opportunities",
                    "y_axis_format": "$,.0f",
                }
            },
            {
                "slice_name": "Win Rate",
                "viz_type": "big_number",
                "dataset_id": datasets["metrics_sales"],
                "params": {
                    "metric": "win_rate",
                    "subheader": "Last 90 Days",
                    "y_axis_format": ".1%",
                    "show_trend_line": True,
                    "start_y_axis_at_zero": True,
                }
            },
            {
                "slice_name": "Average Deal Size",
                "viz_type": "big_number_total",
                "dataset_id": datasets["metrics_sales"],
                "params": {
                    "metric": "avg_won_deal_size",
                    "subheader": "Closed Won Deals",
                    "y_axis_format": "$,.0f",
                }
            },
            {
                "slice_name": "Sales Pipeline Funnel",
                "viz_type": "funnel",
                "dataset_id": datasets["mart_sales_pipeline"],
                "params": {
                    "groupby": ["stage_name"],
                    "metric": "sum__amount",
                    "show_legend": False,
                }
            },
            {
                "slice_name": "Revenue Trend - Last 30 Days",
                "viz_type": "line",
                "dataset_id": datasets["entity_customers_daily"],
                "params": {
                    "metrics": ["sum__daily_new_mrr", "sum__daily_expansion_revenue"],
                    "groupby": ["date"],
                    "time_range": "Last 30 days",
                    "timeseries_limit_metric": "sum__daily_new_mrr",
                    "x_axis_format": "%m/%d",
                    "y_axis_format": "$,.0f",
                    "rich_tooltip": True,
                    "show_legend": True,
                }
            },
            {
                "slice_name": "Top 10 Open Deals",
                "viz_type": "table",
                "dataset_id": datasets["mart_sales_pipeline"],
                "params": {
                    "columns": ["deal_name", "company_name", "owner_name", "stage_name", "amount", "close_date"],
                    "metrics": [],
                    "row_limit": 10,
                    "filters": [
                        {
                            "col": "stage_name",
                            "op": "NOT IN",
                            "val": ["Closed Won", "Closed Lost"]
                        }
                    ],
                    "order_by_cols": ["amount__desc"],
                }
            },
            {
                "slice_name": "Sales Rep Leaderboard",
                "viz_type": "bar",
                "dataset_id": datasets["mart_sales_pipeline"],
                "params": {
                    "metrics": ["sum__amount"],
                    "groupby": ["owner_name"],
                    "filters": [
                        {
                            "col": "stage_name",
                            "op": "==",
                            "val": "Closed Won"
                        }
                    ],
                    "row_limit": 10,
                    "y_axis_format": "$,.0f",
                    "show_legend": False,
                }
            },
            {
                "slice_name": "Lead Source Distribution",
                "viz_type": "pie",
                "dataset_id": datasets["marketing_mqls"],
                "params": {
                    "metric": "count",
                    "groupby": ["lead_source"],
                    "donut": True,
                    "show_labels": True,
                    "label_type": "key_percent",
                    "time_range": "Last 30 days",
                }
            }
        ]
        
        # Create charts
        chart_ids = []
        for chart in charts:
            chart_id = self.create_chart(chart)
            if chart_id:
                chart_ids.append(chart_id)
            time.sleep(1)  # Rate limiting
        
        # Create dashboard
        dashboard_data = {
            "dashboard_title": "Sales Performance Dashboard",
            "slug": "sales-performance",
            "owners": [1],  # Admin user
            "position_json": json.dumps({
                "DASHBOARD_VERSION_KEY": "v2",
                "GRID_ID": {
                    "children": ["ROW-1", "ROW-2", "ROW-3"],
                    "id": "GRID_ID",
                    "type": "GRID"
                },
                "HEADER_ID": {
                    "id": "HEADER_ID",
                    "meta": {"text": "Sales Performance Dashboard"},
                    "type": "HEADER"
                },
                "ROW-1": {
                    "children": chart_ids[:4],  # KPIs
                    "id": "ROW-1",
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                    "type": "ROW"
                },
                "ROW-2": {
                    "children": chart_ids[4:6],  # Funnel and Trend
                    "id": "ROW-2",
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                    "type": "ROW"
                },
                "ROW-3": {
                    "children": chart_ids[6:],  # Tables
                    "id": "ROW-3",
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                    "type": "ROW"
                }
            }),
            "json_metadata": json.dumps({
                "refresh_frequency": 300,
                "color_scheme": "supersetColors",
                "label_colors": {
                    "Won": "#00CC88",
                    "Lost": "#FF5A5F",
                    "Open": "#FFC442"
                }
            })
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            json=dashboard_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            dashboard_id = response.json()['id']
            print(f"\n✓ Successfully created Sales Dashboard!")
            print(f"  Dashboard ID: {dashboard_id}")
            print(f"  URL: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
            return dashboard_id
        else:
            print(f"\n✗ Failed to create dashboard")
            return None

def main():
    creator = SupersetDashboardCreator()
    
    # Login to Superset
    if not creator.login():
        print("Failed to login to Superset. Please check credentials.")
        return
    
    # Create the dashboard
    dashboard_id = creator.create_dashboard()
    
    if dashboard_id:
        print("\n🎉 Sales Dashboard created successfully!")
        print(f"Access it at: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
    else:
        print("\n❌ Failed to create dashboard")

if __name__ == "__main__":
    main()