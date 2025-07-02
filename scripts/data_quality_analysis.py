#!/usr/bin/env python3
"""
Comprehensive Data Quality Analysis Script

This script performs a full row count and data quality analysis across all schemas,
checking for:
- Row counts per table
- Historical data presence
- Date ranges for time-series data
- Data completeness
- Referential integrity
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.database_config import db_helper

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"📊 {title}")
    print(f"{'='*80}")

def get_table_stats():
    """Get row counts and sizes for all tables"""
    results = []
    
    # Get list of tables first
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('raw', 'staging', 'intermediate', 'entity', 'mart', 'metrics')
                AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
        """)
        tables = cursor.fetchall()
    
    # Get row count for each table individually
    for table in tables:
        with db_helper.config.get_cursor(dict_cursor=True) as cursor:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as row_count 
                    FROM {table['table_schema']}.{table['table_name']}
                """)
                row_count = cursor.fetchone()['row_count']
                results.append({
                    'table_schema': table['table_schema'],
                    'table_name': table['table_name'],
                    'row_count': row_count
                })
            except Exception as e:
                results.append({
                    'table_schema': table['table_schema'],
                    'table_name': table['table_name'],
                    'row_count': -1  # Error indicator
                })
    
    return results

def analyze_historical_data():
    """Analyze historical data presence in key tables"""
    historical_tables = {
        'entity.entity_subscriptions_history': {
            'date_column': 'event_date',
            'entity': 'subscription_id'
        },
        'entity.entity_subscriptions_monthly': {
            'date_column': 'month_start',
            'entity': 'subscription_id'
        },
        'entity.entity_accounts_daily': {
            'date_column': 'date',
            'entity': 'account_id'
        },
        'entity.entity_accounts_monthly': {
            'date_column': 'month_start',
            'entity': 'account_id'
        },
        'entity.entity_users_daily': {
            'date_column': 'date',
            'entity': 'user_id'
        },
        'entity.entity_users_weekly': {
            'date_column': 'week_start',
            'entity': 'user_id'
        },
        'entity.entity_devices_daily': {
            'date_column': 'date',
            'entity': 'device_id'
        },
        'entity.entity_locations_daily': {
            'date_column': 'date',
            'entity': 'location_id'
        },
        'metrics.metrics_revenue_daily': {
            'date_column': 'date',
            'entity': None
        },
        'metrics.metrics_revenue_historical': {
            'date_column': 'month',
            'entity': None
        }
    }
    
    results = {}
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        for table, config in historical_tables.items():
            schema, table_name = table.split('.')
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                )
            """, (schema, table_name))
            
            if not cursor.fetchone()['exists']:
                results[table] = {'exists': False}
                continue
            
            # Get date range and row count
            date_col = config['date_column']
            entity_col = config['entity']
            
            if entity_col:
                query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        COUNT(DISTINCT {entity_col}) as unique_entities,
                        MIN({date_col})::date as min_date,
                        MAX({date_col})::date as max_date,
                        COUNT(DISTINCT {date_col}) as unique_dates
                    FROM {table}
                """
            else:
                query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        NULL as unique_entities,
                        MIN({date_col})::date as min_date,
                        MAX({date_col})::date as max_date,
                        COUNT(DISTINCT {date_col}) as unique_dates
                    FROM {table}
                """
            
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                results[table] = {
                    'exists': True,
                    'row_count': result['row_count'],
                    'unique_entities': result['unique_entities'],
                    'min_date': result['min_date'],
                    'max_date': result['max_date'],
                    'unique_dates': result['unique_dates'],
                    'date_range_days': (result['max_date'] - result['min_date']).days if result['min_date'] and result['max_date'] else 0
                }
            except Exception as e:
                results[table] = {'exists': True, 'error': str(e)}
    
    return results

def check_data_quality_metrics():
    """Check key data quality metrics"""
    metrics = {}
    
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Check for orphaned records
        checks = [
            {
                'name': 'Devices without valid locations',
                'query': """
                    SELECT COUNT(*) as count
                    FROM raw.app_database_devices d
                    LEFT JOIN raw.app_database_locations l ON d.location_id = l.id
                    WHERE l.id IS NULL
                """
            },
            {
                'name': 'Locations without valid accounts',
                'query': """
                    SELECT COUNT(*) as count
                    FROM raw.app_database_locations l
                    LEFT JOIN raw.app_database_accounts a ON l.customer_id = a.id
                    WHERE a.id IS NULL
                """
            },
            {
                'name': 'Subscriptions without valid accounts',
                'query': """
                    SELECT COUNT(*) as count
                    FROM raw.app_database_subscriptions s
                    LEFT JOIN raw.app_database_accounts a ON s.customer_id = a.id
                    WHERE a.id IS NULL
                """
            },
            {
                'name': 'Active subscriptions',
                'query': """
                    SELECT COUNT(*) as count
                    FROM raw.app_database_subscriptions
                    WHERE status = 'active'
                """
            },
            {
                'name': 'Accounts with subscriptions',
                'query': """
                    SELECT COUNT(DISTINCT customer_id) as count
                    FROM raw.app_database_subscriptions
                """
            },
            {
                'name': 'Feature usage events in last 30 days',
                'query': """
                    SELECT COUNT(*) as count
                    FROM raw.app_database_feature_usage
                    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
                """
            }
        ]
        
        for check in checks:
            cursor.execute(check['query'])
            metrics[check['name']] = cursor.fetchone()['count']
    
    return metrics

