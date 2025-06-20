#!/usr/bin/env python3
"""
Data Quality and Business Analytics Validation Script

This script performs comprehensive validation of the generated data including:
- Record counts and completeness
- Referential integrity checks
- Business metric validation
- Time series consistency
- Distribution analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from decimal import Decimal
from scripts.database_config import db_helper

def format_number(num):
    """Format numbers with commas."""
    if isinstance(num, (int, float)):
        return f"{num:,}"
    return str(num)

def check_record_counts():
    """Check record counts across all tables."""
    print("\n" + "="*80)
    print("RECORD COUNTS BY TABLE")
    print("="*80)
    
    table_groups = {
        'Core Entities': [
            'app_database_accounts',
            'app_database_locations', 
            'app_database_users',
            'app_database_devices',
            'app_database_subscriptions'
        ],
        'Stripe Billing': [
            'stripe_customers',
            'stripe_prices',
            'stripe_subscriptions',
            'stripe_subscription_items',
            'stripe_invoices',
            'stripe_charges',
            'stripe_events'
        ],
        'HubSpot CRM': [
            'hubspot_companies',
            'hubspot_contacts',
            'hubspot_deals',
            'hubspot_engagements',
            'hubspot_tickets'
        ],
        'Marketing': [
            'google_ads_campaigns',
            'facebook_ads_campaigns',
            'linkedin_ads_campaigns',
            'iterable_campaigns',
            'attribution_touchpoints',
            'marketing_qualified_leads',
            'google_analytics_sessions'
        ]
    }
    
    total_records = 0
    
    for group_name, tables in table_groups.items():
        print(f"\n{group_name}:")
        group_total = 0
        
        for table in tables:
            count = db_helper.get_row_count(table, 'raw')
            total_records += count
            group_total += count
            print(f"  - {table}: {format_number(count)}")
        
        print(f"  Subtotal: {format_number(group_total)}")
    
    print(f"\n{'='*40}")
    print(f"TOTAL RECORDS: {format_number(total_records)}")
    print(f"{'='*40}")

def check_referential_integrity():
    """Check key relationships between tables."""
    print("\n" + "="*80)
    print("REFERENTIAL INTEGRITY CHECKS")
    print("="*80)
    
    checks = [
        {
            'name': 'Locations per Account',
            'query': """
                SELECT COUNT(DISTINCT customer_id) as accounts_with_locations,
                       COUNT(*) as total_locations,
                       ROUND(COUNT(*)::numeric / COUNT(DISTINCT customer_id), 2) as avg_locations_per_account
                FROM raw.app_database_locations
            """
        },
        {
            'name': 'Users per Account',
            'query': """
                SELECT COUNT(DISTINCT customer_id) as accounts_with_users,
                       COUNT(*) as total_users,
                       ROUND(COUNT(*)::numeric / COUNT(DISTINCT customer_id), 2) as avg_users_per_account
                FROM raw.app_database_users
            """
        },
        {
            'name': 'Devices per Location',
            'query': """
                SELECT COUNT(DISTINCT location_id) as locations_with_devices,
                       COUNT(*) as total_devices,
                       ROUND(COUNT(*)::numeric / COUNT(DISTINCT location_id), 2) as avg_devices_per_location
                FROM raw.app_database_devices
            """
        },
        {
            'name': 'Stripe Customer Coverage',
            'query': """
                SELECT 
                    (SELECT COUNT(*) FROM raw.app_database_accounts) as total_accounts,
                    (SELECT COUNT(*) FROM raw.stripe_customers) as stripe_customers,
                    CASE 
                        WHEN (SELECT COUNT(*) FROM raw.app_database_accounts) > 0
                        THEN ROUND(100.0 * (SELECT COUNT(*) FROM raw.stripe_customers) / 
                                 (SELECT COUNT(*) FROM raw.app_database_accounts), 2)
                        ELSE 0
                    END as coverage_percentage
            """
        },
        {
            'name': 'HubSpot Deal Conversion',
            'query': """
                SELECT 
                    COUNT(*) as total_deals,
                    SUM(CASE WHEN dealstage = 'closedwon' THEN 1 ELSE 0 END) as won_deals,
                    ROUND(100.0 * SUM(CASE WHEN dealstage = 'closedwon' THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate
                FROM raw.hubspot_deals
            """
        }
    ]
    
    with db_helper.config.get_cursor() as cursor:
        for check in checks:
            print(f"\n{check['name']}:")
            cursor.execute(check['query'])
            result = cursor.fetchone()
            
            # Format output based on column names
            cursor.execute(check['query'])
            columns = [desc[0] for desc in cursor.description]
            
            for i, col in enumerate(columns):
                value = result[i]
                if isinstance(value, Decimal):
                    value = float(value)
                print(f"  - {col.replace('_', ' ').title()}: {format_number(value)}")

def check_business_metrics():
    """Validate key business metrics."""
    print("\n" + "="*80)
    print("BUSINESS METRICS VALIDATION")
    print("="*80)
    
    metrics = [
        {
            'name': 'Revenue Metrics',
            'query': """
                SELECT 
                    SUM(monthly_recurring_revenue) as total_mrr,
                    AVG(monthly_recurring_revenue) as avg_mrr,
                    MIN(monthly_recurring_revenue) as min_mrr,
                    MAX(monthly_recurring_revenue) as max_mrr
                FROM raw.app_database_accounts
                WHERE is_active = true
            """
        },
        {
            'name': 'Subscription Distribution',
            'query': """
                SELECT 
                    subscription_tier,
                    COUNT(*) as count,
                    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM raw.app_database_accounts
                GROUP BY subscription_tier
                ORDER BY count DESC
            """
        },
        {
            'name': 'Marketing Campaign Performance',
            'query': """
                WITH campaign_totals AS (
                    SELECT 'Google Ads' as platform,
                           SUM(impressions) as impressions,
                           SUM(clicks) as clicks,
                           SUM(cost) as spend,
                           SUM(conversions) as conversions
                    FROM raw.google_ads_campaigns
                    
                    UNION ALL
                    
                    SELECT 'Facebook Ads' as platform,
                           SUM(impressions) as impressions,
                           SUM(clicks) as clicks,
                           SUM(spend) as spend,
                           0 as conversions
                    FROM raw.facebook_ads_campaigns
                    
                    UNION ALL
                    
                    SELECT 'LinkedIn Ads' as platform,
                           SUM(impressions) as impressions,
                           SUM(clicks) as clicks,
                           SUM(cost) as spend,
                           SUM(conversions) as conversions
                    FROM raw.linkedin_ads_campaigns
                )
                SELECT 
                    platform,
                    impressions,
                    clicks,
                    ROUND(100.0 * clicks / NULLIF(impressions, 0), 2) as ctr_percentage,
                    ROUND(spend::numeric, 2) as total_spend,
                    ROUND(spend::numeric / NULLIF(clicks, 0), 2) as avg_cpc
                FROM campaign_totals
                ORDER BY total_spend DESC
            """
        },
        {
            'name': 'Device Health Status',
            'query': """
                SELECT 
                    status,
                    COUNT(*) as device_count,
                    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM raw.app_database_devices
                GROUP BY status
                ORDER BY device_count DESC
            """
        },
        {
            'name': 'Support Ticket Analysis',
            'query': """
                SELECT 
                    hs_ticket_priority as priority,
                    COUNT(*) as ticket_count,
                    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
                    SUM(CASE WHEN hs_pipeline_stage = 'closed' THEN 1 ELSE 0 END) as closed_tickets,
                    ROUND(100.0 * SUM(CASE WHEN hs_pipeline_stage = 'closed' THEN 1 ELSE 0 END) / COUNT(*), 2) as close_rate
                FROM raw.hubspot_tickets
                GROUP BY hs_ticket_priority
                ORDER BY 
                    CASE hs_ticket_priority 
                        WHEN 'HIGH' THEN 1 
                        WHEN 'MEDIUM' THEN 2 
                        WHEN 'LOW' THEN 3 
                    END
            """
        }
    ]
    
    with db_helper.config.get_cursor() as cursor:
        for metric in metrics:
            print(f"\n{metric['name']}:")
            cursor.execute(metric['query'])
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # For multi-row results
            if 'GROUP BY' in metric['query'] or 'UNION' in metric['query']:
                rows = cursor.fetchall()
                if rows:
                    # Print header
                    header = " | ".join(col.replace('_', ' ').title() for col in columns)
                    print(f"  {header}")
                    print(f"  {'-' * len(header)}")
                    
                    # Print rows
                    for row in rows:
                        formatted_values = []
                        for i, value in enumerate(row):
                            if isinstance(value, Decimal):
                                value = float(value)
                            if isinstance(value, (int, float)) and columns[i] not in ['subscription_tier', 'status', 'platform', 'priority']:
                                formatted_values.append(format_number(value))
                            else:
                                formatted_values.append(str(value))
                        print(f"  {' | '.join(formatted_values)}")
            else:
                # Single row result
                result = cursor.fetchone()
                if result:
                    for i, col in enumerate(columns):
                        value = result[i]
                        if isinstance(value, Decimal):
                            value = float(value)
                        print(f"  - {col.replace('_', ' ').title()}: {format_number(value) if value is not None else 'N/A'}")

def check_time_series_consistency():
    """Check time series data consistency."""
    print("\n" + "="*80)
    print("TIME SERIES CONSISTENCY")
    print("="*80)
    
    checks = [
        {
            'name': 'Account Creation Timeline',
            'query': """
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as accounts_created
                FROM raw.app_database_accounts
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
                LIMIT 6
            """
        },
        {
            'name': 'Stripe Invoice Timeline',
            'query': """
                SELECT 
                    DATE_TRUNC('month', created_date) as month,
                    COUNT(*) as invoices,
                    SUM(amount_paid) as revenue,
                    ROUND(AVG(amount_paid), 2) as avg_invoice
                FROM raw.stripe_invoices
                WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', created_date)
                ORDER BY month DESC
            """
        },
        {
            'name': 'Google Analytics Trend',
            'query': """
                SELECT 
                    DATE_TRUNC('month', date) as month,
                    SUM(sessions) as total_sessions,
                    SUM(goal_completions) as total_conversions,
                    ROUND(100.0 * SUM(goal_completions) / NULLIF(SUM(sessions), 0), 2) as conversion_rate
                FROM raw.google_analytics_sessions
                GROUP BY DATE_TRUNC('month', date)
                ORDER BY month DESC
                LIMIT 6
            """
        }
    ]
    
    with db_helper.config.get_cursor() as cursor:
        for check in checks:
            print(f"\n{check['name']}:")
            cursor.execute(check['query'])
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if rows:
                # Print header
                header = " | ".join(col.replace('_', ' ').title() for col in columns)
                print(f"  {header}")
                print(f"  {'-' * len(header)}")
                
                # Print rows
                for row in rows:
                    formatted_values = []
                    for i, value in enumerate(row):
                        if isinstance(value, Decimal):
                            value = float(value)
                        if columns[i] == 'month':
                            formatted_values.append(value.strftime('%Y-%m'))
                        elif isinstance(value, (int, float)):
                            formatted_values.append(format_number(value))
                        else:
                            formatted_values.append(str(value))
                    print(f"  {' | '.join(formatted_values)}")

def check_data_quality_issues():
    """Check for common data quality issues."""
    print("\n" + "="*80)
    print("DATA QUALITY CHECKS")
    print("="*80)
    
    issues = []
    
    with db_helper.config.get_cursor() as cursor:
        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) 
            FROM raw.app_database_locations l
            LEFT JOIN raw.app_database_accounts a ON l.customer_id = a.id
            WHERE a.id IS NULL
        """)
        orphaned_locations = cursor.fetchone()[0]
        if orphaned_locations > 0:
            issues.append(f"Found {orphaned_locations} orphaned locations without accounts")
        
        # Check for duplicate emails
        cursor.execute("""
            SELECT primary_contact_email, COUNT(*) as count
            FROM raw.app_database_accounts
            GROUP BY primary_contact_email
            HAVING COUNT(*) > 1
        """)
        duplicate_emails = cursor.fetchall()
        if duplicate_emails:
            issues.append(f"Found {len(duplicate_emails)} duplicate email addresses")
        
        # Check for future dates
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw.app_database_accounts
            WHERE created_at > CURRENT_TIMESTAMP
        """)
        future_dates = cursor.fetchone()[0]
        if future_dates > 0:
            issues.append(f"Found {future_dates} accounts with future creation dates")
        
        # Check attribution weight sums
        cursor.execute("""
            WITH journey_weights AS (
                SELECT 
                    COALESCE(mql_id, 'journey_' || ROW_NUMBER() OVER()) as journey_id,
                    SUM(attribution_weight) as total_weight
                FROM raw.attribution_touchpoints
                WHERE attribution_weight > 0
                GROUP BY mql_id
            )
            SELECT COUNT(*)
            FROM journey_weights
            WHERE ABS(total_weight - 1.0) > 0.01
        """)
        bad_attribution = cursor.fetchone()[0]
        if bad_attribution > 0:
            issues.append(f"Found {bad_attribution} attribution journeys with weights not summing to 1.0")
    
    if issues:
        print("\n⚠️  Quality Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No major data quality issues found!")

def generate_summary_report():
    """Generate executive summary."""
    print("\n" + "="*80)
    print("EXECUTIVE SUMMARY")
    print("="*80)
    
    with db_helper.config.get_cursor() as cursor:
        # Total accounts and MRR
        cursor.execute("""
            SELECT 
                COUNT(*) as total_accounts,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_accounts,
                SUM(CASE WHEN is_active = true THEN monthly_recurring_revenue ELSE 0 END) as total_mrr
            FROM raw.app_database_accounts
        """)
        account_metrics = cursor.fetchone()
        
        # Marketing metrics
        cursor.execute("""
            SELECT 
                (SELECT SUM(cost) FROM raw.google_ads_campaigns) +
                (SELECT SUM(spend) FROM raw.facebook_ads_campaigns) +
                (SELECT SUM(cost) FROM raw.linkedin_ads_campaigns) as total_ad_spend,
                (SELECT COUNT(*) FROM raw.marketing_qualified_leads) as total_mqls,
                (SELECT SUM(amount) FROM raw.hubspot_deals WHERE dealstage = 'closedwon') as pipeline_value
        """)
        marketing_metrics = cursor.fetchone()
        
        # Operational metrics
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM raw.app_database_devices WHERE status = 'online') as online_devices,
                (SELECT COUNT(*) FROM raw.app_database_devices) as total_devices,
                (SELECT COUNT(*) FROM raw.hubspot_tickets WHERE hs_pipeline_stage != 'closed') as open_tickets
        """)
        operational_metrics = cursor.fetchone()
        
        print(f"\n📊 Business Overview:")
        print(f"  - Total Accounts: {format_number(account_metrics[0])}")
        print(f"  - Active Accounts: {format_number(account_metrics[1])} ({account_metrics[1]/account_metrics[0]*100:.1f}%)")
        print(f"  - Total MRR: ${format_number(float(account_metrics[2]))}")
        print(f"  - Annual Run Rate: ${format_number(float(account_metrics[2]) * 12)}")
        
        print(f"\n📈 Marketing Performance:")
        print(f"  - Total Ad Spend: ${format_number(float(marketing_metrics[0]))}")
        print(f"  - Marketing Qualified Leads: {format_number(marketing_metrics[1])}")
        print(f"  - Pipeline Value: ${format_number(float(marketing_metrics[2]))}")
        if marketing_metrics[0] > 0:
            roi = (float(marketing_metrics[2]) / float(marketing_metrics[0])) * 100
            print(f"  - Marketing ROI: {roi:.1f}%")
        
        print(f"\n🔧 Operational Health:")
        print(f"  - Device Uptime: {operational_metrics[0]/operational_metrics[1]*100:.1f}%")
        print(f"  - Open Support Tickets: {format_number(operational_metrics[2])}")

def main():
    print("="*80)
    print("DATA QUALITY AND BUSINESS ANALYTICS VALIDATION")
    print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Run all checks
    check_record_counts()
    check_referential_integrity()
    check_business_metrics()
    check_time_series_consistency()
    check_data_quality_issues()
    generate_summary_report()
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()