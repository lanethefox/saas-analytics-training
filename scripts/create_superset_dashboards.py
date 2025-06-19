#!/usr/bin/env python3
"""
Create comprehensive Superset dashboards for all domain marts
"""

import requests
import json
import time
from typing import Dict, List, Any

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# Database configuration for Docker PostgreSQL
DATABASE_NAME = "saas_platform_dev"
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_USER = "saas_user"
DATABASE_PASSWORD = "saas_secure_password_2024"

class SupersetDashboardCreator:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.csrf_token = None
        self.database_id = None
        
    def login(self):
        """Login to Superset and get access token"""
        # Get CSRF token
        login_page = self.session.get(f"{SUPERSET_URL}/login/")
        
        # Login
        login_data = {
            "username": USERNAME,
            "password": PASSWORD,
            "provider": "db",
            "refresh": True
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/security/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })
            print("Successfully logged in to Superset")
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def create_database_connection(self):
        """Create or get the database connection"""
        # Check if database already exists
        response = self.session.get(f"{SUPERSET_URL}/api/v1/database/")
        
        if response.status_code == 200:
            databases = response.json()["result"]
            for db in databases:
                if db["database_name"] == DATABASE_NAME:
                    self.database_id = db["id"]
                    print(f"Found existing database connection with ID {self.database_id}")
                    return
        
        # Create new database connection
        database_data = {
            "database_name": DATABASE_NAME,
            "engine": "postgresql",
            "sqlalchemy_uri": f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}",
            "expose_in_sqllab": True,
            "allow_ctas": True,
            "allow_cvas": True,
            "allow_dml": True,
            "allow_multi_schema_metadata_fetch": True,
            "extra": json.dumps({
                "allows_virtual_table_explore": True,
                "schemas_allowed_for_csv_upload": ["entity", "mart", "staging", "intermediate"]
            })
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/database/",
            json=database_data
        )
        
        if response.status_code in [200, 201]:
            self.database_id = response.json()["id"]
            print(f"Created database connection with ID {self.database_id}")
        else:
            raise Exception(f"Failed to create database: {response.text}")
    
    def create_dataset(self, table_name: str, schema: str = "mart") -> int:
        """Create a dataset for a table"""
        dataset_data = {
            "database": self.database_id,
            "schema": schema,
            "table_name": table_name,
            "is_managed_externally": False,
            "external_url": None
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            json=dataset_data
        )
        
        if response.status_code in [200, 201]:
            dataset_id = response.json()["id"]
            print(f"Created dataset for {schema}.{table_name} with ID {dataset_id}")
            return dataset_id
        else:
            # Check if dataset already exists
            response = self.session.get(
                f"{SUPERSET_URL}/api/v1/dataset/",
                params={"q": f'(filters:!((col:table_name,opr:eq,value:{table_name})))'}
            )
            if response.status_code == 200 and response.json()["count"] > 0:
                dataset_id = response.json()["result"][0]["id"]
                print(f"Dataset for {schema}.{table_name} already exists with ID {dataset_id}")
                return dataset_id
            else:
                raise Exception(f"Failed to create dataset: {response.text}")
    
    def create_chart(self, chart_config: Dict[str, Any]) -> int:
        """Create a chart"""
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/chart/",
            json=chart_config
        )
        
        if response.status_code in [200, 201]:
            chart_id = response.json()["id"]
            print(f"Created chart '{chart_config['slice_name']}' with ID {chart_id}")
            return chart_id
        else:
            raise Exception(f"Failed to create chart: {response.text}")
    
    def create_dashboard(self, dashboard_name: str, chart_ids: List[int], position_json: str) -> int:
        """Create a dashboard with charts"""
        dashboard_data = {
            "dashboard_title": dashboard_name,
            "slug": dashboard_name.lower().replace(" ", "-"),
            "owners": [],
            "position_json": position_json,
            "css": "",
            "json_metadata": json.dumps({
                "filter_scopes": {},
                "expanded_slices": {},
                "refresh_frequency": 0,
                "default_filters": "{}",
                "color_scheme": "supersetColors",
                "label_colors": {},
                "shared_label_colors": {},
                "color_scheme_domain": [],
                "cross_filters_enabled": False
            }),
            "published": True
        }
        
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            json=dashboard_data
        )
        
        if response.status_code in [200, 201]:
            dashboard_id = response.json()["id"]
            print(f"Created dashboard '{dashboard_name}' with ID {dashboard_id}")
            
            # Add charts to dashboard
            for chart_id in chart_ids:
                self.session.post(
                    f"{SUPERSET_URL}/api/v1/dashboard/{dashboard_id}/charts",
                    json={"chart_ids": [chart_id]}
                )
            
            return dashboard_id
        else:
            raise Exception(f"Failed to create dashboard: {response.text}")