def analyze_metrics_completeness():
    """Check if metrics tables have complete data"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Get all metrics tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'metrics'
            ORDER BY table_name
        """)
        
        metrics_analysis = {}
        for row in cursor.fetchall():
            table = f"metrics.{row['table_name']}"
            
            # Get row count and check for key metrics
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            
            metrics_analysis[table] = {'row_count': count}
            
            # For summary tables, check key metrics
            if 'summary' in table or 'unified' in table:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'metrics' 
                        AND table_name = %s
                        AND column_name IN ('total_mrr', 'active_customers', 'total_customers', 'mrr', 'arr')
                """, (row['table_name'],))
                
                metric_columns = [col['column_name'] for col in cursor.fetchall()]
                if metric_columns and count > 0:
                    # Get latest values
                    cols = ', '.join(metric_columns)
                    cursor.execute(f"SELECT {cols} FROM {table} LIMIT 1")
                    latest_values = cursor.fetchone()
                    metrics_analysis[table]['latest_metrics'] = latest_values
        
        return metrics_analysis

def main():
    """Main analysis function"""
    print("="*80)
    print("🔍 COMPREHENSIVE DATA QUALITY ANALYSIS")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. Table inventory and row counts
    print_section("Table Inventory and Row Counts")
    table_stats = get_table_stats()
    
    schema_totals = defaultdict(lambda: {'tables': 0, 'rows': 0})
    
    print(f"\n{'Schema':<15} {'Table':<40} {'Row Count':>12}")
    print("-"*70)
    
    for stat in table_stats:
        schema = stat['table_schema']
        table = stat['table_name']
        rows = stat['row_count']
        
        schema_totals[schema]['tables'] += 1
        schema_totals[schema]['rows'] += rows
        
        print(f"{schema:<15} {table:<40} {rows:>12,}")
    
    print("\n" + "="*70)
    print("Schema Summary:")
    print("-"*70)
    
    total_tables = 0
    total_rows = 0
    for schema, totals in sorted(schema_totals.items()):
        print(f"{schema:<15} {totals['tables']:>3} tables {totals['rows']:>15,} rows")
        total_tables += totals['tables']
        total_rows += totals['rows']
    
    print("-"*70)
    print(f"{'TOTAL':<15} {total_tables:>3} tables {total_rows:>15,} rows")
    
    # 2. Historical data analysis
    print_section("Historical Data Analysis")
    historical_data = analyze_historical_data()
    
    print(f"\n{'Table':<45} {'Rows':>10} {'Entities':>10} {'Date Range':<25} {'Days':>6}")
    print("-"*100)
    
    for table, data in sorted(historical_data.items()):
        if not data['exists']:
            print(f"{table:<45} {'NOT FOUND':>10}")
        elif 'error' in data:
            print(f"{table:<45} {'ERROR: ' + data['error'][:30]}")
        else:
            date_range = f"{data['min_date']} to {data['max_date']}" if data['min_date'] else "No dates"
            entities = str(data['unique_entities']) if data['unique_entities'] else "N/A"
            print(f"{table:<45} {data['row_count']:>10,} {entities:>10} {date_range:<25} {data['date_range_days']:>6}")
    
    # 3. Data quality checks
    print_section("Data Quality Metrics")
    quality_metrics = check_data_quality_metrics()
    
    for metric, value in quality_metrics.items():
        status = "✅" if (metric.startswith("Active") or metric.startswith("Accounts")) and value > 0 else "✅" if value == 0 else "⚠️"
        print(f"{status} {metric:<50}: {value:>10,}")
    
    # 4. Metrics completeness
    print_section("Metrics Tables Analysis")
    metrics_data = analyze_metrics_completeness()
    
    for table, data in sorted(metrics_data.items()):
        print(f"\n{table}: {data['row_count']} rows")
        if 'latest_metrics' in data:
            print("  Latest values:")
            for col, val in data['latest_metrics'].items():
                if isinstance(val, (int, float)):
                    print(f"    - {col}: ${val:,.2f}" if 'mrr' in col or 'arr' in col else f"    - {col}: {val:,}")
                else:
                    print(f"    - {col}: {val}")
    
    # 5. Summary
    print_section("Analysis Summary")
    
    # Calculate summary statistics
    has_historical = sum(1 for d in historical_data.values() if d.get('row_count', 0) > 0)
    total_historical_rows = sum(d.get('row_count', 0) for d in historical_data.values() if 'row_count' in d)
    
    print(f"\n✅ Total tables analyzed: {len(table_stats)}")
    print(f"✅ Total rows in database: {total_rows:,}")
    print(f"✅ Historical tables with data: {has_historical}/{len(historical_data)}")
    print(f"✅ Total historical records: {total_historical_rows:,}")
    
    # Check for MRR
    if 'Active subscriptions' in quality_metrics and quality_metrics['Active subscriptions'] > 0:
        print(f"\n💰 Active subscriptions: {quality_metrics['Active subscriptions']}")
    
    print("\n🎉 Data quality analysis complete!")

if __name__ == "__main__":
    main()