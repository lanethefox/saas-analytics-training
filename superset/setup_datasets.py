#!/usr/bin/env python3
"""
Setup all datasets in Apache Superset via API
Creates datasets for all dashboards (Sales, CX, Marketing, Product, Executive)
"""

import requests
import json
import time
from typing import Dict, List, Optional

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin_password_2024"

class SupersetDatasetManager:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        self.access_token = None
        self.database_id = None
        
    def get_csrf_token(self):
        """Get CSRF token from Superset"""
        response = self.session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/")
        if response.status_code == 200:
            self.csrf_token = response.json()['result']
            return True
        return False
    
    def login(self):
        """Login to Superset using the API"""
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
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'X-CSRFToken': self.csrf_token
            })
            print("✓ Successfully logged in to Superset")
            return True
        else:
            print(f"✗ Failed to login: {response.status_code} - {response.text}")
            return False
    
    def get_database_id(self):
        """Get the PostgreSQL database ID"""
        response = self.session.get(
            f"{SUPERSET_URL}/api/v1/database/",
            params={"q": '(filters:!((col:database_name,opr:ct,value:postgres)))'}
        )
        
        if response.status_code == 200:
            databases = response.json()
            if databases['count'] > 0:
                self.database_id = databases['result'][0]['id']
                print(f"✓ Found PostgreSQL database (ID: {self.database_id})")
                return True
        
        print("✗ Could not find PostgreSQL database")
        return False
    
    def create_dataset(self, schema: str, table_name: str, description: str = "") -> Optional[int]:
        """Create a dataset in Superset"""
        dataset_data = {
            "database": self.database_id,
            "schema": schema,
            "table_name": table_name,
            "description": description,
            "is_managed_externally": False,
            "external_url": None
        }
        
        # Check if dataset already exists
        check_response = self.session.get(
            f"{SUPERSET_URL}/api/v1/dataset/",
            params={
                "q": f'(filters:!((col:table_name,opr:eq,value:{table_name}),(col:schema,opr:eq,value:{schema})))'
            }
        )
        
        if check_response.status_code == 200 and check_response.json()['count'] > 0:
            dataset_id = check_response.json()['result'][0]['id']
            print(f"  → Dataset already exists: {schema}.{table_name} (ID: {dataset_id})")
            return dataset_id
        
        # Create new dataset
        response = self.session.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            json=dataset_data
        )
        
        if response.status_code in [200, 201]:
            dataset_id = response.json()['id']
            print(f"✓ Created dataset: {schema}.{table_name} (ID: {dataset_id})")
            
            # Refresh columns
            self.refresh_dataset_columns(dataset_id)
            return dataset_id
        else:
            print(f"✗ Failed to create dataset {schema}.{table_name}: {response.status_code} - {response.text}")
            return None
    
    def refresh_dataset_columns(self, dataset_id: int):
        """Refresh columns for a dataset"""
        response = self.session.put(
            f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}/refresh"
        )
        
        if response.status_code == 200:
            print(f"  → Refreshed columns for dataset {dataset_id}")
        else:
            print(f"  → Failed to refresh columns: {response.status_code}")
    
    def update_dataset_metrics(self, dataset_id: int, metrics: List[Dict]):
        """Add calculated metrics to a dataset"""
        for metric in metrics:
            metric_data = {
                "expression": metric["expression"],
                "metric_name": metric["name"],
                "metric_type": metric.get("type", "sum"),
                "description": metric.get("description", ""),
                "d3format": metric.get("format", ".2f"),
                "datasource_id": dataset_id
            }
            
            response = self.session.post(
                f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}/metric/",
                json=metric_data
            )
            
            if response.status_code in [200, 201]:
                print(f"  → Added metric: {metric['name']}")
            else:
                print(f"  → Failed to add metric {metric['name']}: {response.status_code}")
    
    def setup_all_datasets(self):
        """Create all datasets for all dashboards"""
        print("\n=== Setting up Superset Datasets ===\n")
        
        # Dataset definitions
        datasets = {
            "Universal Datasets": [
                ("public", "metrics_unified", "Combined metrics from all domains"),
                ("public", "metrics_company_overview", "Executive-level metric rollups"),
                ("entity", "entity_customers", "Customer master data with health scores"),
                ("entity", "entity_customers_daily", "Daily customer metrics and trends"),
                ("entity", "entity_customers_history", "Customer change history"),
            ],
            
            "Sales Datasets": [
                ("public", "metrics_sales", "Aggregated sales metrics"),
                ("mart", "mart_sales__pipeline", "Sales pipeline details"),
                ("marketing", "marketing_qualified_leads", "MQL data for sales"),
                ("hubspot", "deals", "HubSpot deals data"),
                ("hubspot", "companies", "HubSpot companies data"),
            ],
            
            "Customer Success Datasets": [
                ("public", "metrics_customer_success", "Customer success KPIs"),
                ("entity", "entity_users", "User activity and engagement"),
                ("entity", "entity_features", "Feature adoption metrics"),
                ("entity", "entity_users_daily", "Daily user metrics"),
                ("entity", "entity_subscriptions", "Subscription details"),
            ],
            
            "Marketing Datasets": [
                ("public", "metrics_marketing", "Marketing performance metrics"),
                ("entity", "entity_campaigns", "Campaign master data"),
                ("entity", "entity_campaigns_daily", "Daily campaign performance"),
                ("entity", "entity_campaigns_history", "Campaign change history"),
                ("mart", "mart_marketing__attribution", "Multi-touch attribution"),
            ],
            
            "Product Analytics Datasets": [
                ("public", "metrics_product_analytics", "Product usage metrics"),
                ("public", "metrics_engagement", "User engagement metrics"),
                ("entity", "entity_devices", "Device performance data"),
                ("entity", "entity_devices_daily", "Daily device metrics"),
                ("staging", "stg_app_database__page_views", "Page view events"),
                ("staging", "stg_app_database__feature_usage", "Feature usage events"),
            ],
            
            "Operations Datasets": [
                ("public", "metrics_operations", "Operational metrics"),
                ("public", "metrics_revenue", "Revenue metrics"),
                ("entity", "entity_locations", "Location master data"),
                ("entity", "entity_locations_daily", "Daily location metrics"),
            ],
            
            "Executive Dashboard Views": [
                ("public", "metrics_api", "API-friendly metrics view"),
                ("public", "superset_sales_kpis", "Sales KPI view"),
                ("public", "superset_sales_pipeline_stages", "Pipeline stages view"),
                ("public", "superset_sales_daily_revenue", "Daily revenue view"),
                ("public", "superset_sales_rep_performance", "Sales rep metrics"),
                ("public", "superset_sales_deals", "Deal details view"),
                ("public", "superset_sales_monthly_metrics", "Monthly sales metrics"),
            ]
        }
        
        # Create datasets by category
        created_datasets = {}
        
        for category, dataset_list in datasets.items():
            print(f"\n{category}:")
            print("-" * len(category))
            
            for schema, table, description in dataset_list:
                dataset_id = self.create_dataset(schema, table, description)
                if dataset_id:
                    created_datasets[f"{schema}.{table}"] = dataset_id
                time.sleep(0.5)  # Rate limiting
        
        # Add calculated metrics to specific datasets
        print("\n\nAdding Calculated Metrics:")
        print("-" * 25)
        
        # Sales metrics
        if "public.metrics_sales" in created_datasets:
            self.update_dataset_metrics(
                created_datasets["public.metrics_sales"],
                [
                    {
                        "name": "win_rate_pct",
                        "expression": "win_rate * 100",
                        "description": "Win rate percentage",
                        "format": ".1%"
                    },
                    {
                        "name": "pipeline_coverage",
                        "expression": "pipeline_value / (total_revenue / 3)",
                        "description": "Pipeline coverage ratio",
                        "format": ".1f"
                    }
                ]
            )
        
        # Customer success metrics
        if "public.metrics_customer_success" in created_datasets:
            self.update_dataset_metrics(
                created_datasets["public.metrics_customer_success"],
                [
                    {
                        "name": "churn_rate_pct",
                        "expression": "churn_rate * 100",
                        "description": "Monthly churn rate percentage",
                        "format": ".1%"
                    },
                    {
                        "name": "health_trend",
                        "expression": "avg_health_score - LAG(avg_health_score, 1)",
                        "description": "Health score trend",
                        "format": "+.1f"
                    }
                ]
            )
        
        print(f"\n\n✓ Successfully created {len(created_datasets)} datasets")
        return created_datasets
    
    def create_virtual_datasets(self):
        """Create SQL-based virtual datasets for complex queries"""
        print("\n\nCreating Virtual Datasets:")
        print("-" * 25)
        
        virtual_datasets = [
            {
                "name": "Customer Health Summary",
                "sql": """
                    SELECT 
                        c.customer_id,
                        c.customer_name,
                        c.health_score,
                        c.health_category,
                        c.churn_risk_score,
                        c.customer_mrr,
                        c.customer_tier,
                        u.active_users,
                        u.avg_engagement_score
                    FROM entity.entity_customers c
                    LEFT JOIN (
                        SELECT 
                            account_id,
                            COUNT(*) as active_users,
                            AVG(engagement_score) as avg_engagement_score
                        FROM entity.entity_users
                        WHERE user_status = 'active'
                        GROUP BY account_id
                    ) u ON c.customer_id = u.account_id
                    WHERE c.customer_status = 'active'
                """
            },
            {
                "name": "Sales Velocity Metrics",
                "sql": """
                    SELECT 
                        DATE_TRUNC('week', created_date) as week,
                        stage_name,
                        COUNT(DISTINCT deal_id) as deals_created,
                        SUM(amount) as total_value,
                        AVG(days_to_close) as avg_velocity,
                        AVG(probability) as avg_probability
                    FROM mart.mart_sales__pipeline
                    WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
                    GROUP BY week, stage_name
                """
            }
        ]
        
        for vd in virtual_datasets:
            dataset_data = {
                "database": self.database_id,
                "table_name": vd["name"].lower().replace(" ", "_"),
                "sql": vd["sql"],
                "description": f"Virtual dataset: {vd['name']}",
                "is_managed_externally": False
            }
            
            response = self.session.post(
                f"{SUPERSET_URL}/api/v1/dataset/",
                json=dataset_data
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Created virtual dataset: {vd['name']}")
            else:
                print(f"✗ Failed to create virtual dataset: {vd['name']}")

def main():
    manager = SupersetDatasetManager()
    
    # Get CSRF token
    if not manager.get_csrf_token():
        print("Failed to get CSRF token")
        return
    
    # Login to Superset
    if not manager.login():
        print("Failed to login to Superset")
        return
    
    # Get database ID
    if not manager.get_database_id():
        print("Failed to find database")
        return
    
    # Create all datasets
    datasets = manager.setup_all_datasets()
    
    # Create virtual datasets
    manager.create_virtual_datasets()
    
    print("\n\n🎉 Dataset setup complete!")
    print(f"Created {len(datasets)} datasets in Superset")
    print(f"\nNext steps:")
    print("1. Navigate to Superset: {SUPERSET_URL}")
    print("2. Go to Data → Datasets to verify")
    print("3. Start creating charts using these datasets")

if __name__ == "__main__":
    main()