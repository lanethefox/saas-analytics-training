#!/usr/bin/env python3
"""
Verify all generated data in PostgreSQL database
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

def verify_table_data(table_name, sample_query=None, show_sample=True):
    """Verify data in a specific table"""
    print(f"\n{'='*60}")
    print(f"Table: raw.{table_name}")
    print('='*60)
    
    # Get row count
    count = db_helper.get_row_count(table_name)
    print(f"Total rows: {count:,}")
    
    if count > 0 and show_sample:
        # Show sample data
        with db_helper.config.get_cursor(dict_cursor=True) as cursor:
            if sample_query:
                cursor.execute(sample_query)
            else:
                cursor.execute(f"""
                    SELECT * FROM raw.{table_name} 
                    LIMIT 5
                """)
            samples = cursor.fetchall()
            
            if samples:
                print(f"\nSample data (showing {len(samples)} rows):")
                for i, row in enumerate(samples, 1):
                    print(f"\nRow {i}:")
                    for key, value in row.items():
                        if value is not None:
                            if isinstance(value, (dict, list)):
                                print(f"  {key}: {json.dumps(value, indent=2)}")
                            elif isinstance(value, datetime):
                                print(f"  {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
                            else:
                                print(f"  {key}: {value}")
    
    return count

def main():
    """Main verification function"""
    print("=" * 80)
    print("POSTGRESQL DATA VERIFICATION REPORT")
    print("=" * 80)
    print(f"Database: {db_helper.config.db_name}")
    print(f"Host: {db_helper.config.db_host}:{db_helper.config.db_port}")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("\n❌ Failed to connect to database!")
        return
    
    # Core entity tables
    print("\n" + "="*80)
    print("CORE ENTITIES")
    print("="*80)
    
    tables_to_verify = [
        {
            'name': 'app_database_accounts',
            'query': """
                SELECT a.*, 
                       (SELECT COUNT(*) FROM raw.app_database_locations l WHERE l.customer_id = a.id) as location_count_actual,
                       (SELECT COUNT(*) FROM raw.app_database_users u WHERE u.customer_id = a.id) as user_count
                FROM raw.app_database_accounts a
                ORDER BY a.created_at DESC
                LIMIT 5
            """
        },
        {
            'name': 'app_database_locations',
            'query': """
                SELECT l.*, a.name as account_name
                FROM raw.app_database_locations l
                JOIN raw.app_database_accounts a ON l.customer_id = a.id
                ORDER BY l.created_at DESC
                LIMIT 5
            """
        },
        {
            'name': 'app_database_users',
            'query': """
                SELECT u.*, a.name as account_name
                FROM raw.app_database_users u
                JOIN raw.app_database_accounts a ON u.customer_id = a.id
                ORDER BY u.created_at DESC
                LIMIT 5
            """
        },
        {
            'name': 'app_database_devices',
            'query': """
                SELECT d.*, l.name as location_name
                FROM raw.app_database_devices d
                JOIN raw.app_database_locations l ON d.location_id = l.id
                ORDER BY d.created_at DESC
                LIMIT 5
            """
        },
        {
            'name': 'app_database_subscriptions',
            'query': """
                SELECT s.*, a.name as account_name
                FROM raw.app_database_subscriptions s
                JOIN raw.app_database_accounts a ON s.customer_id = a.id
                ORDER BY s.created_at DESC
                LIMIT 5
            """
        }
    ]
    
    core_totals = {}
    for table_info in tables_to_verify:
        count = verify_table_data(table_info['name'], table_info.get('query'))
        core_totals[table_info['name']] = count
    
    # Stripe tables
    print("\n" + "="*80)
    print("STRIPE BILLING DATA")
    print("="*80)
    
    stripe_tables = [
        'stripe_customers',
        'stripe_prices'
    ]
    
    stripe_totals = {}
    for table in stripe_tables:
        count = verify_table_data(table)
        stripe_totals[table] = count
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\nCore Entities:")
    for table, count in core_totals.items():
        print(f"  {table}: {count:,} records")
    
    print("\nStripe Billing:")
    for table, count in stripe_totals.items():
        print(f"  {table}: {count:,} records")
    
    # Business metrics
    print("\n" + "="*80)
    print("BUSINESS METRICS")
    print("="*80)
    
    with db_helper.config.get_cursor() as cursor:
        # Active subscriptions and MRR
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'active') as active_subs,
                COUNT(*) FILTER (WHERE status = 'canceled') as canceled_subs,
                SUM(monthly_price) FILTER (WHERE status = 'active') as total_mrr
            FROM raw.app_database_subscriptions
        """)
        sub_metrics = cursor.fetchone()
        print(f"\nSubscriptions:")
        print(f"  Active: {sub_metrics[0]:,}")
        print(f"  Canceled: {sub_metrics[1]:,}")
        print(f"  Total MRR: ${sub_metrics[2]:,.2f}" if sub_metrics[2] else "  Total MRR: $0.00")
        
        # User distribution by role
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM raw.app_database_users
            GROUP BY role
            ORDER BY count DESC
        """)
        print(f"\nUsers by Role:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,}")
        
        # Device status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM raw.app_database_devices
            GROUP BY status
            ORDER BY count DESC
        """)
        print(f"\nDevices by Status:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,}")
        
        # Account distribution by business type
        cursor.execute("""
            SELECT business_type, COUNT(*) as count
            FROM raw.app_database_accounts
            GROUP BY business_type
            ORDER BY count DESC
        """)
        print(f"\nAccounts by Business Type:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,}")
    
    print("\n" + "="*80)
    print("✅ Data verification complete!")
    print("="*80)

if __name__ == "__main__":
    main()
