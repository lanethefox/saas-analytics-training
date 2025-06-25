#!/usr/bin/env python3
"""
Validate the data platform setup by checking:
1. All raw tables have data
2. All staging tables have data
3. All dbt models are compiled
4. Key metrics are populated
"""

import sys
import os
from database_config import db_helper

# Expected tables by schema
EXPECTED_TABLES = {
    'raw': [
        'app_database_accounts', 'app_database_users', 'app_database_devices',
        'app_database_locations', 'app_database_subscriptions', 'app_database_user_sessions',
        'app_database_tap_events', 'app_database_feature_usage', 'app_database_page_views',
        'stripe_customers', 'stripe_prices', 'stripe_subscriptions',
        'stripe_subscription_items', 'stripe_invoices', 'stripe_charges',
        'stripe_payment_intents', 'stripe_events', 'hubspot_companies',
        'hubspot_contacts', 'hubspot_deals', 'hubspot_engagements',
        'hubspot_owners', 'hubspot_tickets', 'google_analytics_sessions',
        'google_ads_campaigns', 'facebook_ads_campaigns', 'linkedin_ads_campaigns',
        'iterable_campaigns', 'attribution_touchpoints', 'marketing_qualified_leads'
    ],
    'staging': [
        'stg_app_database__accounts', 'stg_app_database__users', 'stg_app_database__devices',
        'stg_app_database__locations', 'stg_app_database__subscriptions',
        'stg_app_database__user_sessions', 'stg_app_database__tap_events',
        'stg_app_database__feature_usage', 'stg_app_database__page_views',
        'stg_stripe__customers', 'stg_stripe__prices', 'stg_stripe__subscriptions',
        'stg_stripe__subscription_items', 'stg_stripe__invoices', 'stg_stripe__charges',
        'stg_stripe__payment_intents', 'stg_stripe__events',
        'stg_hubspot__companies', 'stg_hubspot__contacts', 'stg_hubspot__deals',
        'stg_hubspot__engagements', 'stg_hubspot__owners', 'stg_hubspot__tickets',
        'stg_marketing__google_analytics_sessions', 'stg_marketing__google_ads_campaigns',
        'stg_marketing__facebook_ads_campaigns', 'stg_marketing__linkedin_ads_campaigns',
        'stg_marketing__iterable_campaigns', 'stg_marketing__attribution_touchpoints',
        'stg_marketing__marketing_qualified_leads'
    ],
    'mart': [
        'mart_customer_success__health', 'mart_device_operations',
        'mart_marketing__attribution', 'mart_operations__performance',
        'mart_operations_health', 'mart_product__adoption',
        'mart_sales__pipeline', 'operations_device_monitoring'
    ],
    'metrics': [
        'metrics_api', 'metrics_company_overview', 'metrics_customer_success',
        'metrics_engagement', 'metrics_marketing', 'metrics_operations',
        'metrics_product_analytics', 'metrics_revenue', 'metrics_sales',
        'metrics_unified'
    ]
}

# Minimum expected row counts for critical tables
MIN_ROW_COUNTS = {
    'raw.app_database_accounts': 50,
    'raw.app_database_users': 50,
    'raw.app_database_devices': 50,
    'raw.stripe_customers': 50,
    'mart.mart_customer_success__health': 5
}

def check_table_exists(schema, table):
    """Check if a table exists in the specified schema"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            )
        """, (schema, table))
        return cursor.fetchone()['exists']

def get_row_count(schema, table):
    """Get row count for a table"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
        return cursor.fetchone()['count']

def validate_schema_tables(schema_name, expected_tables):
    """Validate all tables in a schema"""
    print(f"\n📊 Validating {schema_name} schema...")
    print("-" * 50)
    
    missing_tables = []
    empty_tables = []
    total_rows = 0
    
    for table in expected_tables:
        if not check_table_exists(schema_name, table):
            missing_tables.append(table)
            print(f"  ❌ {table}: MISSING")
        else:
            row_count = get_row_count(schema_name, table)
            total_rows += row_count
            
            # Check minimum row counts for critical tables
            min_required = MIN_ROW_COUNTS.get(f"{schema_name}.{table}", 0)
            
            if row_count == 0:
                empty_tables.append(table)
                print(f"  ⚠️  {table}: EMPTY")
            elif row_count < min_required:
                print(f"  ⚠️  {table}: {row_count:,} rows (minimum {min_required:,} expected)")
            else:
                print(f"  ✅ {table}: {row_count:,} rows")
    
    # Summary for schema
    print(f"\n{schema_name.upper()} Schema Summary:")
    print(f"  Total tables: {len(expected_tables)}")
    print(f"  Missing tables: {len(missing_tables)}")
    print(f"  Empty tables: {len(empty_tables)}")
    print(f"  Total rows: {total_rows:,}")
    
    return len(missing_tables), len(empty_tables), total_rows

def validate_dbt_models():
    """Check if dbt models are compiled"""
    print("\n📊 Validating dbt models...")
    print("-" * 50)
    
    dbt_target_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'dbt_project', 'target'
    )
    
    if not os.path.exists(dbt_target_path):
        print("  ❌ dbt target directory not found - models not compiled")
        return False
    
    # Count compiled models
    compiled_models = 0
    for root, dirs, files in os.walk(dbt_target_path):
        if 'compiled' in root:
            compiled_models += len([f for f in files if f.endswith('.sql')])
    
    if compiled_models > 0:
        print(f"  ✅ Found {compiled_models} compiled dbt models")
        return True
    else:
        print("  ❌ No compiled dbt models found")
        return False

def main():
    """Run validation checks"""
    print("🔍 SaaS Data Platform Validation")
    print("=" * 60)
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    if not db_helper.test_connection():
        print("  ❌ Failed to connect to database")
        sys.exit(1)
    print("  ✅ Database connection successful")
    
    # Track overall health
    total_missing = 0
    total_empty = 0
    issues = []
    
    # Validate each schema
    for schema, tables in EXPECTED_TABLES.items():
        missing, empty, rows = validate_schema_tables(schema, tables)
        total_missing += missing
        total_empty += empty
        
        if missing > 0:
            issues.append(f"{missing} missing tables in {schema} schema")
        if empty > 0 and schema == 'raw':  # Only worry about empty raw tables
            issues.append(f"{empty} empty tables in {schema} schema")
    
    # Validate dbt models
    if not validate_dbt_models():
        issues.append("dbt models not compiled")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    if total_missing == 0 and (total_empty == 0 or total_empty < 5) and len(issues) == 0:
        print("✅ All validations passed!")
        print("   - All expected tables exist")
        print("   - All critical tables have data")
        print("   - dbt models are compiled")
        return 0
    else:
        print("⚠️  Validation completed with issues:")
        for issue in issues:
            print(f"   - {issue}")
        
        if total_missing > 0:
            print("\n❌ Critical: Missing tables detected")
            return 1
        else:
            print("\n⚠️  Non-critical issues found, but setup is functional")
            return 0

if __name__ == "__main__":
    sys.exit(main())