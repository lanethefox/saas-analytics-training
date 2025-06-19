#!/bin/bash
# Superset Setup Script using superset shell

echo "🚀 Setting up Superset datasets, charts, and dashboards"
echo "============================================================"

# Create datasets using superset shell
echo -e "\n📊 Creating datasets..."
docker exec saas_platform_superset superset shell << 'EOF'
from superset import db
from superset.connectors.sqla.models import SqlaTable
from superset.models.core import Database

# Get the database
database = db.session.query(Database).filter_by(id=3).first()
if not database:
    print("❌ Database ID 3 not found!")
    exit()

# Tables to create
tables = [
    # Entity Layer - Core Tables
    ("entity", "entity_customers", "Customer master data with health scores and MRR"),
    ("entity", "entity_devices", "IoT device registry with performance metrics"),
    ("entity", "entity_users", "User profiles with engagement scores"),
    ("entity", "entity_subscriptions", "Subscription lifecycle and revenue data"),
    ("entity", "entity_locations", "Location operational metrics"),
    ("entity", "entity_campaigns", "Marketing campaign performance"),
    ("entity", "entity_features", "Product feature adoption metrics"),
    
    # Entity Layer - History Tables
    ("entity", "entity_customers_history", "Customer state change history"),
    ("entity", "entity_devices_history", "Device lifecycle events"),
    ("entity", "entity_users_history", "User engagement evolution"),
    ("entity", "entity_subscriptions_history", "Subscription modifications"),
    
    # Entity Layer - Grain Tables
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
]

created = 0
for schema, table_name, desc in tables:
    existing = db.session.query(SqlaTable).filter_by(
        database_id=3, schema=schema, table_name=table_name
    ).first()
    
    if not existing:
        table = SqlaTable(
            table_name=table_name,
            schema=schema,
            database=database,
            database_id=3,
            description=desc
        )
        db.session.add(table)
        print(f"✅ Created: {schema}.{table_name}")
        created += 1
    else:
        print(f"ℹ️  Exists: {schema}.{table_name}")

db.session.commit()
print(f"\n✅ Created {created} new datasets")

# Sync columns for all tables
print("\n🔄 Syncing table columns...")
for schema, table_name, _ in tables:
    table = db.session.query(SqlaTable).filter_by(
        database_id=3, schema=schema, table_name=table_name
    ).first()
    if table:
        try:
            table.fetch_metadata()
            print(f"✅ Synced: {schema}.{table_name}")
        except Exception as e:
            print(f"⚠️  Failed to sync {schema}.{table_name}: {str(e)}")

db.session.commit()
print("\n✅ Dataset setup complete!")
exit()
EOF

# Create charts
echo -e "\n📈 Creating charts..."
docker exec saas_platform_superset superset shell << 'EOF'
import json
from superset import db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

charts = [
    {
        "name": "Customer Health Distribution",
        "viz": "pie",
        "table": "entity_customers",
        "params": {
            "viz_type": "pie",
            "groupby": ["customer_health_tier"],
            "metric": "count",
            "donut": True,
            "show_legend": True,
            "show_labels": True
        }
    },
    {
        "name": "MRR by Customer Tier",
        "viz": "dist_bar", 
        "table": "entity_customers",
        "params": {
            "viz_type": "dist_bar",
            "groupby": ["customer_health_tier"],
            "metrics": ["sum__monthly_recurring_revenue"],
            "order_bars": True
        }
    },
    {
        "name": "Device Fleet Status",
        "viz": "pie",
        "table": "entity_devices",
        "params": {
            "viz_type": "pie",
            "groupby": ["device_status"],
            "metric": "count",
            "donut": True
        }
    },
    {
        "name": "User Engagement Distribution",
        "viz": "histogram",
        "table": "entity_users",
        "params": {
            "viz_type": "histogram",
            "all_columns_x": ["engagement_score"],
            "bins": 20
        }
    },
    {
        "name": "Top At-Risk Customers",
        "viz": "table",
        "table": "entity_customers",
        "params": {
            "viz_type": "table",
            "groupby": ["company_name", "customer_health_tier"],
            "metrics": ["sum__monthly_recurring_revenue", "max__churn_risk_score"],
            "row_limit": 20,
            "include_search": True
        }
    }
]

created = 0
for chart in charts:
    # Find datasource
    ds = db.session.query(SqlaTable).filter_by(table_name=chart["table"]).first()
    if not ds:
        print(f"⚠️  Table not found: {chart['table']}")
        continue
    
    # Check if exists
    existing = db.session.query(Slice).filter_by(slice_name=chart["name"]).first()
    if not existing:
        slice = Slice(
            slice_name=chart["name"],
            viz_type=chart["viz"],
            datasource_type="table",
            datasource_id=ds.id,
            datasource_name=ds.table_name,
            params=json.dumps(chart["params"])
        )
        db.session.add(slice)
        print(f"✅ Created chart: {chart['name']}")
        created += 1
    else:
        print(f"ℹ️  Chart exists: {chart['name']}")

db.session.commit()
print(f"\n✅ Created {created} new charts")
exit()
EOF

# Create dashboards
echo -e "\n🎨 Creating dashboards..."
docker exec saas_platform_superset superset shell << 'EOF'
import json
from superset import db
from superset.models.dashboard import Dashboard
from superset.models.slice import Slice

# Create Customer Success Dashboard
dash = Dashboard(
    dashboard_title="🎯 Customer Success Command Center",
    slug="customer-success",
    published=True
)

# Add charts
chart_names = ["Customer Health Distribution", "MRR by Customer Tier", "Top At-Risk Customers"]
for name in chart_names:
    chart = db.session.query(Slice).filter_by(slice_name=name).first()
    if chart:
        dash.slices.append(chart)

existing = db.session.query(Dashboard).filter_by(slug="customer-success").first()
if not existing:
    db.session.add(dash)
    db.session.commit()
    print("✅ Created Customer Success Dashboard")
else:
    print("ℹ️  Customer Success Dashboard already exists")

# Create Operations Dashboard
ops_dash = Dashboard(
    dashboard_title="⚙️ Operations Command Center",
    slug="operations",
    published=True
)

chart_names = ["Device Fleet Status"]
for name in chart_names:
    chart = db.session.query(Slice).filter_by(slice_name=name).first()
    if chart:
        ops_dash.slices.append(chart)

existing = db.session.query(Dashboard).filter_by(slug="operations").first()
if not existing:
    db.session.add(ops_dash)
    db.session.commit()
    print("✅ Created Operations Dashboard")
else:
    print("ℹ️  Operations Dashboard already exists")

print("\n✅ Dashboard setup complete!")
exit()
EOF

echo -e "\n============================================================"
echo "🎉 Setup Complete!"
echo "============================================================"
echo -e "\n📝 Access your dashboards at http://localhost:8088"
echo "   Username: admin"
echo "   Password: admin_password_2024"
echo -e "\n📊 Available Dashboards:"
echo "   • Customer Success: http://localhost:8088/superset/dashboard/customer-success/"
echo "   • Operations: http://localhost:8088/superset/dashboard/operations/"
echo -e "\n💡 Next Steps:"
echo "   1. Visit the dashboards"
echo "   2. Create additional charts as needed"
echo "   3. Add filters and cross-filtering"
echo "   4. Set up scheduled reports"
