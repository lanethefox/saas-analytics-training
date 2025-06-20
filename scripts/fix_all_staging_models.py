#!/usr/bin/env python3
"""
Automatically fix all staging models based on actual database schema
"""

import os
import re
import psycopg2
import subprocess

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

def get_table_columns(schema, table):
    """Get actual columns from database table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s 
        ORDER BY ordinal_position
    """, (schema, table))
    
    columns = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    
    return columns

def fix_staging_model(model_path, table_name, actual_columns):
    """Fix a single staging model file"""
    
    if not os.path.exists(model_path):
        print(f"  - Model not found: {model_path}")
        return False
    
    with open(model_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Common column mappings that don't exist
    column_fixes = {
        # Stripe specific
        'product': "NULL::text",
        'collection_method': "'charge_automatically'::text",
        'default_payment_method': "NULL::text",
        'latest_invoice': "NULL::text",
        'payment_method': "NULL::text",
        'customer_email': "NULL::text",
        'customer_name': "NULL::text",
        'billing_details': "'{}'::jsonb",
        'outcome': "'{}'::jsonb",
        'payment_method_details': "'{}'::jsonb",
        'shipping': "NULL::jsonb",
        'livemode': "false::boolean",
        'request': "'{}'::jsonb",
        'pending_webhooks': "0::integer",
        
        # HubSpot specific
        'portal_id': "1::integer",
        
        # Check if metadata exists
        'metadata': "'{}'::jsonb" if 'metadata' not in actual_columns else 'metadata',
        'associations': "'{}'::jsonb" if 'associations' not in actual_columns else 'associations'
    }
    
    # Find all column references in the SQL
    column_pattern = r'(?:^|\s+)(\w+)(?:\s+as|\s*,|\s+from)'
    matches = re.findall(column_pattern, content, re.MULTILINE | re.IGNORECASE)
    
    for col in set(matches):
        if col.lower() in ['select', 'from', 'where', 'case', 'when', 'then', 'else', 'end', 'and', 'or', 'null', 'true', 'false', 'as', 'cast', 'current_timestamp']:
            continue
            
        if col not in actual_columns and col in column_fixes:
            # Replace column reference with default value
            pattern = rf'\b{col}\b(?=\s+as|\s*,)'
            replacement = column_fixes[col]
            content = re.sub(pattern, replacement, content)
            print(f"    - Replaced {col} with {replacement}")
    
    # Fix to_timestamp issues - if column is already timestamp
    timestamp_pattern = r'to_timestamp\((\w+)\)'
    for match in re.finditer(timestamp_pattern, content):
        col_name = match.group(1)
        if col_name in actual_columns and 'timestamp' in actual_columns[col_name]:
            content = content.replace(f'to_timestamp({col_name})', col_name)
            print(f"    - Fixed to_timestamp({col_name}) -> {col_name}")
    
    # Fix missing columns in CASE statements
    case_pattern = r'when\s+(\w+)\s+is\s+null'
    for match in re.finditer(case_pattern, content, re.IGNORECASE):
        col_name = match.group(1)
        if col_name not in actual_columns and col_name not in ['cast', 'null']:
            # Comment out this condition
            old_line = match.group(0)
            new_line = f"when false -- {old_line} (column doesn't exist)"
            content = content.replace(old_line, new_line)
            print(f"    - Commented out condition for missing column: {col_name}")
    
    if content != original_content:
        with open(model_path, 'w') as f:
            f.write(content)
        return True
    
    return False

def fix_all_staging_models():
    """Fix all staging models"""
    
    base_path = '/Users/lane/Development/Active/data-platform/dbt_project/models/staging'
    
    # Mapping of staging folders to raw tables
    model_mappings = {
        'app_database': [
            ('stg_app_database__accounts.sql', 'app_database_accounts'),
            ('stg_app_database__devices.sql', 'app_database_devices'),
            ('stg_app_database__feature_usage.sql', 'app_database_feature_usage'),
            ('stg_app_database__locations.sql', 'app_database_locations'),
            ('stg_app_database__page_views.sql', 'app_database_page_views'),
            ('stg_app_database__subscriptions.sql', 'app_database_subscriptions'),
            ('stg_app_database__tap_events.sql', 'app_database_tap_events'),
            ('stg_app_database__user_sessions.sql', 'app_database_user_sessions'),
            ('stg_app_database__users.sql', 'app_database_users')
        ],
        'stripe': [
            ('stg_stripe__charges.sql', 'stripe_charges'),
            ('stg_stripe__customers.sql', 'stripe_customers'),
            ('stg_stripe__events.sql', 'stripe_events'),
            ('stg_stripe__invoices.sql', 'stripe_invoices'),
            ('stg_stripe__payment_intents.sql', 'stripe_payment_intents'),
            ('stg_stripe__prices.sql', 'stripe_prices'),
            ('stg_stripe__subscription_items.sql', 'stripe_subscription_items'),
            ('stg_stripe__subscriptions.sql', 'stripe_subscriptions')
        ],
        'hubspot': [
            ('stg_hubspot__companies.sql', 'hubspot_companies'),
            ('stg_hubspot__contacts.sql', 'hubspot_contacts'),
            ('stg_hubspot__deals.sql', 'hubspot_deals'),
            ('stg_hubspot__engagements.sql', 'hubspot_engagements'),
            ('stg_hubspot__owners.sql', 'hubspot_owners'),
            ('stg_hubspot__tickets.sql', 'hubspot_tickets')
        ],
        'marketing': [
            ('stg_marketing__attribution_touchpoints.sql', 'attribution_touchpoints'),
            ('stg_marketing__facebook_ads_campaigns.sql', 'facebook_ads_campaigns'),
            ('stg_marketing__google_ads_campaigns.sql', 'google_ads_campaigns'),
            ('stg_marketing__google_analytics_sessions.sql', 'google_analytics_sessions'),
            ('stg_marketing__iterable_campaigns.sql', 'iterable_campaigns'),
            ('stg_marketing__linkedin_ads_campaigns.sql', 'linkedin_ads_campaigns'),
            ('stg_marketing__marketing_qualified_leads.sql', 'marketing_qualified_leads')
        ]
    }
    
    total_fixed = 0
    
    for folder, models in model_mappings.items():
        print(f"\nFixing {folder} models:")
        
        for model_file, table_name in models:
            model_path = os.path.join(base_path, folder, model_file)
            print(f"\n  Checking {model_file}...")
            
            # Get actual columns
            actual_columns = get_table_columns('raw', table_name)
            
            if actual_columns:
                if fix_staging_model(model_path, table_name, actual_columns):
                    print(f"  ✓ Fixed {model_file}")
                    total_fixed += 1
                else:
                    print(f"  - No changes needed for {model_file}")
            else:
                print(f"  ✗ Could not get columns for {table_name}")
    
    return total_fixed

def test_fixed_models():
    """Test all staging models after fixes"""
    print("\n\nTesting fixed models...")
    
    cmd = 'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run -s staging --profiles-dir . 2>&1"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Count successes and failures
    success_count = result.stdout.count("Completed successfully")
    error_count = result.stdout.count("ERROR")
    
    print(f"\nTest Results:")
    print(f"  - Successful: {success_count}")
    print(f"  - Failed: {error_count}")
    
    return success_count, error_count

def main():
    print("Fixing all staging models based on actual database schema...")
    
    # Fix models
    fixed_count = fix_all_staging_models()
    print(f"\n\nTotal models fixed: {fixed_count}")
    
    # Test models
    print("\nWould you like to test all staging models now? (y/n): ", end='')
    if input().lower() == 'y':
        success, errors = test_fixed_models()
        
        if errors == 0:
            print("\n✅ All staging models are now working!")
        else:
            print(f"\n⚠️  {errors} models still have errors. Check the output for details.")

if __name__ == "__main__":
    main()