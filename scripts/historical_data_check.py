#!/usr/bin/env python3
"""
Check historical data presence across key entity and metrics tables
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.database_config import db_helper

def check_historical_table(table_name, date_column, entity_column=None):
    """Check a single historical table"""
    try:
        with db_helper.config.get_cursor(dict_cursor=True) as cursor:
            if entity_column:
                query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        COUNT(DISTINCT {entity_column}) as unique_entities,
                        MIN({date_column})::date as min_date,
                        MAX({date_column})::date as max_date,
                        COUNT(DISTINCT {date_column}::date) as unique_dates
                    FROM {table_name}
                """
            else:
                query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        MIN({date_column})::date as min_date,
                        MAX({date_column})::date as max_date,
                        COUNT(DISTINCT {date_column}::date) as unique_dates
                    FROM {table_name}
                """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result['row_count'] > 0:
                days_span = (result['max_date'] - result['min_date']).days if result['min_date'] else 0
                return {
                    'exists': True,
                    'row_count': result['row_count'],
                    'unique_entities': result.get('unique_entities'),
                    'min_date': result['min_date'],
                    'max_date': result['max_date'],
                    'unique_dates': result['unique_dates'],
                    'days_span': days_span
                }
            else:
                return {'exists': True, 'row_count': 0}
    except Exception as e:
        return {'exists': False, 'error': str(e)}

def main():
    print("\n" + "="*100)
    print("📊 HISTORICAL DATA ANALYSIS")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # Define key historical tables to check with correct column names
    historical_tables = [
        # Entity daily/weekly/monthly tables
        ('entity.entity_customers_daily', 'snapshot_date', 'account_id'),
        ('entity.entity_customers_history', 'snapshot_date', 'account_id'),
        ('entity.entity_subscriptions_history', 'snapshot_date', 'subscription_id'),
        ('entity.entity_subscriptions_monthly', 'month_start_date', 'subscription_id'),
        ('entity.entity_devices_history', 'snapshot_date', 'device_id'),
        ('entity.entity_devices_hourly', 'event_hour', 'device_id'),
        ('entity.entity_locations_history', 'snapshot_date', 'location_id'),
        ('entity.entity_locations_weekly', 'week_start_date', 'location_id'),
        ('entity.entity_users_history', 'snapshot_date', 'user_id'),
        ('entity.entity_users_weekly', 'week_start_date', 'user_id'),
        ('entity.entity_features_history', 'snapshot_date', 'feature_name'),
        ('entity.entity_features_monthly', 'month_start_date', 'feature_name'),
        
        # Intermediate fact tables
        ('intermediate.fct_customer_history', 'date', 'account_id'),
        ('intermediate.fct_device_history', 'event_timestamp', 'device_id'),
        ('intermediate.fct_subscription_history', 'date', 'subscription_id'),
        
        # Metrics tables
        ('metrics.metrics_revenue_daily', 'metric_date', None),
        ('metrics.metrics_revenue_historical', 'month', None),
        ('metrics.metrics_customer_historical', 'report_month', None),
        ('metrics.metrics_operations_daily', 'report_date', None),
    ]
    
    print(f"\n{'Table':<50} {'Rows':>10} {'Entities':>10} {'Date Range':<25} {'Days':>6} {'Dates':>6}")
    print("-"*110)
    
    total_historical_rows = 0
    tables_with_data = 0
    
    for table_name, date_col, entity_col in historical_tables:
        result = check_historical_table(table_name, date_col, entity_col)
        
        if result['exists'] and 'error' not in result:
            row_count = result['row_count']
            total_historical_rows += row_count
            
            if row_count > 0:
                tables_with_data += 1
                entities = str(result['unique_entities']) if result.get('unique_entities') else "N/A"
                date_range = f"{result['min_date']} to {result['max_date']}"
                print(f"{table_name:<50} {row_count:>10,} {entities:>10} {date_range:<25} {result['days_span']:>6} {result['unique_dates']:>6}")
            else:
                print(f"{table_name:<50} {'0':>10} {'N/A':>10} {'No data':<25} {'0':>6} {'0':>6}")
        else:
            error_msg = result.get('error', 'Table not found')[:30]
            print(f"{table_name:<50} {'ERROR':>10} {error_msg}")
    
    print("-"*110)
    print(f"\n📊 Summary:")
    print(f"   - Tables with historical data: {tables_with_data}/{len(historical_tables)}")
    print(f"   - Total historical records: {total_historical_rows:,}")
    
    # Check specific metrics
    print("\n📈 Key Metrics Check:")
    
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Check revenue metrics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT metric_date) as days_with_data,
                MIN(metric_date) as earliest_date,
                MAX(metric_date) as latest_date,
                SUM(new_mrr) as total_new_mrr,
                SUM(churned_mrr) as total_churned_mrr
            FROM metrics.metrics_revenue_daily
        """)
        revenue = cursor.fetchone()
        
        if revenue['days_with_data'] > 0:
            print(f"\n   Revenue Metrics:")
            print(f"   - Days with data: {revenue['days_with_data']}")
            print(f"   - Date range: {revenue['earliest_date']} to {revenue['latest_date']}")
            print(f"   - Total new MRR: ${revenue['total_new_mrr']:,.2f}")
            print(f"   - Total churned MRR: ${revenue['total_churned_mrr']:,.2f}")
        
        # Check current MRR
        cursor.execute("""
            SELECT 
                total_mrr,
                active_customers,
                total_subscriptions
            FROM metrics.metrics_revenue_summary
            LIMIT 1
        """)
        current = cursor.fetchone()
        
        if current:
            print(f"\n   Current State:")
            print(f"   - Active MRR: ${current['total_mrr']:,.2f}")
            print(f"   - Active customers: {current['active_customers']:,}")
            print(f"   - Total subscriptions: {current['total_subscriptions']:,}")
    
    print("\n✅ Historical data analysis complete!")

if __name__ == "__main__":
    main()