#!/usr/bin/env python3
"""
Superset Setup using CLI Commands
Creates datasets, charts, and dashboards using Superset CLI
"""

import subprocess
import json
import time

def run_superset_command(command):
    """Run a command inside the Superset container"""
    full_command = f"docker exec saas_platform_superset {command}"
    print(f"Running: {command}")
    
    result = subprocess.run(
        full_command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return True, result.stdout
    else:
        return False, result.stderr

def create_datasets_script():
    """Create a Python script to run inside Superset container"""
    script_content = '''
import logging
from superset import app, db
from superset.connectors.sqla.models import SqlaTable
from superset.models.core import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tables to create
tables_config = [
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
    ("entity", "entity_customers_daily", "Daily customer snapshots"),
    ("entity", "entity_devices_hourly", "Hourly device metrics"),
    ("entity", "entity_users_weekly", "Weekly user engagement"),
    ("entity", "entity_subscriptions_monthly", "Monthly subscription cohorts"),
    
    # Mart Layer
    ("mart", "mart_customer_success__health", "Customer health and risk analysis"),
    ("mart", "mart_sales__pipeline", "Sales pipeline and conversion"),
    ("mart", "mart_marketing__attribution", "Multi-touch attribution"),
    ("mart", "mart_product__adoption", "Feature adoption analytics"),
    ("mart", "mart_operations__performance", "Operational KPIs"),
    ("mart", "mart_device_operations", "Device fleet management"),
    ("mart", "operations_device_monitoring", "Real-time monitoring")
]

with app.app_context():
    # Get the database
    database = db.session.query(Database).filter_by(id=3).first()
    if not database:
        logger.error("Database ID 3 not found!")
        exit(1)
    
    created_count = 0
    
    for schema, table_name, description in tables_config:
        # Check if table already exists
        existing = db.session.query(SqlaTable).filter_by(
            database_id=3,
            schema=schema,
            table_name=table_name
        ).first()
        
        if not existing:
            # Create new table
            table = SqlaTable(
                table_name=table_name,
                schema=schema,
                database=database,
                database_id=3,
                description=description
            )
            
            db.session.add(table)
            logger.info(f"Created dataset: {schema}.{table_name}")
            created_count += 1
        else:
            logger.info(f"Dataset already exists: {schema}.{table_name}")
    
    # Commit all changes
    db.session.commit()
    logger.info(f"Created {created_count} new datasets")
    
    # Sync columns for all tables
    for schema, table_name, _ in tables_config:
        table = db.session.query(SqlaTable).filter_by(
            database_id=3,
            schema=schema,
            table_name=table_name
        ).first()
        
        if table:
            try:
                table.fetch_metadata()
                db.session.commit()
                logger.info(f"Synced columns for {schema}.{table_name}")
            except Exception as e:
                logger.warning(f"Could not sync columns for {schema}.{table_name}: {str(e)}")

print("Dataset creation complete!")
'''
    
    # Write script to file
    with open('/tmp/create_superset_datasets.py', 'w') as f:
        f.write(script_content)
    
    # Copy script to container
    subprocess.run(
        "docker cp /tmp/create_superset_datasets.py saas_platform_superset:/tmp/",
        shell=True
    )
    
    return True

def create_charts_script():
    """Create a Python script to create charts"""
    script_content = '''
import json
from superset import app, db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

charts_config = [
    {
        "slice_name": "Customer Health Distribution",
        "viz_type": "pie",
        "datasource_name": "entity_customers",
        "params": {
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
            "donut": True,
            "innerRadius": 30
        }
    },
    {
        "slice_name": "MRR by Customer Tier",
        "viz_type": "dist_bar",
        "datasource_name": "entity_customers",
        "params": {
            "viz_type": "dist_bar",
            "groupby": ["customer_health_tier"],
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "monthly_recurring_revenue"},
                "aggregate": "SUM",
                "label": "Total MRR"
            }],
            "y_axis_format": "$,.0f"
        }
    },
    {
        "slice_name": "Device Fleet Status",
        "viz_type": "sunburst",
        "datasource_name": "entity_devices",
        "params": {
            "viz_type": "sunburst",
            "groupby": ["device_status", "device_type"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "device_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Device Count"
            }
        }
    },
    {
        "slice_name": "Sales Pipeline Funnel",
        "viz_type": "funnel",
        "datasource_name": "mart_sales__pipeline",
        "params": {
            "viz_type": "funnel",
            "groupby": ["pipeline_stage"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "opportunity_value"},
                "aggregate": "SUM",
                "label": "Pipeline Value"
            }
        }
    },
    {
        "slice_name": "Marketing Channel Performance",
        "viz_type": "treemap",
        "datasource_name": "mart_marketing__attribution", 
        "params": {
            "viz_type": "treemap",
            "groupby": ["channel", "campaign_type"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "attributed_revenue"},
                "aggregate": "SUM",
                "label": "Revenue"
            }
        }
    }
]

with app.app_context():
    created_count = 0
    
    for chart_config in charts_config:
        # Find the datasource
        datasource = db.session.query(SqlaTable).filter_by(
            table_name=chart_config["datasource_name"]
        ).first()
        
        if not datasource:
            print(f"Datasource not found: {chart_config['datasource_name']}")
            continue
        
        # Check if slice already exists
        existing = db.session.query(Slice).filter_by(
            slice_name=chart_config["slice_name"]
        ).first()
        
        if not existing:
            slice = Slice(
                slice_name=chart_config["slice_name"],
                viz_type=chart_config["viz_type"],
                datasource_type="table",
                datasource_id=datasource.id,
                datasource_name=datasource.table_name,
                params=json.dumps(chart_config["params"])
            )
            
            db.session.add(slice)
            print(f"Created chart: {chart_config['slice_name']}")
            created_count += 1
        else:
            print(f"Chart already exists: {chart_config['slice_name']}")
    
    db.session.commit()
    print(f"Created {created_count} new charts")
'''
    
    with open('/tmp/create_superset_charts.py', 'w') as f:
        f.write(script_content)
    
    subprocess.run(
        "docker cp /tmp/create_superset_charts.py saas_platform_superset:/tmp/",
        shell=True
    )
    
    return True

def create_dashboards_script():
    """Create a Python script to create dashboards"""
    script_content = '''
import json
from superset import app, db
from superset.models.dashboard import Dashboard
from superset.models.slice import Slice

dashboards_config = [
    {
        "dashboard_title": "🎯 Customer Success Command Center",
        "slug": "customer-success",
        "slices": ["Customer Health Distribution", "MRR by Customer Tier"],
        "position_json": {
            "DASHBOARD_VERSION_KEY": "v2",
            "GRID_ID": {
                "id": "GRID_ID",
                "type": "GRID",
                "children": ["ROW-1"]
            },
            "HEADER_ID": {
                "id": "HEADER_ID",
                "type": "HEADER",
                "meta": {"text": "Customer Success Command Center"}
            },
            "ROW-1": {
                "id": "ROW-1",
                "type": "ROW",
                "children": ["CHART-1", "CHART-2"]
            }
        }
    },
    {
        "dashboard_title": "⚙️ Operations Command Center",
        "slug": "operations",
        "slices": ["Device Fleet Status"],
        "position_json": {
            "DASHBOARD_VERSION_KEY": "v2",
            "GRID_ID": {
                "id": "GRID_ID", 
                "type": "GRID",
                "children": ["ROW-1"]
            },
            "HEADER_ID": {
                "id": "HEADER_ID",
                "type": "HEADER",
                "meta": {"text": "Operations Command Center"}
            },
            "ROW-1": {
                "id": "ROW-1",
                "type": "ROW",
                "children": ["CHART-1"]
            }
        }
    },
    {
        "dashboard_title": "💰 Sales Pipeline",
        "slug": "sales-pipeline",
        "slices": ["Sales Pipeline Funnel"],
        "position_json": {}
    },
    {
        "dashboard_title": "📈 Marketing Attribution",
        "slug": "marketing",
        "slices": ["Marketing Channel Performance"],
        "position_json": {}
    }
]

with app.app_context():
    created_count = 0
    
    for dash_config in dashboards_config:
        # Check if dashboard already exists
        existing = db.session.query(Dashboard).filter_by(
            slug=dash_config["slug"]
        ).first()
        
        if not existing:
            dashboard = Dashboard(
                dashboard_title=dash_config["dashboard_title"],
                slug=dash_config["slug"],
                published=True,
                position_json=json.dumps(dash_config.get("position_json", {}))
            )
            
            # Add slices
            for slice_name in dash_config["slices"]:
                slice = db.session.query(Slice).filter_by(
                    slice_name=slice_name
                ).first()
                if slice:
                    dashboard.slices.append(slice)
            
            db.session.add(dashboard)
            print(f"Created dashboard: {dash_config['dashboard_title']}")
            created_count += 1
        else:
            print(f"Dashboard already exists: {dash_config['dashboard_title']}")
    
    db.session.commit()
    print(f"Created {created_count} new dashboards")
'''
    
    with open('/tmp/create_superset_dashboards.py', 'w') as f:
        f.write(script_content)
    
    subprocess.run(
        "docker cp /tmp/create_superset_dashboards.py saas_platform_superset:/tmp/",
        shell=True
    )
    
    return True

def main():
    """Main execution function"""
    print("🚀 Superset Setup via CLI")
    print("=" * 60)
    
    # Create and run dataset creation script
    print("\n📊 Creating datasets...")
    create_datasets_script()
    success, output = run_superset_command("python /tmp/create_superset_datasets.py")
    if success:
        print("✅ Datasets created successfully")
    else:
        print(f"❌ Dataset creation failed: {output}")
    
    # Wait a bit for datasets to be fully created
    time.sleep(2)
    
    # Create and run charts creation script
    print("\n📈 Creating charts...")
    create_charts_script()
    success, output = run_superset_command("python /tmp/create_superset_charts.py")
    if success:
        print("✅ Charts created successfully")
    else:
        print(f"❌ Chart creation failed: {output}")
    
    # Create and run dashboards creation script
    print("\n🎨 Creating dashboards...")
    create_dashboards_script()
    success, output = run_superset_command("python /tmp/create_superset_dashboards.py")
    if success:
        print("✅ Dashboards created successfully")
    else:
        print(f"❌ Dashboard creation failed: {output}")
    
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    
    print("\n📝 Access your dashboards at http://localhost:8088")
    print("   • Customer Success: /superset/dashboard/customer-success/")
    print("   • Operations: /superset/dashboard/operations/")
    print("   • Sales Pipeline: /superset/dashboard/sales-pipeline/")
    print("   • Marketing: /superset/dashboard/marketing/")
    
    print("\n🔑 Login: admin / admin_password_2024")

if __name__ == "__main__":
    main()
