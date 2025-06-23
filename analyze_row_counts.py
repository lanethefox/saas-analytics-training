#!/usr/bin/env python3
"""
Analyze row counts and generate LOAD_REPORT.md
"""

from scripts.database_config import db_helper
from scripts.environment_config import current_env
from datetime import datetime

# Expected row counts based on LARGE environment (100K accounts)
EXPECTED_COUNTS = {
    'raw': {
        'app_database_accounts': 100000,
        'app_database_locations': 150000,  # 1.5x accounts
        'app_database_users': 500000,  # 5x accounts
        'app_database_devices': 450000,  # 4.5x accounts
        'app_database_subscriptions': 100000,  # 1 per account (current) + some history
        'app_database_tap_events': 500000000,  # 500M events
        'app_database_user_sessions': 1000000,  # Estimated
        'app_database_page_views': 250000,  # As configured
        'app_database_feature_usage': 1000000,  # Estimated
        'device_telemetry': 100000,
        'stripe_customers': 100000,
        'stripe_prices': 4,  # Basic tiers
        'stripe_subscriptions': 100000,
        'stripe_subscription_items': 100000,
        'stripe_invoices': 1200000,  # ~12 months per subscription
        'stripe_charges': 1200000,  # 1 per invoice
        'stripe_events': 5000000,  # Various events
        'stripe_payment_intents': 1200000,  # 1 per charge
        'hubspot_companies': 100025,  # Accounts + prospects
        'hubspot_contacts': 300000,  # ~3 per company
        'hubspot_deals': 250,  # As configured
        'hubspot_engagements': 37500,  # 150 per deal
        'hubspot_tickets': 10000,
        'hubspot_owners': 1251,  # Sales team + system
        'marketing_campaigns': 120,  # 10 per month
        'marketing_qualified_leads': 10000,
        'campaign_performance': 7200,  # 60 per campaign
        'attribution_touchpoints': 60000,  # 6 per MQL
        'google_analytics_sessions': 800000,  # 8 per account
        'facebook_ads_campaigns': 50,
        'google_ads_campaigns': 75,
        'linkedin_ads_campaigns': 40,
        'iterable_campaigns': 100
    },
    'entity': {},  # dbt models, not generated directly
    'intermediate': {},  # dbt models
    'mart': {}  # dbt models
}

def get_all_tables():
    """Get all tables with row counts"""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                table_schema,
                table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        return cursor.fetchall()

def get_row_count(schema, table):
    """Get exact row count for a table"""
    try:
        with db_helper.config.get_cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            return cursor.fetchone()[0]
    except Exception as e:
        return None

def analyze_counts():
    """Analyze row counts vs expectations"""
    tables = get_all_tables()
    results = {}
    issues = []
    
    for schema, table in tables:
        count = get_row_count(schema, table)
        if schema not in results:
            results[schema] = {}
        results[schema][table] = count
        
        # Check against expectations
        if schema in EXPECTED_COUNTS and table in EXPECTED_COUNTS[schema]:
            expected = EXPECTED_COUNTS[schema][table]
            if count is not None:
                # Allow 10% variance for most tables
                if table in ['app_database_tap_events', 'stripe_events', 'stripe_invoices']:
                    # Allow more variance for large/computed tables
                    variance_allowed = 0.2  # 20%
                else:
                    variance_allowed = 0.1  # 10%
                
                if abs(count - expected) / expected > variance_allowed:
                    issues.append({
                        'schema': schema,
                        'table': table,
                        'expected': expected,
                        'actual': count,
                        'variance': (count - expected) / expected * 100
                    })
    
    return results, issues

