#!/usr/bin/env python3
"""
Generate educational content from real platform data.
Creates onboarding guides, workday simulations, and exercises using actual data.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.database_config import db_helper

class EducationContentGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            database='saas_platform_dev',
            user='saas_user',
            password='saas_secure_password_2024'
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.edu_dir = Path('edu')
        self.edu_dir.mkdir(exist_ok=True)
        
    def generate_all(self):
        """Generate all educational content"""
        print("🎓 Starting Educational Content Generation...")
        
        # Generate onboarding guides
        self.generate_sales_onboarding()
        self.generate_marketing_onboarding()
        self.generate_product_onboarding()
        self.generate_customer_success_onboarding()
        self.generate_analytics_engineering_onboarding()
        
        # Generate workday simulations
        self.generate_workday_simulations()
        
        # Generate team OKRs
        self.generate_team_okrs()
        
        print("✅ Educational Content Generation Complete!")
    
    def generate_sales_onboarding(self):
        """Generate sales analyst onboarding guide"""
        print("💼 Generating Sales Analyst Onboarding...")
        
        output_dir = self.edu_dir / 'onboarding' / 'sales'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get real data for examples
        self.cur.execute("""
            SELECT 
                a.id,
                a.name,
                s.plan_name,
                s.monthly_price,
                COUNT(DISTINCT l.id) as locations,
                COUNT(DISTINCT d.id) as devices
            FROM raw.app_database_accounts a
            JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
            LEFT JOIN raw.app_database_locations l ON l.customer_id = a.id
            LEFT JOIN raw.app_database_devices d ON d.location_id = l.id
            WHERE s.status = 'active'
            GROUP BY a.id, a.name, s.plan_name, s.monthly_price
            ORDER BY s.monthly_price DESC
            LIMIT 5
        """)
        top_accounts = self.cur.fetchall()
        
        # Day 1: Platform Overview
        with open(output_dir / 'day1_platform_overview.md', 'w') as f:
            f.write("# Day 1: Sales Analytics Platform Overview\n\n")
            f.write("## Welcome to TapFlow Analytics!\n\n")
            f.write("As a Sales Analyst, you'll be working with data from our B2B SaaS platform ")
            f.write("that serves the beverage dispensing industry.\n\n")
            
            f.write("## Your Key Responsibilities\n")
            f.write("- Monitor sales pipeline health\n")
            f.write("- Track revenue metrics (MRR, ARR, growth)\n")
            f.write("- Analyze win/loss patterns\n")
            f.write("- Support sales forecasting\n")
            f.write("- Create executive dashboards\n\n")
            
            f.write("## Platform Overview\n")
            
            # Add current stats
            self.cur.execute("""
                SELECT 
                    COUNT(DISTINCT customer_id) as total_customers,
                    SUM(monthly_price) as mrr,
                    AVG(monthly_price) as avg_deal_size
                FROM raw.app_database_subscriptions
                WHERE status = 'active'
            """)
            stats = self.cur.fetchone()
            
            f.write(f"### Current Business Metrics\n")
            f.write(f"- **Active Customers**: {stats['total_customers']:,}\n")
            f.write(f"- **Monthly Recurring Revenue**: ${stats['mrr']:,.2f}\n")
            f.write(f"- **Average Deal Size**: ${stats['avg_deal_size']:,.2f}\n\n")
            
            f.write("### Top 5 Accounts (Your Focus Accounts)\n\n")
            f.write("These are real accounts you'll be analyzing:\n\n")
            f.write("| Account | Plan | MRR | Locations | Devices |\n")
            f.write("|---------|------|-----|-----------|----------|\n")
            
            for acc in top_accounts:
                f.write(f"| {acc['name']} | {acc['plan_name']} | ${acc['monthly_price']:,.2f} | {acc['locations']} | {acc['devices']:,} |\n")
            
            f.write("\n## Today's Exercise\n")
            f.write("1. Log into the analytics platform\n")
            f.write("2. Navigate to the Sales Dashboard\n")
            f.write("3. Find the account '{}'".format(top_accounts[0]['name']))
            f.write(" and note their:\n")
            f.write("   - Subscription start date\n")
            f.write("   - Device growth over time\n")
            f.write("   - Recent activity\n\n")
            
            f.write("## Key Tables You'll Use\n")
            f.write("```sql\n")
            f.write("-- Accounts and their subscriptions\n")
            f.write("SELECT * FROM raw.app_database_accounts;\n")
            f.write("SELECT * FROM raw.app_database_subscriptions;\n\n")
            f.write("-- For pipeline analysis\n")
            f.write("SELECT * FROM staging.stg_opportunities;  -- Once available\n")
            f.write("```\n\n")
            
            f.write("## Helpful Query\n")
            f.write("```sql\n")
            f.write("-- Get MRR by plan\n")
            f.write("SELECT \n")
            f.write("    plan_name,\n")
            f.write("    COUNT(*) as customers,\n")
            f.write("    SUM(monthly_price) as total_mrr\n")
            f.write("FROM raw.app_database_subscriptions\n")
            f.write("WHERE status = 'active'\n")
            f.write("GROUP BY plan_name\n")
            f.write("ORDER BY total_mrr DESC;\n")
            f.write("```\n")
        
        # Day 2: Sales Data Model
        with open(output_dir / 'day2_sales_data_model.md', 'w') as f:
            f.write("# Day 2: Understanding the Sales Data Model\n\n")
            f.write("## The Sales Analytics Data Flow\n\n")
            f.write("```mermaid\n")
            f.write("graph LR\n")
            f.write("    A[Leads] --> B[Opportunities]\n")
            f.write("    B --> C[Accounts]\n")
            f.write("    C --> D[Subscriptions]\n")
            f.write("    D --> E[Revenue]\n")
            f.write("```\n\n")
            
            f.write("## Core Entities\n\n")
            f.write("### Accounts (Closed Won)\n")
            f.write("Currently we have {} accounts in the system.\n\n".format(stats['total_customers']))
            
            f.write("Key fields:\n")
            f.write("- `id`: Unique identifier\n")
            f.write("- `name`: Company name\n")
            f.write("- `business_type`: Industry segment\n")
            f.write("- `created_date`: When they became a customer\n\n")
            
            f.write("### Subscriptions (Revenue Generator)\n")
            f.write("Each account has one active subscription.\n\n")
            
            f.write("Key fields:\n")
            f.write("- `customer_id`: Links to account\n")
            f.write("- `plan_name`: Tier (starter/professional/business/enterprise)\n")
            f.write("- `monthly_price`: MRR contribution\n")
            f.write("- `start_date`: Subscription start\n\n")
            
            f.write("## Real Data Exercise\n\n")
            
            # Get a specific account for exercise
            self.cur.execute("""
                SELECT 
                    a.id,
                    a.name,
                    a.business_type,
                    s.plan_name,
                    s.monthly_price,
                    DATE(s.start_date) as start_date
                FROM raw.app_database_accounts a
                JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
                WHERE s.plan_name = 'enterprise'
                ORDER BY RANDOM()
                LIMIT 1
            """)
            example = self.cur.fetchone()
            
            f.write(f"Let's analyze a real enterprise account: **{example['name']}**\n\n")
            f.write("Run this query:\n")
            f.write("```sql\n")
            f.write(f"-- Analyze {example['name']}'s growth\n")
            f.write("WITH account_metrics AS (\n")
            f.write("    SELECT \n")
            f.write("        a.id,\n")
            f.write("        a.name,\n")
            f.write("        COUNT(DISTINCT l.id) as location_count,\n")
            f.write("        COUNT(DISTINCT d.id) as device_count,\n")
            f.write("        s.monthly_price as mrr\n")
            f.write("    FROM raw.app_database_accounts a\n")
            f.write("    JOIN raw.app_database_subscriptions s ON s.customer_id = a.id\n")
            f.write("    LEFT JOIN raw.app_database_locations l ON l.customer_id = a.id\n")
            f.write("    LEFT JOIN raw.app_database_devices d ON d.location_id = l.id\n")
            f.write(f"    WHERE a.id = '{example['id']}'\n")
            f.write("    GROUP BY a.id, a.name, s.monthly_price\n")
            f.write(")\n")
            f.write("SELECT * FROM account_metrics;\n")
            f.write("```\n\n")
            
            f.write("## Key Insights to Find\n")
            f.write("1. What's their device-to-revenue ratio?\n")
            f.write("2. How many locations do they have?\n")
            f.write("3. What's their potential for expansion?\n")
        
        # Continue with remaining days...
        self.generate_remaining_sales_days(output_dir, top_accounts)
    
    def generate_remaining_sales_days(self, output_dir, top_accounts):
        """Generate days 3-5 of sales onboarding"""
        
        # Day 3: Key Sales Metrics
        with open(output_dir / 'day3_sales_metrics.md', 'w') as f:
            f.write("# Day 3: Key Sales Metrics Deep Dive\n\n")
            f.write("## Core Sales Metrics\n\n")
            
            # Get real metric values
            self.cur.execute("""
                SELECT 
                    SUM(monthly_price) as mrr,
                    COUNT(DISTINCT customer_id) as customers,
                    AVG(monthly_price) as avg_deal_size,
                    SUM(monthly_price) * 12 as arr
                FROM raw.app_database_subscriptions
                WHERE status = 'active'
            """)
            metrics = self.cur.fetchone()
            
            f.write("### Current Performance\n")
            f.write(f"- **MRR**: ${metrics['mrr']:,.2f}\n")
            f.write(f"- **ARR**: ${metrics['arr']:,.2f}\n")
            f.write(f"- **Total Customers**: {metrics['customers']:,}\n")
            f.write(f"- **ARPA**: ${metrics['avg_deal_size']:,.2f}\n\n")
            
            f.write("## Metric Calculations\n\n")
            f.write("### 1. Monthly Recurring Revenue (MRR)\n")
            f.write("```sql\n")
            f.write("-- Calculate current MRR\n")
            f.write("SELECT \n")
            f.write("    DATE_TRUNC('month', CURRENT_DATE) as month,\n")
            f.write("    SUM(monthly_price) as mrr,\n")
            f.write("    COUNT(*) as active_subscriptions\n")
            f.write("FROM raw.app_database_subscriptions\n")
            f.write("WHERE status = 'active';\n")
            f.write("```\n\n")
            
            f.write("### 2. MRR Movement Analysis\n")
            f.write("```sql\n")
            f.write("-- New MRR this month\n")
            f.write("SELECT \n")
            f.write("    SUM(monthly_price) as new_mrr,\n")
            f.write("    COUNT(*) as new_customers\n")
            f.write("FROM raw.app_database_subscriptions\n")
            f.write("WHERE DATE_TRUNC('month', start_date) = DATE_TRUNC('month', CURRENT_DATE)\n")
            f.write("AND status = 'active';\n")
            f.write("```\n\n")
            
            f.write("## Today's Project\n")
            f.write("Create a sales performance dashboard showing:\n")
            f.write("1. MRR trend over last 6 months\n")
            f.write("2. New customers by month\n")
            f.write("3. Revenue by customer segment\n")
            f.write("4. Top 10 accounts by revenue\n")
        
        # Day 4: Building Dashboards
        with open(output_dir / 'day4_sales_dashboards.md', 'w') as f:
            f.write("# Day 4: Building Your First Sales Dashboard\n\n")
            f.write("## Dashboard Components\n\n")
            
            f.write("### 1. Executive Summary\n")
            f.write("```sql\n")
            f.write("-- Executive KPIs\n")
            f.write("WITH kpis AS (\n")
            f.write("    SELECT \n")
            f.write("        SUM(monthly_price) as mrr,\n")
            f.write("        SUM(monthly_price) * 12 as arr,\n")
            f.write("        COUNT(DISTINCT customer_id) as total_customers,\n")
            f.write("        SUM(monthly_price) / COUNT(DISTINCT customer_id) as arpa\n")
            f.write("    FROM raw.app_database_subscriptions\n")
            f.write("    WHERE status = 'active'\n")
            f.write(")\n")
            f.write("SELECT * FROM kpis;\n")
            f.write("```\n\n")
            
            f.write("### 2. Revenue Breakdown\n")
            f.write("```sql\n")
            f.write("-- Revenue by segment\n")
            f.write("SELECT \n")
            f.write("    s.plan_name,\n")
            f.write("    COUNT(*) as customers,\n")
            f.write("    SUM(s.monthly_price) as segment_mrr,\n")
            f.write("    ROUND(SUM(s.monthly_price) * 100.0 / SUM(SUM(s.monthly_price)) OVER (), 1) as revenue_share\n")
            f.write("FROM raw.app_database_subscriptions s\n")
            f.write("WHERE s.status = 'active'\n")
            f.write("GROUP BY s.plan_name\n")
            f.write("ORDER BY segment_mrr DESC;\n")
            f.write("```\n")
        
        # Day 5: Advanced Analytics
        with open(output_dir / 'day5_advanced_analytics.md', 'w') as f:
            f.write("# Day 5: Advanced Sales Analytics\n\n")
            f.write("## Cohort Analysis\n")
            f.write("```sql\n")
            f.write("-- Revenue cohort analysis\n")
            f.write("WITH cohorts AS (\n")
            f.write("    SELECT \n")
            f.write("        DATE_TRUNC('month', start_date) as cohort_month,\n")
            f.write("        customer_id,\n")
            f.write("        monthly_price\n")
            f.write("    FROM raw.app_database_subscriptions\n")
            f.write("    WHERE status = 'active'\n")
            f.write(")\n")
            f.write("SELECT \n")
            f.write("    cohort_month,\n")
            f.write("    COUNT(DISTINCT customer_id) as cohort_size,\n")
            f.write("    SUM(monthly_price) as cohort_mrr,\n")
            f.write("    AVG(monthly_price) as avg_deal_size\n")
            f.write("FROM cohorts\n")
            f.write("GROUP BY cohort_month\n")
            f.write("ORDER BY cohort_month DESC;\n")
            f.write("```\n\n")
            
            f.write("## Expansion Revenue Opportunities\n")
            
            # Find expansion opportunities
            self.cur.execute("""
                SELECT 
                    a.name,
                    s.plan_name,
                    s.monthly_price,
                    COUNT(DISTINCT d.id) as device_count,
                    CASE 
                        WHEN s.plan_name = 'starter' AND COUNT(DISTINCT d.id) > 8 THEN 'Upgrade to Professional'
                        WHEN s.plan_name = 'professional' AND COUNT(DISTINCT d.id) > 40 THEN 'Upgrade to Business'
                        WHEN s.plan_name = 'business' AND COUNT(DISTINCT d.id) > 150 THEN 'Upgrade to Enterprise'
                        ELSE 'Properly Tiered'
                    END as recommendation
                FROM raw.app_database_accounts a
                JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
                LEFT JOIN raw.app_database_locations l ON l.customer_id = a.id
                LEFT JOIN raw.app_database_devices d ON d.location_id = l.id
                WHERE s.status = 'active'
                GROUP BY a.name, s.plan_name, s.monthly_price
                HAVING COUNT(DISTINCT d.id) > 
                    CASE 
                        WHEN s.plan_name = 'starter' THEN 8
                        WHEN s.plan_name = 'professional' THEN 40
                        WHEN s.plan_name = 'business' THEN 150
                        ELSE 999999
                    END
                LIMIT 5
            """)
            
            opportunities = self.cur.fetchall()
            
            if opportunities:
                f.write("\n### Real Expansion Opportunities\n\n")
                f.write("| Account | Current Plan | Devices | Recommendation | Potential MRR Increase |\n")
                f.write("|---------|--------------|---------|----------------|------------------------|\n")
                
                for opp in opportunities:
                    current_mrr = opp['monthly_price']
                    if 'Professional' in opp['recommendation']:
                        new_mrr = 999
                    elif 'Business' in opp['recommendation']:
                        new_mrr = 2999
                    elif 'Enterprise' in opp['recommendation']:
                        new_mrr = 9999
                    else:
                        new_mrr = current_mrr
                    
                    increase = new_mrr - current_mrr
                    f.write(f"| {opp['name']} | {opp['plan_name']} | {opp['device_count']} | {opp['recommendation']} | ${increase:,.2f} |\n")
            
            f.write("\n## Week 1 Wrap-up\n")
            f.write("Congratulations! You've completed your first week. You should now be able to:\n")
            f.write("- Navigate the sales data model\n")
            f.write("- Calculate key revenue metrics\n")
            f.write("- Build basic dashboards\n")
            f.write("- Identify expansion opportunities\n")
            f.write("- Perform cohort analysis\n")
    
    def generate_marketing_onboarding(self):
        """Generate marketing analyst onboarding"""
        print("📈 Generating Marketing Analyst Onboarding...")
        
        output_dir = self.edu_dir / 'onboarding' / 'marketing'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'day1_marketing_overview.md', 'w') as f:
            f.write("# Marketing Analytics Onboarding\n\n")
            f.write("## Week 1: Foundation\n\n")
            
            # Get customer acquisition data
            self.cur.execute("""
                SELECT 
                    DATE_TRUNC('month', created_date) as acquisition_month,
                    COUNT(*) as new_customers,
                    COUNT(*) * 299 as estimated_acquisition_cost
                FROM raw.app_database_accounts
                WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY 1
                ORDER BY 1 DESC
            """)
            
            f.write("### Recent Customer Acquisition\n\n")
            f.write("| Month | New Customers | Est. Acquisition Cost |\n")
            f.write("|-------|---------------|----------------------|\n")
            
            for row in self.cur.fetchall():
                month = row['acquisition_month'].strftime('%Y-%m')
                f.write(f"| {month} | {row['new_customers']} | ${row['estimated_acquisition_cost']:,} |\n")
            
            f.write("\n### Your Focus Areas\n")
            f.write("- Customer Acquisition Cost (CAC)\n")
            f.write("- Lead-to-Customer Conversion\n")
            f.write("- Channel Performance\n")
            f.write("- Campaign ROI\n")
    
    def generate_product_onboarding(self):
        """Generate product analyst onboarding"""
        print("📱 Generating Product Analyst Onboarding...")
        
        output_dir = self.edu_dir / 'onboarding' / 'product'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'day1_product_overview.md', 'w') as f:
            f.write("# Product Analytics Onboarding\n\n")
            f.write("## Understanding Product Usage\n\n")
            
            # Get device usage stats
            self.cur.execute("""
                SELECT 
                    device_type,
                    COUNT(*) as device_count,
                    COUNT(CASE WHEN status = 'online' THEN 1 END) as online_count,
                    ROUND(COUNT(CASE WHEN status = 'online' THEN 1 END) * 100.0 / COUNT(*), 1) as online_pct
                FROM raw.app_database_devices
                GROUP BY device_type
                ORDER BY device_count DESC
            """)
            
            f.write("### Device Usage Patterns\n\n")
            f.write("| Device Type | Total | Online | Online % |\n")
            f.write("|-------------|-------|--------|----------|\n")
            
            for row in self.cur.fetchall():
                f.write(f"| {row['device_type']} | {row['device_count']:,} | {row['online_count']:,} | {row['online_pct']}% |\n")
            
            f.write("\n### Key Product Metrics\n")
            f.write("- Feature Adoption Rate\n")
            f.write("- User Engagement (DAU/MAU)\n")
            f.write("- Time to Value\n")
            f.write("- Product Health Score\n")
    
    def generate_customer_success_onboarding(self):
        """Generate customer success analyst onboarding"""
        print("🤝 Generating Customer Success Analyst Onboarding...")
        
        output_dir = self.edu_dir / 'onboarding' / 'customer_success'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'day1_cs_overview.md', 'w') as f:
            f.write("# Customer Success Analytics Onboarding\n\n")
            f.write("## Your Mission\n")
            f.write("Ensure customer success through data-driven insights.\n\n")
            
            # Get at-risk accounts
            self.cur.execute("""
                WITH device_health AS (
                    SELECT 
                        l.customer_id,
                        COUNT(CASE WHEN d.status = 'online' THEN 1 END) * 100.0 / COUNT(*) as uptime_pct
                    FROM raw.app_database_locations l
                    JOIN raw.app_database_devices d ON d.location_id = l.id
                    GROUP BY l.customer_id
                )
                SELECT 
                    a.name,
                    s.plan_name,
                    dh.uptime_pct,
                    CASE 
                        WHEN dh.uptime_pct < 70 THEN 'High Risk'
                        WHEN dh.uptime_pct < 80 THEN 'Medium Risk'
                        ELSE 'Healthy'
                    END as risk_level
                FROM raw.app_database_accounts a
                JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
                JOIN device_health dh ON dh.customer_id = a.id
                WHERE dh.uptime_pct < 80
                ORDER BY dh.uptime_pct
                LIMIT 5
            """)
            
            at_risk = self.cur.fetchall()
            
            if at_risk:
                f.write("### At-Risk Accounts Requiring Attention\n\n")
                f.write("| Account | Plan | Device Uptime | Risk Level |\n")
                f.write("|---------|------|---------------|------------|\n")
                
                for acc in at_risk:
                    f.write(f"| {acc['name']} | {acc['plan_name']} | {acc['uptime_pct']:.1f}% | {acc['risk_level']} |\n")
            
            f.write("\n### Key CS Metrics\n")
            f.write("- Customer Health Score\n")
            f.write("- Net Revenue Retention (NRR)\n")
            f.write("- Churn Risk Prediction\n")
            f.write("- Time to Resolution\n")
    
    def generate_analytics_engineering_onboarding(self):
        """Generate analytics engineering onboarding"""
        print("🔧 Generating Analytics Engineering Onboarding...")
        
        output_dir = self.edu_dir / 'onboarding' / 'analytics_engineering'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'week1_technical_foundation.md', 'w') as f:
            f.write("# Analytics Engineering Onboarding\n\n")
            f.write("## Week 1: Technical Foundation\n\n")
            
            f.write("### Day 1: dbt Project Structure\n")
            f.write("```bash\n")
            f.write("transform/\n")
            f.write("├── models/\n")
            f.write("│   ├── staging/       # Clean raw data\n")
            f.write("│   ├── intermediate/  # Business logic\n")
            f.write("│   └── metrics/       # Final metrics\n")
            f.write("├── tests/            # Data quality tests\n")
            f.write("├── macros/           # Reusable SQL\n")
            f.write("└── dbt_project.yml   # Configuration\n")
            f.write("```\n\n")
            
            f.write("### Current Data Architecture\n")
            
            # Get schema statistics
            self.cur.execute("""
                SELECT 
                    table_schema,
                    COUNT(*) as table_count,
                    SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint / 1024 / 1024 as size_mb
                FROM pg_tables
                WHERE schemaname IN ('raw', 'staging', 'intermediate', 'metrics')
                GROUP BY table_schema
                ORDER BY table_schema
            """)
            
            f.write("| Schema | Tables | Size (MB) |\n")
            f.write("|--------|--------|----------|\n")
            
            for row in self.cur.fetchall():
                f.write(f"| {row['table_schema']} | {row['table_count']} | {row['size_mb']:.1f} |\n")
            
            f.write("\n### Your Responsibilities\n")
            f.write("- Data pipeline reliability (99.9% uptime)\n")
            f.write("- Data quality monitoring\n")
            f.write("- Performance optimization\n")
            f.write("- Self-service enablement\n")
    
    def generate_workday_simulations(self):
        """Generate workday simulation content"""
        print("📅 Generating Workday Simulations...")
        
        output_dir = self.edu_dir / 'workday_simulations'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sales Analyst Day
        with open(output_dir / 'sales_analyst_day.md', 'w') as f:
            f.write("# A Day in the Life: Sales Analyst\n\n")
            f.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n\n")
            
            # Get yesterday's metrics
            self.cur.execute("""
                SELECT 
                    COUNT(CASE WHEN DATE(start_date) = CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as new_customers_yesterday,
                    SUM(CASE WHEN DATE(start_date) = CURRENT_DATE - INTERVAL '1 day' THEN monthly_price END) as new_mrr_yesterday
                FROM raw.app_database_subscriptions
            """)
            yesterday = self.cur.fetchone()
            
            f.write("## 9:00 AM - Daily Standup Prep\n\n")
            f.write("Check yesterday's performance:\n")
            f.write("```sql\n")
            f.write("-- Yesterday's new business\n")
            f.write("SELECT \n")
            f.write("    COUNT(*) as new_customers,\n")
            f.write("    SUM(monthly_price) as new_mrr\n")
            f.write("FROM raw.app_database_subscriptions\n")
            f.write("WHERE DATE(start_date) = CURRENT_DATE - INTERVAL '1 day';\n")
            f.write("```\n\n")
            
            if yesterday['new_customers_yesterday']:
                f.write(f"**Result**: {yesterday['new_customers_yesterday']} new customers, ${yesterday['new_mrr_yesterday']:,.2f} new MRR\n\n")
            else:
                f.write("**Result**: No new customers yesterday\n\n")
            
            f.write("## 9:30 AM - Executive Dashboard Update\n\n")
            
            # Get a real anomaly to investigate
            self.cur.execute("""
                WITH daily_devices AS (
                    SELECT 
                        l.customer_id,
                        a.name,
                        COUNT(CASE WHEN d.status = 'online' THEN 1 END) as online_devices,
                        COUNT(*) as total_devices,
                        COUNT(CASE WHEN d.status = 'online' THEN 1 END) * 100.0 / COUNT(*) as uptime_pct
                    FROM raw.app_database_locations l
                    JOIN raw.app_database_devices d ON d.location_id = l.id
                    JOIN raw.app_database_accounts a ON a.id = l.customer_id
                    GROUP BY l.customer_id, a.name
                    HAVING COUNT(*) > 50
                )
                SELECT * FROM daily_devices
                WHERE uptime_pct < 75
                ORDER BY total_devices DESC
                LIMIT 1
            """)
            
            anomaly = self.cur.fetchone()
            
            if anomaly:
                f.write("## 10:00 AM - Investigate Anomaly\n\n")
                f.write(f"**Alert**: {anomaly['name']} showing low device uptime ({anomaly['uptime_pct']:.1f}%)\n\n")
                f.write("Investigation query:\n")
                f.write("```sql\n")
                f.write("-- Check device status distribution\n")
                f.write("SELECT \n")
                f.write("    d.status,\n")
                f.write("    COUNT(*) as device_count,\n")
                f.write("    l.name as location\n")
                f.write("FROM raw.app_database_devices d\n")
                f.write("JOIN raw.app_database_locations l ON l.id = d.location_id\n")
                f.write(f"WHERE l.customer_id = '{anomaly['customer_id']}'\n")
                f.write("GROUP BY d.status, l.name\n")
                f.write("ORDER BY device_count DESC;\n")
                f.write("```\n\n")
                
                f.write("**Action**: Notify Customer Success team for proactive outreach\n\n")
            
            f.write("## 2:00 PM - Custom Report Request\n\n")
            f.write("Regional manager wants to see performance by state.\n\n")
            f.write("```sql\n")
            f.write("-- Revenue by state\n")
            f.write("SELECT \n")
            f.write("    l.state,\n")
            f.write("    COUNT(DISTINCT l.customer_id) as customers,\n")
            f.write("    SUM(s.monthly_price) as state_mrr,\n")
            f.write("    AVG(s.monthly_price) as avg_deal_size\n")
            f.write("FROM raw.app_database_locations l\n")
            f.write("JOIN raw.app_database_subscriptions s ON s.customer_id = l.customer_id\n")
            f.write("WHERE s.status = 'active'\n")
            f.write("GROUP BY l.state\n")
            f.write("ORDER BY state_mrr DESC\n")
            f.write("LIMIT 10;\n")
            f.write("```\n\n")
            
            f.write("## 4:00 PM - Weekly Forecast Prep\n\n")
            f.write("Prepare data for tomorrow's forecast meeting.\n\n")
            f.write("```sql\n")
            f.write("-- Pipeline forecast\n")
            f.write("WITH monthly_run_rate AS (\n")
            f.write("    SELECT \n")
            f.write("        DATE_TRUNC('month', start_date) as month,\n")
            f.write("        SUM(monthly_price) as new_mrr,\n")
            f.write("        COUNT(*) as new_customers\n")
            f.write("    FROM raw.app_database_subscriptions\n")
            f.write("    WHERE start_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')\n")
            f.write("    GROUP BY 1\n")
            f.write(")\n")
            f.write("SELECT \n")
            f.write("    month,\n")
            f.write("    new_mrr,\n")
            f.write("    new_customers,\n")
            f.write("    AVG(new_mrr) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as rolling_avg\n")
            f.write("FROM monthly_run_rate\n")
            f.write("ORDER BY month;\n")
            f.write("```\n")
    
    def generate_team_okrs(self):
        """Generate team OKRs and priorities"""
        print("🎯 Generating Team OKRs...")
        
        output_dir = self.edu_dir / 'team_okrs'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get current business metrics for context
        self.cur.execute("""
            SELECT 
                COUNT(DISTINCT customer_id) as total_customers,
                SUM(monthly_price) as current_mrr,
                COUNT(DISTINCT customer_id) FILTER (WHERE DATE_TRUNC('quarter', start_date) = DATE_TRUNC('quarter', CURRENT_DATE)) as new_customers_qtd
            FROM raw.app_database_subscriptions
            WHERE status = 'active'
        """)
        metrics = self.cur.fetchone()
        
        with open(output_dir / 'q1_2025_okrs.md', 'w') as f:
            f.write("# Q1 2025 OKRs - All Teams\n\n")
            f.write(f"Current State: {metrics['total_customers']:,} customers, ${metrics['current_mrr']:,.2f} MRR\n\n")
            
            f.write("## Sales Team OKRs\n\n")
            f.write("### Objective 1: Accelerate Revenue Growth\n")
            f.write("**Key Results:**\n")
            f.write(f"- KR1: Increase MRR from ${metrics['current_mrr']:,.2f} to ${metrics['current_mrr'] * 1.15:,.2f} (15% growth)\n")
            f.write("- KR2: Close 50 new enterprise accounts\n")
            f.write("- KR3: Achieve 95% forecast accuracy\n\n")
            
            f.write("**Initiatives:**\n")
            f.write("- Implement predictive lead scoring\n")
            f.write("- Launch enterprise sales playbook\n")
            f.write("- Automate pipeline reporting\n\n")
            
            f.write("### Objective 2: Improve Sales Efficiency\n")
            f.write("**Key Results:**\n")
            f.write("- KR1: Reduce average sales cycle from 45 to 35 days\n")
            f.write("- KR2: Increase win rate from 25% to 30%\n")
            f.write("- KR3: Achieve 90% CRM data quality score\n\n")
            
            f.write("## Marketing Team OKRs\n\n")
            f.write("### Objective 1: Optimize Customer Acquisition\n")
            f.write("**Key Results:**\n")
            f.write("- KR1: Reduce CAC by 20% while maintaining quality\n")
            f.write("- KR2: Generate 500 qualified leads per month\n")
            f.write("- KR3: Achieve 30% MQL to SQL conversion rate\n\n")
            
            f.write("## Product Team OKRs\n\n")
            f.write("### Objective 1: Drive Product-Led Growth\n")
            f.write("**Key Results:**\n")
            f.write("- KR1: Increase feature adoption rate to 80%\n")
            f.write("- KR2: Reduce time-to-value from 14 to 7 days\n")
            f.write("- KR3: Achieve 50+ NPS score\n\n")
            
            f.write("## Customer Success Team OKRs\n\n")
            f.write("### Objective 1: Maximize Customer Retention\n")
            f.write("**Key Results:**\n")
            f.write("- KR1: Maintain churn rate below 10% annually\n")
            f.write("- KR2: Achieve 120% net revenue retention\n")
            f.write("- KR3: Complete QBRs with 100% of enterprise accounts\n\n")
            
            f.write("## Analytics Engineering Team OKRs\n\n")
            f.write("### Objective 1: Enable Data-Driven Decision Making\n")
            f.write("**Key Results:**\n")
            f.write("- KR1: Achieve 99.9% data pipeline uptime\n")
            f.write("- KR2: Reduce metric calculation time by 50%\n")
            f.write("- KR3: Launch self-service analytics for 80% of use cases\n")
    
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    generator = EducationContentGenerator()
    generator.generate_all()