def create_executive_dashboard(creator: SupersetDashboardCreator):
    """Create executive summary dashboard using entity tables"""
    print("\n=== Creating Executive Dashboard ===")
    
    # Create datasets from entity tables
    customers_id = creator.create_dataset("entity_customers", schema="entity")
    
    charts = []
    
    # Key metrics
    charts.append(creator.create_chart({
        "slice_name": "Total Active Customers",
        "viz_type": "big_number_total",
        "datasource_id": customers_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "customer_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Active Customers"
            }],
            "filters": [{"col": "is_active", "op": "==", "val": True}]
        })
    }))
    
    charts.append(creator.create_chart({
        "slice_name": "Total MRR",
        "viz_type": "big_number_total", 
        "datasource_id": customers_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "monthly_recurring_revenue"},
                "aggregate": "SUM",
                "label": "Total MRR"
            }],
            "filters": [{"col": "is_active", "op": "==", "val": True}]
        })
    }))
    
    charts.append(creator.create_chart({
        "slice_name": "Average Customer Health Score",
        "viz_type": "big_number_total",
        "datasource_id": customers_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "customer_health_score"},
                "aggregate": "AVG",
                "label": "Avg Health Score"
            }],
            "filters": [{"col": "is_active", "op": "==", "val": True}]
        })
    }))
    
    charts.append(creator.create_chart({
        "slice_name": "Customer Health Distribution",
        "viz_type": "pie",
        "datasource_id": customers_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "customer_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Customers"
            }],
            "groupby": ["customer_tier"],
            "row_limit": 10,
            "donut": True,
            "show_legend": True
        })
    }))
    
    # Create dashboard
    position_json = json.dumps({
        "CHART-1": {"children": [], "id": "CHART-1", "meta": {"chartId": charts[0], "height": 30, "width": 3}, "type": "CHART"},
        "CHART-2": {"children": [], "id": "CHART-2", "meta": {"chartId": charts[1], "height": 30, "width": 3}, "type": "CHART"},
        "CHART-3": {"children": [], "id": "CHART-3", "meta": {"chartId": charts[2], "height": 30, "width": 3}, "type": "CHART"},
        "CHART-4": {"children": [], "id": "CHART-4", "meta": {"chartId": charts[3], "height": 30, "width": 3}, "type": "CHART"},
        "GRID_ID": {"children": ["CHART-1", "CHART-2", "CHART-3", "CHART-4"], "id": "GRID_ID", "type": "GRID"}
    })
    
    creator.create_dashboard("Executive Summary Dashboard", charts, position_json)

def create_customer_analytics_dashboard(creator: SupersetDashboardCreator):
    """Create customer analytics dashboard"""
    print("\n=== Creating Customer Analytics Dashboard ===")
    
    # Create datasets
    customers_daily_id = creator.create_dataset("entity_customers_daily", schema="entity")
    customers_history_id = creator.create_dataset("entity_customers_history", schema="entity")
    
    charts = []
    
    # MRR Growth Chart
    charts.append(creator.create_chart({
        "slice_name": "MRR Growth Trend",
        "viz_type": "line",
        "datasource_id": customers_daily_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "total_mrr"},
                "aggregate": "SUM",
                "label": "Total MRR"
            }],
            "groupby": ["snapshot_date"],
            "time_range": "Last 90 days",
            "row_limit": 10000,
            "x_axis_label": "Date",
            "y_axis_label": "MRR ($)"
        })
    }))
    
    # Customer Count Trend
    charts.append(creator.create_chart({
        "slice_name": "Active Customer Count Trend",
        "viz_type": "area",
        "datasource_id": customers_daily_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE", 
                "column": {"column_name": "active_customers"},
                "aggregate": "SUM",
                "label": "Active Customers"
            }],
            "groupby": ["snapshot_date"],
            "time_range": "Last 90 days",
            "row_limit": 10000,
            "show_brush": True
        })
    }))
    
    # Churn Analysis
    charts.append(creator.create_chart({
        "slice_name": "Monthly Churn Rate",
        "viz_type": "line",
        "datasource_id": customers_daily_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SQL",
                "sqlExpression": "CASE WHEN SUM(active_customers) > 0 THEN (SUM(churned_customers)::FLOAT / SUM(active_customers)) * 100 ELSE 0 END",
                "label": "Churn Rate %"
            }],
            "groupby": ["snapshot_date"],
            "time_range": "Last 180 days",
            "row_limit": 10000
        })
    }))
    
    # Customer Cohort Analysis
    charts.append(creator.create_chart({
        "slice_name": "Customer Cohort Retention",
        "viz_type": "heatmap",
        "datasource_id": customers_daily_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "retention_rate"},
                "aggregate": "AVG",
                "label": "Retention Rate"
            }],
            "groupby": ["cohort_month", "months_since_acquisition"],
            "row_limit": 500
        })
    }))
    
    # Create dashboard
    position_json = json.dumps({
        "CHART-1": {"children": [], "id": "CHART-1", "meta": {"chartId": charts[0], "height": 50, "width": 6}, "type": "CHART"},
        "CHART-2": {"children": [], "id": "CHART-2", "meta": {"chartId": charts[1], "height": 50, "width": 6}, "type": "CHART"},
        "CHART-3": {"children": [], "id": "CHART-3", "meta": {"chartId": charts[2], "height": 50, "width": 6}, "type": "CHART"},
        "CHART-4": {"children": [], "id": "CHART-4", "meta": {"chartId": charts[3], "height": 50, "width": 6}, "type": "CHART"},
        "GRID_ID": {"children": ["CHART-1", "CHART-2", "CHART-3", "CHART-4"], "id": "GRID_ID", "type": "GRID"}
    })
    
    creator.create_dashboard("Customer Analytics Dashboard", charts, position_json)

def main():
    """Main function to create all dashboards"""
    creator = SupersetDashboardCreator()
    
    try:
        # Login to Superset
        creator.login()
        
        # Create database connection
        creator.create_database_connection()
        
        # Create dashboards
        create_executive_dashboard(creator)
        create_customer_analytics_dashboard(creator)
        
        print("\n✅ All dashboards created successfully!")
        print(f"\nAccess dashboards at: {SUPERSET_URL}/dashboard/list/")
        
    except Exception as e:
        print(f"\n❌ Error creating dashboards: {e}")
        raise

if __name__ == "__main__":
    main()
