#!/usr/bin/env python3
"""
Generate synthetic LinkedIn Ads campaigns data for the bar management SaaS platform.

This module creates LinkedIn advertising campaign records with:
- Sponsored Content campaigns
- Message Ads campaigns  
- Text Ads campaigns
- B2B focused targeting
- Professional audience metrics
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
    ('BRAND_AWARENESS', 0.15),
    ('WEBSITE_VISITS', 0.25),
    ('ENGAGEMENT', 0.20),
    ('LEAD_GENERATION', 0.30),
    ('WEBSITE_CONVERSIONS', 0.10)
]

CAMPAIGN_FORMATS = [
    ('SPONSORED_CONTENT', 0.50),
    ('MESSAGE_ADS', 0.20),
    ('TEXT_ADS', 0.15),
    ('DYNAMIC_ADS', 0.10),
    ('VIDEO_ADS', 0.05)
]

# B2B targeting criteria
JOB_TITLES = [
    'Bar Owner', 'Restaurant Owner', 'Bar Manager', 
    'Restaurant Manager', 'Hospitality Manager',
    'General Manager', 'Operations Manager',
    'F&B Manager', 'Beverage Director',
    'Business Owner', 'CEO', 'COO'
]

JOB_FUNCTIONS = [
    'Business Development',
    'Operations', 
    'Management',
    'Entrepreneurship',
    'Purchasing',
    'Administrative'
]

JOB_SENIORITIES = [
    'Owner',
    'C-Level',
    'Director',
    'Manager',
    'Senior'
]

COMPANY_SIZES = [
    '1-10 employees',
    '11-50 employees',
    '51-200 employees',
    '201-500 employees',
    '501-1000 employees'
]

INDUSTRIES = [
    'Restaurants',
    'Food & Beverages',
    'Hospitality',
    'Entertainment',
    'Retail',
    'Wine & Spirits'
]

# Ad content templates
AD_TEMPLATES = {
    'LEAD_GENERATION': [
        "📊 See How {count}+ Bars Increased Revenue by 25%",
        "Free Guide: Modern Bar Management Best Practices",
        "Calculate Your Bar's Potential Savings →"
    ],
    'WEBSITE_CONVERSIONS': [
        "Transform Your Bar Operations in 14 Days",
        "Join Industry Leaders Using Smart Bar Tech",
        "Limited Offer: 30% Off Annual Plans"
    ],
    'BRAND_AWARENESS': [
        "The Future of Bar Management is Here",
        "Why Smart Bars Choose Automated Solutions",
        "Innovation in Hospitality Technology"
    ],
    'ENGAGEMENT': [
        "What's Your Biggest Bar Management Challenge?",
        "Poll: How Do You Track Inventory?",
        "Share Your Bar Success Story"
    ],
    'WEBSITE_VISITS': [
        "Discover 5 Ways to Optimize Bar Profits",
        "New: Real-Time Analytics Dashboard",
        "Case Study: 40% Reduction in Waste"
    ]
}

def generate_linkedin_campaigns():
    """Generate LinkedIn Ads campaigns"""
    campaigns = []
    
    # Calculate number of campaigns based on environment
    # Roughly 1 campaign per 30 accounts for realistic B2B ratio
    num_campaigns = max(80, current_env.accounts // 30)
    
    print(f"Generating {num_campaigns:,} LinkedIn Ads campaigns...")
    
    # Time range for campaigns (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    for i in range(num_campaigns):
        campaign_id = f"li_camp_{uuid.uuid4().hex[:12]}"
        
        # Campaign dates
        campaign_start = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days - 30)
        )
        campaign_end = campaign_start + timedelta(days=random.randint(14, 120))
        
        # Determine campaign objective and format
        objective = random.choices(
            [obj[0] for obj in CAMPAIGN_OBJECTIVES],
            [obj[1] for obj in CAMPAIGN_OBJECTIVES]
        )[0]
        
        format_type = random.choices(
            [fmt[0] for fmt in CAMPAIGN_FORMATS],
            [fmt[1] for fmt in CAMPAIGN_FORMATS]
        )[0]
        
        # Status based on dates
        if campaign_end < datetime.now():
            status = 'COMPLETED'
        elif campaign_start > datetime.now():
            status = 'DRAFT'
        else:
            status = random.choices(
                ['ACTIVE', 'PAUSED'],
                [0.70, 0.30]
            )[0]
        
        # Budget (LinkedIn tends to be more expensive)
        daily_budget = random.choice([75, 100, 150, 200, 300, 400, 500])
        total_budget = daily_budget * (campaign_end - campaign_start).days
        
        # Calculate actual spend based on status
        if status == 'COMPLETED':
            spend_ratio = random.uniform(0.80, 0.95)
        elif status == 'ACTIVE':
            days_running = (datetime.now() - campaign_start).days
            spend_ratio = min(0.90, days_running / (campaign_end - campaign_start).days)
        else:
            spend_ratio = random.uniform(0.05, 0.25)
        
        total_spend = total_budget * spend_ratio
        
        # Performance metrics based on format (LinkedIn has lower volumes but higher quality)
        if format_type == 'SPONSORED_CONTENT':
            impressions = int(total_spend * random.uniform(50, 150))     # $6.67-20 CPM
            clicks = int(impressions * random.uniform(0.004, 0.008))     # 0.4-0.8% CTR
            conversions = int(clicks * random.uniform(0.10, 0.20))       # 10-20% conversion
        elif format_type == 'MESSAGE_ADS':
            impressions = int(total_spend * random.uniform(20, 50))      # $20-50 CPM
            clicks = int(impressions * random.uniform(0.03, 0.05))       # 3-5% CTR (opens)
            conversions = int(clicks * random.uniform(0.05, 0.15))       # 5-15% conversion
        elif format_type == 'TEXT_ADS':
            impressions = int(total_spend * random.uniform(200, 400))    # $2.50-5 CPM
            clicks = int(impressions * random.uniform(0.002, 0.004))     # 0.2-0.4% CTR
            conversions = int(clicks * random.uniform(0.08, 0.15))       # 8-15% conversion
        elif format_type == 'DYNAMIC_ADS':
            impressions = int(total_spend * random.uniform(80, 200))
            clicks = int(impressions * random.uniform(0.006, 0.012))     # 0.6-1.2% CTR
            conversions = int(clicks * random.uniform(0.12, 0.25))       # 12-25% conversion
        else:  # VIDEO_ADS
            impressions = int(total_spend * random.uniform(40, 100))     # $10-25 CPM
            clicks = int(impressions * random.uniform(0.008, 0.015))     # 0.8-1.5% CTR
            conversions = int(clicks * random.uniform(0.05, 0.10))       # 5-10% conversion
        
        # Generate campaign name
        campaign_name = f"{objective.replace('_', ' ').title()} - {format_type.replace('_', ' ').title()} - {campaign_start.strftime('%Q%q %Y')}"
        
        # B2B Targeting
        targeting = {
            'job_titles': random.sample(JOB_TITLES, k=random.randint(3, 6)),
            'job_functions': random.sample(JOB_FUNCTIONS, k=random.randint(2, 4)),
            'job_seniorities': random.sample(JOB_SENIORITIES, k=random.randint(2, 3)),
            'company_sizes': random.sample(COMPANY_SIZES, k=random.randint(2, 4)),
            'industries': random.sample(INDUSTRIES, k=random.randint(2, 4)),
            'locations': {
                'countries': ['United States'],
                'regions': random.sample([
                    'California', 'Texas', 'New York', 'Florida',
                    'Illinois', 'Pennsylvania', 'Ohio', 'Georgia'
                ], k=random.randint(3, 6))
            },
            'audience_expansion': random.choice([True, False]),
            'matched_audiences': []
        }
        
        # Engagement metrics
        social_actions = int(impressions * random.uniform(0.001, 0.003))  # Likes, shares, etc.
        
        campaign = {
            'id': campaign_id,
            'name': campaign_name,
            'objective': objective,
            'format': format_type,
            'status': status,
            'created_time': campaign_start,
            'updated_time': campaign_start + timedelta(days=random.randint(0, 7)),
            'start_date': campaign_start.date(),
            'end_date': campaign_end.date(),
            'daily_budget': daily_budget * 100,  # Store in cents
            'total_budget': total_budget * 100,
            'bid_type': random.choice(['AUTOMATED', 'CPM', 'CPC', 'CPV']),
            'bid_amount': random.randint(500, 2000),  # $5-20
            'currency': 'USD',
            'time_zone': 'America/New_York',
            'targeting': json.dumps(targeting),
            'creative_type': format_type,
            'impressions': impressions,
            'clicks': clicks,
            'spend': int(total_spend * 100),  # Store in cents
            'reach': int(impressions * random.uniform(0.4, 0.6)),  # 40-60% unique reach
            'frequency': round(random.uniform(1.5, 3.0), 2),
            'conversions': conversions,
            'conversion_rate': round(conversions / clicks * 100, 2) if clicks > 0 else 0,
            'cost_per_click': round(total_spend / clicks, 2) if clicks > 0 else 0,
            'cost_per_conversion': round(total_spend / conversions, 2) if conversions > 0 else 0,
            'cost_per_thousand': round(total_spend / impressions * 1000, 2) if impressions > 0 else 0,
            'click_through_rate': round(clicks / impressions * 100, 3) if impressions > 0 else 0,
            'social_actions': social_actions,
            'engagement_rate': round(social_actions / impressions * 100, 3) if impressions > 0 else 0,
            'video_views': int(impressions * 0.3) if format_type == 'VIDEO_ADS' else None,
            'video_completions': int(impressions * 0.1) if format_type == 'VIDEO_ADS' else None,
            'leads_generated': conversions if objective == 'LEAD_GENERATION' else 0,
            'lead_form_completion_rate': round(random.uniform(0.15, 0.35), 3) if objective == 'LEAD_GENERATION' else None,
            'message_sends': clicks if format_type == 'MESSAGE_ADS' else 0,
            'message_opens': int(clicks * 0.7) if format_type == 'MESSAGE_ADS' else 0
        }
        
        campaigns.append(campaign)
    
    return campaigns

def insert_linkedin_campaigns(campaigns):
    """Insert LinkedIn campaigns into the database"""
    print(f"\nInserting {len(campaigns):,} campaigns into database...")
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        inserted = db_helper.bulk_insert('linkedin_ads_campaigns', batch)
        total_inserted += inserted
        
        if (i + batch_size) % 2000 == 0:
            print(f"  Inserted {i + batch_size:,} records...")
    
    return total_inserted

def verify_linkedin_campaigns():
    """Verify the inserted campaigns"""
    count = db_helper.get_row_count('linkedin_ads_campaigns')
    print(f"\n✓ Verification: {count:,} campaigns in database")
    
    # Show objective distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                objective,
                COUNT(*) as count,
                AVG(spend/100.0) as avg_spend,
                AVG(cost_per_conversion/100.0) as avg_cpc,
                SUM(conversions) as total_conversions
            FROM raw.linkedin_ads_campaigns
            GROUP BY objective
            ORDER BY count DESC
        """)
        obj_dist = cursor.fetchall()
        
        print("\nCampaign objective distribution:")
        for row in obj_dist:
            cpc = row['avg_cpc'] if row['avg_cpc'] else 0
            print(f"  {row['objective']}: {row['count']:,} campaigns, ${row['avg_spend']:,.2f} avg spend, ${cpc:.2f} avg CPC, {row['total_conversions']:,} conversions")
        
        # Show format performance
        cursor.execute("""
            SELECT 
                format,
                COUNT(*) as campaigns,
                AVG(click_through_rate) as avg_ctr,
                AVG(conversion_rate) as avg_conv_rate,
                SUM(leads_generated) as total_leads
            FROM raw.linkedin_ads_campaigns
            GROUP BY format
            ORDER BY campaigns DESC
        """)
        format_summary = cursor.fetchall()
        
        print("\nCampaign format performance:")
        for row in format_summary:
            print(f"  {row['format']}: {row['campaigns']:,} campaigns, {row['avg_ctr']:.3f}% CTR, {row['avg_conv_rate']:.2f}% conv rate, {row['total_leads']:,} leads")

def main():
    """Main execution function"""
    print("=" * 60)
    print("LinkedIn Ads Campaign Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if campaigns already exist
    existing_count = db_helper.get_row_count('linkedin_ads_campaigns')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} campaigns already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('linkedin_ads_campaigns')
        else:
            print("Aborting...")
            return
    
    # Generate campaigns
    campaigns = generate_linkedin_campaigns()
    
    # Insert into database
    inserted = insert_linkedin_campaigns(campaigns)
    
    # Verify
    verify_linkedin_campaigns()
    
    print(f"\n✅ Successfully generated {inserted:,} LinkedIn Ads campaigns!")

if __name__ == "__main__":
    main()