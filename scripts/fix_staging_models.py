#!/usr/bin/env python3
"""
Fix common issues in staging models based on actual schema
"""

import subprocess
import psycopg2
import re
import os

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

def fix_stripe_models():
    """Fix Stripe staging models based on actual schema"""
    
    # Get actual columns for each stripe table
    stripe_tables = {
        'stripe_prices': get_table_columns('raw', 'stripe_prices'),
        'stripe_customers': get_table_columns('raw', 'stripe_customers'),
        'stripe_subscriptions': get_table_columns('raw', 'stripe_subscriptions'),
        'stripe_invoices': get_table_columns('raw', 'stripe_invoices'),
        'stripe_charges': get_table_columns('raw', 'stripe_charges'),
        'stripe_events': get_table_columns('raw', 'stripe_events'),
        'stripe_subscription_items': get_table_columns('raw', 'stripe_subscription_items'),
        'stripe_payment_intents': get_table_columns('raw', 'stripe_payment_intents')
    }
    
    print("Stripe table schemas:")
    for table, columns in stripe_tables.items():
        print(f"\n{table}:")
        for col, dtype in columns.items():
            print(f"  - {col}: {dtype}")
    
    # Common missing columns in Stripe models
    missing_columns = {
        'product': "NULL::text",
        'metadata': "'{}'::jsonb",
        'collection_method': "'charge_automatically'::text",
        'default_payment_method': "NULL::text",
        'latest_invoice': "NULL::text",
        'payment_method': "NULL::text",
        'description': "NULL::text",
        'invoice': "NULL::text",
        'customer_email': "NULL::text",
        'customer_name': "NULL::text",
        'billing_details': "'{}'::jsonb",
        'outcome': "'{}'::jsonb",
        'payment_method_details': "'{}'::jsonb",
        'shipping': "NULL::jsonb",
        'livemode': "false::boolean",
        'request': "'{}'::jsonb",
        'pending_webhooks': "0::integer"
    }
    
    return missing_columns

def fix_hubspot_models():
    """Fix HubSpot staging models"""
    
    # Get actual columns
    hubspot_tables = {
        'hubspot_companies': get_table_columns('raw', 'hubspot_companies'),
        'hubspot_contacts': get_table_columns('raw', 'hubspot_contacts'),
        'hubspot_deals': get_table_columns('raw', 'hubspot_deals'),
        'hubspot_engagements': get_table_columns('raw', 'hubspot_engagements'),
        'hubspot_tickets': get_table_columns('raw', 'hubspot_tickets'),
        'hubspot_owners': get_table_columns('raw', 'hubspot_owners')
    }
    
    print("\n\nHubSpot table schemas:")
    for table, columns in hubspot_tables.items():
        print(f"\n{table}:")
        for col, dtype in columns.items():
            print(f"  - {col}: {dtype}")
    
    # Common missing columns in HubSpot models
    missing_columns = {
        'metadata': "'{}'::jsonb",
        'associations': "'{}'::jsonb",
        'portal_id': "1::integer",
        'property_*': "NULL::text"  # Many property columns might be missing
    }
    
    return missing_columns

def fix_marketing_models():
    """Fix Marketing staging models"""
    
    # Get actual columns
    marketing_tables = {
        'google_ads_campaigns': get_table_columns('raw', 'google_ads_campaigns'),
        'facebook_ads_campaigns': get_table_columns('raw', 'facebook_ads_campaigns'),
        'linkedin_ads_campaigns': get_table_columns('raw', 'linkedin_ads_campaigns'),
        'iterable_campaigns': get_table_columns('raw', 'iterable_campaigns'),
        'attribution_touchpoints': get_table_columns('raw', 'attribution_touchpoints'),
        'marketing_qualified_leads': get_table_columns('raw', 'marketing_qualified_leads'),
        'google_analytics_sessions': get_table_columns('raw', 'google_analytics_sessions')
    }
    
    print("\n\nMarketing table schemas:")
    for table, columns in marketing_tables.items():
        print(f"\n{table}:")
        for col, dtype in columns.items():
            print(f"  - {col}: {dtype}")
    
    return {}

def main():
    print("Analyzing staging model issues...\n")
    
    # Check each category
    stripe_fixes = fix_stripe_models()
    hubspot_fixes = fix_hubspot_models()
    marketing_fixes = fix_marketing_models()
    
    print("\n\nSummary of fixes needed:")
    print("\nStripe models - common missing columns:")
    for col, default in stripe_fixes.items():
        print(f"  - {col}: {default}")
    
    print("\nHubSpot models - common missing columns:")
    for col, default in hubspot_fixes.items():
        print(f"  - {col}: {default}")
    
    print("\n\nNext steps:")
    print("1. Update staging models to handle missing columns with NULL or default values")
    print("2. Remove references to columns that don't exist in raw tables")
    print("3. Fix data type conversions (e.g., to_timestamp on timestamp columns)")
    print("4. Run models individually to test fixes")

if __name__ == "__main__":
    main()