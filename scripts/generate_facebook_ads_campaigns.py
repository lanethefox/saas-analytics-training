#!/usr/bin/env python3
"""
Generate synthetic Facebook Ads campaigns data for the bar management SaaS platform.

This module creates Facebook advertising campaign records with:
- Brand awareness campaigns
- Lead generation campaigns
- Conversion campaigns
- Realistic spend and performance metrics
"""

import sys
import os
import json
import random
import uuid
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
CAMPAIGN_OBJECTIVES = [
    ('BRAND_AWARENESS', 0.20),
    ('REACH', 0.15),
    ('TRAFFIC', 0.25),
    ('LEAD_GENERATION', 0.25),
    ('CONVERSIONS', 0.15)
]

CAMPAIGN_STATUS = [
    ('ACTIVE', 0.60),
    ('PAUSED', 0.20),
    ('COMPLETED', 0.15),
    ('DRAFT', 0.05)
]

# Industry-specific ad copy templates
AD_TEMPLATES = {
    'BRAND_AWARENESS': [
        "Revolutionize Your Bar Management with {company}",
        "The Future of Hospitality Management is Here",
        "Join {count}+ Bars Using Smart Management Solutions"
    ],
    'LEAD_GENERATION': [
        "Free Demo: See How {company} Transforms Bar Operations",
        "Get Your Custom Bar Management Solution Quote",
        "Download: The Ultimate Guide to Modern Bar Management"
    ],
    'CONVERSIONS': [
        "Start Your 14-Day Free Trial Today",
        "Limited Time: 20% Off Annual Bar Management Plans",
        "Upgrade Your Bar Operations - Sign Up Now"
    ],
    'TRAFFIC': [
        "10 Ways Smart Bars Increase Revenue by 30%",
        "Case Study: How {bar} Saved 15 Hours Weekly",
        "New Features: Real-Time Inventory Tracking"
    ],
    'REACH': [
        "Bar Owners: This One Tool Changes Everything",
        "Why Smart Bars Choose {company}",
        "The #1 Bar Management Platform in {region}"
    ]
}

# Targeting parameters
TARGETING_INTERESTS = [
    'Bar Management',
    'Restaurant Management',
    'Hospitality Industry',
    'Small Business Owners',
    'Entrepreneurship',
    'Food & Beverage Industry',
    'Business Software',
    'Inventory Management'
]

TARGETING_BEHAVIORS = [
    'Small business owners',
    'Restaurant owners',
    'Bar owners',
    'Hospitality professionals',
    'Business decision makers'
]

