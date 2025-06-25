#!/usr/bin/env python3
"""
Generate synthetic Google Ads campaigns data for the bar management SaaS platform.

This module creates Google advertising campaign records with:
- Search campaigns
- Display campaigns
- Shopping campaigns
- Performance Max campaigns
- Realistic quality scores and performance metrics
"""

import sys
import os
import json
import random
import uuid
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# Campaign configuration
CAMPAIGN_TYPES = [
    ('SEARCH', 0.40),
    ('DISPLAY', 0.25),
    ('PERFORMANCE_MAX', 0.20),
    ('VIDEO', 0.10),
    ('SHOPPING', 0.05)
]

CAMPAIGN_STATUS = [
    ('ENABLED', 0.60),
    ('PAUSED', 0.20),
    ('ENDED', 0.15),
    ('PENDING', 0.05)
]

# Industry-specific keywords for search campaigns
SEARCH_KEYWORDS = [
    'bar management software',
    'bar inventory system',
    'bar pos system',
    'restaurant management software',
    'hospitality software',
    'bar analytics dashboard',
    'liquor inventory tracking',
    'bar staff scheduling',
    'bar accounting software',
    'cocktail recipe management',
    'bar equipment monitoring',
    'tavern management system'
]

# Ad group themes
AD_GROUP_THEMES = [
    'Inventory Management',
    'Staff Scheduling',
    'Analytics & Reporting',
    'POS Integration',
    'Cost Control',
    'Customer Experience',
    'Compliance & Safety',
    'Mobile Solutions'
]

# Quality score factors
def calculate_quality_score():
    """Calculate Google Ads quality score (1-10)"""
    # Weighted average of factors
    relevance = random.randint(5, 10)
    landing_page = random.randint(4, 10)
    ctr = random.randint(3, 10)
    
    score = (relevance * 0.4 + landing_page * 0.3 + ctr * 0.3)
    return max(1, min(10, int(score)))

def generate_google_campaigns():
    """Generate Google Ads campaigns"""
    campaigns = []
    
    # Calculate number of campaigns based on environment
    # Roughly 1 campaign per 25 accounts for realistic ratio
    num_campaigns = max(100, current_env.accounts // 25)
    
    print(f"Generating {num_campaigns:,} Google Ads campaigns...")
    
    # Time range for campaigns (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    for i in range(num_campaigns):
        campaign_id = f"goog_camp_{uuid.uuid4().hex[:12]}"
        
        # Campaign dates
        campaign_start = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days - 30)
        )
        campaign_end = campaign_start + timedelta(days=random.randint(30, 180))
        
        # Determine campaign type and status
        campaign_type = random.choices(
            [t[0] for t in CAMPAIGN_TYPES],
            [t[1] for t in CAMPAIGN_TYPES]
        )[0]
        
        # Status based on dates
        if campaign_end < datetime.now():
            status = 'ENDED'
        elif campaign_start > datetime.now():
            status = 'PENDING'
        else:
            status = random.choices(
                ['ENABLED', 'PAUSED'],
                [0.75, 0.25]
            )[0]
        
        # Budget and bidding
        daily_budget = random.choice([25, 50, 75, 100, 150, 200, 300])
        bidding_strategy = random.choice([
            'MAXIMIZE_CLICKS',
            'MAXIMIZE_CONVERSIONS',
            'TARGET_CPA',
            'TARGET_ROAS',
            'MAXIMIZE_CONVERSION_VALUE'
        ])
        
        # Calculate actual spend based on status
        if status == 'ENDED':
            days_run = (campaign_end - campaign_start).days
            spend_ratio = random.uniform(0.85, 0.98)
        elif status == 'ENABLED':
            days_run = (datetime.now() - campaign_start).days
            spend_ratio = random.uniform(0.80, 0.95)
        else:
            days_run = random.randint(1, 30)
            spend_ratio = random.uniform(0.1, 0.3)
        
        total_spend = daily_budget * days_run * spend_ratio
        
        # Performance metrics based on campaign type
        quality_score = calculate_quality_score()
        
        if campaign_type == 'SEARCH':
            impressions = int(total_spend * random.uniform(200, 400))    # $2.50-5.00 CPM
            clicks = int(impressions * random.uniform(0.025, 0.045))     # 2.5-4.5% CTR
            conversions = int(clicks * random.uniform(0.05, 0.15))       # 5-15% conversion
        elif campaign_type == 'DISPLAY':
            impressions = int(total_spend * random.uniform(1000, 2000))  # $0.50-1.00 CPM
            clicks = int(impressions * random.uniform(0.001, 0.003))     # 0.1-0.3% CTR
            conversions = int(clicks * random.uniform(0.02, 0.05))       # 2-5% conversion
        elif campaign_type == 'PERFORMANCE_MAX':
            impressions = int(total_spend * random.uniform(400, 800))
            clicks = int(impressions * random.uniform(0.015, 0.03))      # 1.5-3% CTR
            conversions = int(clicks * random.uniform(0.08, 0.18))       # 8-18% conversion
        elif campaign_type == 'VIDEO':
            impressions = int(total_spend * random.uniform(100, 300))    # $3.33-10 CPM
            clicks = int(impressions * random.uniform(0.005, 0.015))     # 0.5-1.5% CTR
            conversions = int(clicks * random.uniform(0.01, 0.03))       # 1-3% conversion
        else:  # SHOPPING
            impressions = int(total_spend * random.uniform(300, 600))
            clicks = int(impressions * random.uniform(0.02, 0.04))       # 2-4% CTR
            conversions = int(clicks * random.uniform(0.03, 0.08))       # 3-8% conversion
        
        # Generate campaign name
        theme = random.choice(AD_GROUP_THEMES)
        campaign_name = f"{campaign_type} - {theme} - {campaign_start.strftime('%b %Y')}"
        
        # Removed network settings, geo targets, and advanced metrics - not in schema
        
        # Map campaign type to advertising channel type
        advertising_channel_map = {
            'SEARCH': 'SEARCH',
            'DISPLAY': 'DISPLAY',
            'PERFORMANCE_MAX': 'MULTI_CHANNEL',
            'VIDEO': 'VIDEO',
            'SHOPPING': 'SHOPPING'
        }
        
        campaign = {
            'id': campaign_id,
            'name': campaign_name,
            'status': status,
            'campaign_type': campaign_type,
            'advertising_channel_type': advertising_channel_map[campaign_type],
            'start_date': campaign_start.date(),
            'end_date': campaign_end.date(),
            'budget_amount': daily_budget,  # In dollars
            'target_cpa': round(random.uniform(20, 100), 2) if bidding_strategy == 'TARGET_CPA' else None,  # In dollars
            'impressions': impressions,
            'clicks': clicks,
            'cost': round(total_spend, 2),  # In dollars
            'conversions': conversions
        }
        
        campaigns.append(campaign)
    
    return campaigns