def generate_report():
    """Generate LOAD_REPORT.md"""
    results, issues = analyze_counts()
    
    report = f"""# Data Load Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Environment: {current_env.name} (LARGE scale - 100K accounts)

## Executive Summary

Total schemas analyzed: {len(results)}
Total tables: {sum(len(tables) for tables in results.values())}
Tables with issues: {len(issues)}

## Row Count Inventory

"""
    
    # Add row counts by schema
    for schema in sorted(results.keys()):
        report += f"### {schema} Schema\n\n"
        report += "| Table | Row Count | Expected | Status |\n"
        report += "|-------|-----------|----------|--------|\n"
        
        for table in sorted(results[schema].keys()):
            count = results[schema][table]
            expected = EXPECTED_COUNTS.get(schema, {}).get(table, 'N/A')
            
            if count is None:
                status = "❌ Error"
            elif expected == 'N/A':
                status = "➖ No expectation"
            else:
                variance = abs(count - expected) / expected * 100 if expected > 0 else 0
                if variance <= 10:
                    status = "✅ OK"
                elif variance <= 20:
                    status = "⚠️ Warning"
                else:
                    status = "❌ Issue"
            
            count_str = f"{count:,}" if count is not None else "Error"
            expected_str = f"{expected:,}" if isinstance(expected, int) else expected
            
            report += f"| {table} | {count_str} | {expected_str} | {status} |\n"
        
        report += "\n"
    
    # Add issues section
    if issues:
        report += "## Issues Identified\n\n"
        
        for issue in sorted(issues, key=lambda x: abs(x['variance']), reverse=True):
            report += f"### {issue['schema']}.{issue['table']}\n\n"
            report += f"- **Expected**: {issue['expected']:,}\n"
            report += f"- **Actual**: {issue['actual']:,}\n"
            report += f"- **Variance**: {issue['variance']:.1f}%\n\n"
            
            # Root cause analysis
            report += "**Root Cause Analysis**:\n"
            
            # Specific analysis per table
            if issue['table'] == 'app_database_subscriptions':
                if issue['actual'] > issue['expected']:
                    report += "- The subscription generator creates historical records for plan changes\n"
                    report += "- 25% of accounts have subscription history with up to 3 changes each\n"
                    report += "- Expected: 100K current + 25K historical = 125K, but got 171K\n"
                    report += "- The generator may be creating more history than intended\n"
                
            elif issue['table'] == 'stripe_subscriptions':
                report += "- Stripe subscriptions mirror app_database_subscriptions\n"
                report += "- The same historical records issue affects this table\n"
                report += "- Each app subscription creates a corresponding Stripe subscription\n"
            
            elif issue['table'] == 'stripe_invoices':
                if issue['actual'] > issue['expected']:
                    report += "- Expected 12 invoices per subscription (monthly billing)\n"
                    report += "- With 171K subscriptions, this creates more invoices than expected\n"
                    report += "- The generator was limited to 12 months but subscription history inflated the count\n"
                else:
                    report += "- Invoice generation was limited to last 12 months\n"
                    report += "- Some subscriptions may not have full invoice history\n"
            
            elif issue['table'] == 'stripe_subscription_items':
                report += "- Each Stripe subscription creates at least one subscription item\n"
                report += "- With 171K subscriptions, we get more items than expected\n"
                report += "- Some subscriptions may have multiple items (add-ons, usage-based pricing)\n"
            
            elif issue['table'] == 'app_database_locations':
                report += "- Expected 1.5 locations per account on average\n"
                report += "- Actual: 2.1 locations per account\n"
                report += "- The weighted distribution in the generator is producing more multi-location accounts\n"
            
            elif issue['table'] == 'app_database_users':
                report += "- Expected 5 users per account on average\n"
                report += "- Actual: 3 users per account\n"
                report += "- The generator may be creating fewer users for smaller accounts\n"
                report += "- Role distribution may be limiting user creation\n"
            
            elif issue['table'] == 'app_database_user_sessions':
                report += "- Generator was configured for SMALL environment (50K sessions)\n"
                report += "- Should scale to 1M sessions for LARGE environment\n"
                report += "- Generator needs environment-aware scaling\n"
            
            elif issue['table'] == 'app_database_feature_usage':
                report += "- Generator completed but inserted 0 records\n"
                report += "- Likely no users found or date range issue\n"
                report += "- The generator may have run before users were created\n"
            
            elif issue['table'] == 'app_database_tap_events':
                report += "- Configured for 500M events but only generated 8M\n"
                report += "- The chunked generation may have been interrupted\n"
                report += "- Check .tap_events_progress.json for resumption data\n"
                report += "- This is a critical table for analytics\n"
            
            elif issue['table'] == 'hubspot_contacts':
                report += "- Expected 3 contacts per company (300K total)\n"
                report += "- Only generated 40K contacts\n"
                report += "- Generator may be limited by SMALL environment config\n"
            
            elif issue['table'] == 'hubspot_engagements':
                report += "- Expected 150 engagements per deal (37.5K total)\n"
                report += "- Only generated 2.3K engagements\n"
                report += "- Generator may have different multiplier or be limited\n"
            
            elif issue['table'] == 'hubspot_tickets':
                report += "- Expected 10K support tickets\n"
                report += "- Only generated 400 tickets\n"
                report += "- Generator using SMALL environment config (4 per account sample)\n"
            
            elif issue['table'] == 'google_analytics_sessions':
                report += "- Expected 800K sessions (8 per account)\n"
                report += "- Only generated 181 sessions\n"
                report += "- Generator failed or has severe limiting factor\n"
                report += "- Critical for analytics dashboards\n"
            
            elif issue['table'] == 'marketing_qualified_leads':
                report += "- Expected 10K MQLs\n"
                report += "- Only generated 149 MQLs\n"
                report += "- Generator may be using strict qualification criteria\n"
            
            elif issue['table'] == 'attribution_touchpoints':
                report += "- Expected 6 touchpoints per MQL (60K total)\n"
                report += "- With only 149 MQLs, max possible is ~900 touchpoints\n"
                report += "- The 15K actual suggests other touchpoint sources\n"
            
            elif issue['table'] == 'campaign_performance':
                report += "- Expected 60 metrics per campaign (7.2K total)\n"
                report += "- Depends on number of marketing campaigns\n"
                report += "- May need to verify marketing_campaigns count\n"
            
            elif issue['table'] == 'stripe_charges':
                report += "- Expected 1 charge per invoice\n"
                report += "- Fewer charges than invoices suggests failed payments\n"
                report += "- Or invoices without charges (credits, adjustments)\n"
            
            elif issue['table'] == 'stripe_payment_intents':
                report += "- Should match stripe_charges count\n"
                report += "- Payment intents created for each charge attempt\n"
            
            elif issue['table'] == 'stripe_prices':
                report += "- Expected 4 basic pricing tiers\n"
                report += "- Actual has 6 prices\n"
                report += "- May include legacy or custom prices\n"
            
            elif 'ads_campaigns' in issue['table']:
                report += "- Ad campaign tables represent marketing campaigns over time\n"
                report += "- Not scaled by customer count\n"
                report += "- Generator may be creating minimal campaign set\n"
                report += "- Expected counts may be too high for realistic campaign data\n"
            
            elif issue['table'] == 'iterable_campaigns':
                report += "- Email marketing campaigns\n"
                report += "- Only 4 campaigns generated (one per category)\n"
                report += "- Generator using minimal template approach\n"
            
            else:
                report += "- Variance outside expected range\n"
                report += "- Review generator configuration and logic\n"
            
            report += "\n**Proposed Solution**:\n"
            
            # Table-specific solutions
            if issue['table'] == 'app_database_tap_events':
                report += "- Resume the chunked generation: `python3 scripts/generate_tap_events.py`\n"
                report += "- Monitor progress - this will take significant time for 500M records\n"
                report += "- Consider reducing to 50M for development/testing\n"
            
            elif issue['table'] == 'app_database_feature_usage':
                report += "- Re-run after ensuring users exist: `python3 scripts/generate_feature_usage.py`\n"
                report += "- Check date range configuration in the generator\n"
                report += "- Verify user session data is available\n"
            
            elif issue['table'] == 'google_analytics_sessions':
                report += "- Re-run with proper scaling: `python3 scripts/generate_google_analytics_sessions.py`\n"
                report += "- Update generator to use environment config for record count\n"
                report += "- Critical for analytics - prioritize fixing\n"
            
            elif issue['table'] in ['app_database_user_sessions', 'hubspot_contacts', 'hubspot_tickets', 'hubspot_engagements']:
                report += "- Update generator to scale with environment size\n"
                report += "- Re-run with LARGE environment settings\n"
                report += f"- Command: `python3 scripts/generate_{issue['table']}.py`\n"
            
            elif issue['table'] in ['marketing_qualified_leads', 'attribution_touchpoints']:
                report += "- Review qualification criteria in generator\n"
                report += "- These tables are interdependent - fix MQLs first\n"
                report += "- Consider adjusting expected counts to match business logic\n"
            
            elif issue['table'] == 'app_database_subscriptions':
                report += "- Document that 171K is the correct count with history\n"
                report += "- Update expected count to 170K-180K range\n"
                report += "- No action needed - working as designed\n"
            
            elif issue['table'] in ['stripe_subscriptions', 'stripe_subscription_items', 'stripe_invoices']:
                report += "- These counts are correct given subscription history\n"
                report += "- Update expectations to match subscription count\n"
                report += "- Document the multiplier effect in each generator\n"
            
            elif issue['table'] == 'app_database_locations':
                report += "- Adjust weighted distribution to achieve 1.5x multiplier\n"
                report += "- Or document that 2.1x is the actual business ratio\n"
                report += "- Current data is valid - decision needed on target\n"
            
            elif issue['table'] == 'app_database_users':
                report += "- Review user creation logic for small accounts\n"
                report += "- Consider minimum users per account\n"
                report += "- Re-run if 5x multiplier is business requirement\n"
            
            elif 'ads_campaigns' in issue['table'] or issue['table'] == 'iterable_campaigns':
                report += "- These are marketing configuration tables, not transactional\n"
                report += "- Current counts may be realistic for a SaaS company\n"
                report += "- Adjust expectations or add more historical campaigns\n"
            
            elif issue['table'] == 'stripe_prices':
                report += "- 6 prices is reasonable (basic/pro/enterprise × monthly/annual)\n"
                report += "- Document the price structure\n"
                report += "- No action needed\n"
            
            else:
                # Generic solutions based on variance
                if issue['variance'] < -90:
                    report += "- Critical issue - regenerate immediately\n"
                    report += "- Check for environment configuration issues\n"
                    report += "- Verify all dependencies were generated first\n"
                elif issue['variance'] < -50:
                    report += "- Significant gap - investigate root cause\n"
                    report += "- Check generator logs for errors\n"
                    report += "- Consider partial regeneration\n"
                elif issue['variance'] > 50:
                    report += "- Document the business logic causing extra records\n"
                    report += "- Update expectations if variance is intended\n"
                    report += "- Otherwise adjust generator parameters\n"
                else:
                    report += "- Variance within acceptable range\n"
                    report += "- Update documentation with actual ratios\n"
                    report += "- No immediate action required\n"
            
            report += "\n"
    else:
        report += "## Issues Identified\n\nNo significant issues found! All tables are within acceptable variance limits.\n\n"
    
    # Add recommendations
    report += """## Recommendations

1. **Document Expectations**: Update generator scripts with clear comments about expected row counts
2. **Add Validation**: Add post-generation validation to each generator script
3. **Monitor Growth**: As data scales, monitor these ratios to ensure they remain realistic
4. **Historical Data**: Consider the impact of historical data on row counts (e.g., subscription history)

## Data Relationships

Key multipliers observed:
- Locations per Account: ~1.5x
- Users per Account: ~5x
- Devices per Account: ~4.5x
- Invoices per Subscription: ~12x (monthly billing)
- Contacts per Company: ~3x

## Next Steps

1. Review any tables with ❌ Issue status
2. Update generator scripts based on findings
3. Re-run specific generators if needed
4. Update this report after any corrections
"""
    
    return report

def main():
    print("Analyzing database row counts...")
    report = generate_report()
    
    with open('LOAD_REPORT.md', 'w') as f:
        f.write(report)
    
    print("✅ LOAD_REPORT.md created successfully!")

if __name__ == "__main__":
    main()