def generate_facebook_campaigns():
    """Generate Facebook Ads campaigns"""
    campaigns = []
    
    # Calculate number of campaigns based on environment
    # Roughly 1 campaign per 20 accounts for realistic ratio
    num_campaigns = max(100, current_env.accounts // 20)
    
    print(f"Generating {num_campaigns:,} Facebook Ads campaigns...")
    
    # Time range for campaigns (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    for i in range(num_campaigns):
        campaign_id = f"fb_camp_{uuid.uuid4().hex[:12]}"
        
        # Campaign dates
        campaign_start = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days - 30)
        )
        campaign_end = campaign_start + timedelta(days=random.randint(7, 90))
        
        # Determine campaign objective and status
        objective = random.choices(
            [obj[0] for obj in CAMPAIGN_OBJECTIVES],
            [obj[1] for obj in CAMPAIGN_OBJECTIVES]
        )[0]
        
        # Status based on dates
        if campaign_end < datetime.now():
            status = 'COMPLETED'
        elif campaign_start > datetime.now():
            status = 'DRAFT'
        else:
            status = random.choices(
                ['ACTIVE', 'PAUSED'],
                [0.75, 0.25]
            )[0]
        
        # Budget and spend
        daily_budget = random.choice([50, 100, 150, 200, 250, 300, 500])
        lifetime_budget = daily_budget * (campaign_end - campaign_start).days
        
        # Calculate actual spend based on status
        if status == 'COMPLETED':
            spend_ratio = random.uniform(0.85, 0.98)
        elif status == 'ACTIVE':
            days_running = (datetime.now() - campaign_start).days
            spend_ratio = min(0.95, days_running / (campaign_end - campaign_start).days)
        else:
            spend_ratio = random.uniform(0.1, 0.3)
        
        total_spend = lifetime_budget * spend_ratio
        
        # Performance metrics based on objective
        if objective == 'BRAND_AWARENESS':
            impressions = int(total_spend * random.uniform(800, 1200))  # $0.83-1.25 CPM
            clicks = int(impressions * random.uniform(0.008, 0.015))    # 0.8-1.5% CTR
            conversions = 0
        elif objective == 'TRAFFIC':
            impressions = int(total_spend * random.uniform(600, 1000))
            clicks = int(impressions * random.uniform(0.015, 0.025))    # 1.5-2.5% CTR
            conversions = int(clicks * random.uniform(0.02, 0.05))      # 2-5% conversion
        elif objective == 'LEAD_GENERATION':
            impressions = int(total_spend * random.uniform(400, 800))
            clicks = int(impressions * random.uniform(0.02, 0.04))      # 2-4% CTR
            conversions = int(clicks * random.uniform(0.15, 0.25))      # 15-25% conversion
        elif objective == 'CONVERSIONS':
            impressions = int(total_spend * random.uniform(300, 600))
            clicks = int(impressions * random.uniform(0.025, 0.045))    # 2.5-4.5% CTR
            conversions = int(clicks * random.uniform(0.08, 0.15))      # 8-15% conversion
        else:  # REACH
            impressions = int(total_spend * random.uniform(1000, 1500))
            clicks = int(impressions * random.uniform(0.005, 0.01))     # 0.5-1% CTR
            conversions = 0
        
        # Generate campaign name
        campaign_name = f"{objective.replace('_', ' ').title()} - {fake.bs().title()} - {campaign_start.strftime('%b %Y')}"
        
        # Targeting
        targeting = {
            'age_min': random.choice([25, 30, 35]),
            'age_max': random.choice([55, 60, 65]),
            'genders': random.choice([['all'], ['male'], ['female'], ['all']]),
            'locations': {
                'countries': ['US'],
                'regions': random.sample(['CA', 'TX', 'NY', 'FL', 'IL', 'PA'], k=random.randint(2, 5))
            },
            'interests': random.sample(TARGETING_INTERESTS, k=random.randint(3, 5)),
            'behaviors': random.sample(TARGETING_BEHAVIORS, k=random.randint(2, 3))
        }
        
        campaign = {
            'id': campaign_id,
            'name': campaign_name,
            'objective': objective,
            'status': status,
            'created_time': campaign_start,
            'updated_time': campaign_start + timedelta(days=random.randint(0, 7)),
            'start_time': campaign_start,
            'stop_time': campaign_end,
            'daily_budget': daily_budget * 100,  # Store in cents
            'lifetime_budget': lifetime_budget * 100,
            'spend_cap': (lifetime_budget * 1.1) * 100,  # 10% above lifetime budget
            'currency': 'USD',
            'time_zone': 'America/New_York',
            'targeting': json.dumps(targeting),
            'bid_strategy': random.choice(['LOWEST_COST', 'COST_CAP', 'BID_CAP']),
            'attribution_setting': json.dumps({
                'click_lookback_window': 7,
                'view_lookback_window': 1
            }),
            'optimization_goal': random.choice(['IMPRESSIONS', 'LINK_CLICKS', 'CONVERSIONS']),
            'pixel_id': f"px_{random.randint(100000, 999999)}",
            'account_id': f"act_{random.randint(100000, 999999)}",
            'impressions': impressions,
            'clicks': clicks,
            'spend': int(total_spend * 100),  # Store in cents
            'reach': int(impressions * random.uniform(0.6, 0.8)),  # 60-80% unique reach
            'frequency': round(random.uniform(1.2, 2.5), 2),
            'cpm': round(total_spend / impressions * 1000, 2) if impressions > 0 else 0,
            'cpc': round(total_spend / clicks, 2) if clicks > 0 else 0,
            'ctr': round(clicks / impressions * 100, 2) if impressions > 0 else 0,
            'conversions': conversions,
            'conversion_rate': round(conversions / clicks * 100, 2) if clicks > 0 else 0,
            'cost_per_conversion': round(total_spend / conversions, 2) if conversions > 0 else 0
        }
        
        campaigns.append(campaign)
    
    return campaigns

def insert_facebook_campaigns(campaigns):
    """Insert Facebook campaigns into the database"""
    print(f"\nInserting {len(campaigns):,} campaigns into database...")
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        inserted = db_helper.bulk_insert('facebook_ads_campaigns', batch)
        total_inserted += inserted
        
        if (i + batch_size) % 2000 == 0:
            print(f"  Inserted {i + batch_size:,} records...")
    
    return total_inserted

def verify_facebook_campaigns():
    """Verify the inserted campaigns"""
    count = db_helper.get_row_count('facebook_ads_campaigns')
    print(f"\n✓ Verification: {count:,} campaigns in database")
    
    # Show objective distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                objective,
                COUNT(*) as count,
                AVG(spend/100.0) as avg_spend,
                SUM(conversions) as total_conversions
            FROM raw.facebook_ads_campaigns
            GROUP BY objective
            ORDER BY count DESC
        """)
        obj_dist = cursor.fetchall()
        
        print("\nCampaign objective distribution:")
        for row in obj_dist:
            print(f"  {row['objective']}: {row['count']:,} campaigns, ${row['avg_spend']:,.2f} avg spend, {row['total_conversions']:,} conversions")
        
        # Show performance summary
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as campaigns,
                SUM(spend)/100.0 as total_spend,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                AVG(ctr) as avg_ctr
            FROM raw.facebook_ads_campaigns
            GROUP BY status
            ORDER BY campaigns DESC
        """)
        status_summary = cursor.fetchall()
        
        print("\nCampaign status summary:")
        for row in status_summary:
            print(f"  {row['status']}: {row['campaigns']:,} campaigns, ${row['total_spend']:,.2f} spend, {row['avg_ctr']:.2f}% CTR")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Facebook Ads Campaign Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if campaigns already exist
    existing_count = db_helper.get_row_count('facebook_ads_campaigns')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} campaigns already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('facebook_ads_campaigns')
        else:
            print("Aborting...")
            return
    
    # Generate campaigns
    campaigns = generate_facebook_campaigns()
    
    # Insert into database
    inserted = insert_facebook_campaigns(campaigns)
    
    # Verify
    verify_facebook_campaigns()
    
    print(f"\n✅ Successfully generated {inserted:,} Facebook Ads campaigns!")

if __name__ == "__main__":
    main()