def insert_google_campaigns(campaigns):
    """Insert Google campaigns into the database"""
    print(f"\nInserting {len(campaigns):,} campaigns into database...")
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        inserted = db_helper.bulk_insert('google_ads_campaigns', batch)
        total_inserted += inserted
        
        if (i + batch_size) % 2000 == 0:
            print(f"  Inserted {i + batch_size:,} records...")
    
    return total_inserted

def verify_google_campaigns():
    """Verify the inserted campaigns"""
    count = db_helper.get_row_count('google_ads_campaigns')
    print(f"\n✓ Verification: {count:,} campaigns in database")
    
    # Show campaign type distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                campaign_type,
                COUNT(*) as count,
                AVG(cost) as avg_cost,
                SUM(conversions) as total_conversions
            FROM raw.google_ads_campaigns
            GROUP BY campaign_type
            ORDER BY count DESC
        """)
        type_dist = cursor.fetchall()
        
        print("\nCampaign type distribution:")
        for row in type_dist:
            print(f"  {row['campaign_type']}: {row['count']:,} campaigns, ${row['avg_cost']:,.2f} avg cost, {row['total_conversions']:,} conversions")
        
        # Show status summary
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as campaigns,
                SUM(cost) as total_cost,
                AVG(CASE WHEN clicks > 0 THEN conversions::float / clicks * 100 ELSE 0 END) as avg_conv_rate
            FROM raw.google_ads_campaigns
            GROUP BY status
            ORDER BY campaigns DESC
        """)
        status_summary = cursor.fetchall()
        
        print("\nCampaign status summary:")
        for row in status_summary:
            print(f"  {row['status']}: {row['campaigns']:,} campaigns, ${row['total_cost']:,.2f} total cost, {row['avg_conv_rate']:.2f}% conv rate")

def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Google Ads campaigns data')
    parser.add_argument('--force', action='store_true', 
                        help='Force regeneration without prompting')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Google Ads Campaign Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if campaigns already exist
    existing_count = db_helper.get_row_count('google_ads_campaigns')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} campaigns already exist")
        if args.force:
            print("Force flag set - truncating existing data...")
            db_helper.truncate_table('google_ads_campaigns')
        else:
            response = input("Do you want to truncate and regenerate? (y/N): ")
            if response.lower() == 'y':
                db_helper.truncate_table('google_ads_campaigns')
            else:
                print("Aborting...")
                return
    
    # Generate campaigns
    campaigns = generate_google_campaigns()
    
    # Insert into database
    inserted = insert_google_campaigns(campaigns)
    
    # Verify
    verify_google_campaigns()
    
    print(f"\n✅ Successfully generated {inserted:,} Google Ads campaigns!")

if __name__ == "__main__":
    main()