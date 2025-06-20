#!/usr/bin/env python3
"""
Generate synthetic marketing campaigns data for the bar management SaaS platform.

This script creates:
- 25 campaigns across Google Ads, Facebook, LinkedIn, and Email
- Proper date ranges and budgets
- Platform-specific attributes
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def generate_campaign_id(platform):
    """Generate platform-specific campaign ID."""
    if platform == 'google':
        return f"GA_{fake.random_int(min=1000000000, max=9999999999)}"
    elif platform == 'facebook':
        return f"FB_{fake.random_int(min=1000000000, max=9999999999)}"
    elif platform == 'linkedin':
        return f"LI_{fake.random_int(min=1000000000, max=9999999999)}"
    else:  # iterable
        return f"IT_{fake.random_int(min=100000, max=999999)}"

def generate_google_ads_campaigns(num_campaigns=10):
    """Generate Google Ads campaigns."""
    campaigns = []
    
    campaign_types = [
        {'type': 'SEARCH', 'channel': 'SEARCH', 'objectives': ['Lead Generation', 'Brand Awareness']},
        {'type': 'DISPLAY', 'channel': 'DISPLAY', 'objectives': ['Remarketing', 'Brand Awareness']},
        {'type': 'VIDEO', 'channel': 'VIDEO', 'objectives': ['Brand Awareness', 'Product Launch']},
        {'type': 'SHOPPING', 'channel': 'SHOPPING', 'objectives': ['Sales', 'Product Promotion']}
    ]
    
    campaign_names = [
        "Bar Management - Search - {objective}",
        "Tap System - {objective} - {region}",
        "Restaurant POS - {objective}",
        "Happy Hour Analytics - {objective}",
        "Inventory Management - {objective} - {season}"
    ]
    
    regions = ['US', 'Northeast', 'West Coast', 'Midwest', 'South']
    seasons = ['Q1', 'Q2', 'Q3', 'Q4', 'Spring', 'Summer', 'Fall', 'Winter']
    
    for i in range(num_campaigns):
        campaign_id = generate_campaign_id('google')
        campaign_type_info = fake.random_element(campaign_types)
        objective = fake.random_element(campaign_type_info['objectives'])
        
        # Generate campaign name
        name_template = fake.random_element(campaign_names)
        name = name_template.format(
            objective=objective,
            region=fake.random_element(regions),
            season=fake.random_element(seasons)
        )
        
        # Determine campaign dates and status
        if i < 6:  # 60% active campaigns
            start_date = datetime.now() - timedelta(days=fake.random_int(min=30, max=180))
            end_date = datetime.now() + timedelta(days=fake.random_int(min=30, max=180))
            status = 'ENABLED'
        elif i < 8:  # 20% paused campaigns
            start_date = datetime.now() - timedelta(days=fake.random_int(min=60, max=360))
            end_date = datetime.now() + timedelta(days=fake.random_int(min=30, max=90))
            status = 'PAUSED'
        else:  # 20% ended campaigns
            start_date = datetime.now() - timedelta(days=fake.random_int(min=180, max=540))
            end_date = datetime.now() - timedelta(days=fake.random_int(min=1, max=60))
            status = 'ENDED'
        
        # Budget based on campaign type
        if campaign_type_info['type'] == 'SEARCH':
            daily_budget = fake.random_int(min=50, max=500)
        elif campaign_type_info['type'] == 'DISPLAY':
            daily_budget = fake.random_int(min=30, max=300)
        elif campaign_type_info['type'] == 'VIDEO':
            daily_budget = fake.random_int(min=100, max=1000)
        else:  # SHOPPING
            daily_budget = fake.random_int(min=40, max=400)
        
        # Calculate total budget
        campaign_days = (end_date - start_date).days
        total_budget = daily_budget * campaign_days
        
        # Performance metrics (for active/ended campaigns)
        if status != 'PAUSED':
            days_running = min((datetime.now() - start_date).days, campaign_days)
            impressions = fake.random_int(min=1000, max=50000) * days_running
            ctr = fake.random_int(min=1, max=5) / 100  # 1-5% CTR
            clicks = int(impressions * ctr)
            cpc = fake.random_int(min=50, max=500) / 100  # $0.50-$5.00 CPC
            cost = clicks * cpc
            conversion_rate = fake.random_int(min=2, max=10) / 100  # 2-10% conversion
            conversions = int(clicks * conversion_rate)
        else:
            impressions = 0
            clicks = 0
            cost = 0
            conversions = 0
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'status': status,
            'campaign_type': campaign_type_info['type'],
            'advertising_channel_type': campaign_type_info['channel'],
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'budget_amount': float(total_budget),
            'target_cpa': float(fake.random_int(min=20, max=100)),
            'impressions': impressions,
            'clicks': clicks,
            'cost': float(cost),
            'conversions': conversions,
            'created_at': start_date.isoformat()
        }
        
        campaigns.append(campaign)
    
    return campaigns

def generate_facebook_ads_campaigns(num_campaigns=6):
    """Generate Facebook Ads campaigns."""
    campaigns = []
    
    objectives = [
        'CONVERSIONS',
        'BRAND_AWARENESS', 
        'REACH',
        'TRAFFIC',
        'ENGAGEMENT',
        'LEAD_GENERATION'
    ]
    
    campaign_names = [
        "Bar Owners - {objective} - {audience}",
        "Restaurant Tech - {objective}",
        "Tap Analytics - {objective} - {placement}",
        "Industry Event - {objective}",
        "Customer Success Stories - {objective}"
    ]
    
    audiences = ['Lookalike', 'Interest-Based', 'Retargeting', 'Custom']
    placements = ['Feed', 'Stories', 'Reels', 'All Placements']
    
    for i in range(num_campaigns):
        campaign_id = generate_campaign_id('facebook')
        objective = fake.random_element(objectives)
        
        # Generate campaign name
        name_template = fake.random_element(campaign_names)
        name = name_template.format(
            objective=objective.replace('_', ' ').title(),
            audience=fake.random_element(audiences),
            placement=fake.random_element(placements)
        )
        
        # Determine campaign dates and status
        if i < 4:  # Active campaigns
            start_time = datetime.now() - timedelta(days=fake.random_int(min=7, max=90))
            status = 'ACTIVE'
            end_time = None
        else:  # Completed campaigns
            start_time = datetime.now() - timedelta(days=fake.random_int(min=90, max=365))
            end_time = start_time + timedelta(days=fake.random_int(min=14, max=90))
            status = 'COMPLETED'
        
        # Budget
        if objective in ['CONVERSIONS', 'LEAD_GENERATION']:
            daily_budget = fake.random_int(min=50, max=300)
        else:
            daily_budget = fake.random_int(min=20, max=150)
        
        lifetime_budget = daily_budget * fake.random_int(min=30, max=180)
        
        # Performance metrics
        if status == 'ACTIVE':
            days_running = (datetime.now() - start_time).days
        else:
            days_running = (end_time - start_time).days
        
        impressions = fake.random_int(min=5000, max=100000) * days_running
        ctr = fake.random_int(min=5, max=30) / 1000  # 0.5-3% CTR
        clicks = int(impressions * ctr)
        cpm = fake.random_int(min=5, max=50)  # $5-$50 CPM
        spend = (impressions / 1000) * cpm
        
        # Actions (conversions, leads, etc.)
        actions = []
        if objective == 'CONVERSIONS':
            actions.append({
                'action_type': 'purchase',
                'value': fake.random_int(min=5, max=50)
            })
        elif objective == 'LEAD_GENERATION':
            actions.append({
                'action_type': 'leadgen.other',
                'value': fake.random_int(min=10, max=100)
            })
        elif objective == 'TRAFFIC':
            actions.append({
                'action_type': 'link_click',
                'value': clicks
            })
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'status': status,
            'objective': objective,
            'start_time': start_time.isoformat(),
            'stop_time': end_time.isoformat() if end_time else None,
            'daily_budget': float(daily_budget),
            'lifetime_budget': float(lifetime_budget),
            'impressions': impressions,
            'clicks': clicks,
            'spend': float(spend),
            'actions': json.dumps(actions) if actions else None,
            'created_time': start_time.isoformat(),
            'created_at': start_time.isoformat()
        }
        
        campaigns.append(campaign)
    
    return campaigns

def generate_linkedin_ads_campaigns(num_campaigns=5):
    """Generate LinkedIn Ads campaigns."""
    campaigns = []
    
    campaign_types = ['SPONSORED_CONTENT', 'TEXT_ADS', 'SPONSORED_INMAILS', 'DYNAMIC_ADS']
    objectives = ['BRAND_AWARENESS', 'WEBSITE_VISITS', 'ENGAGEMENT', 'LEAD_GENERATION', 'WEBSITE_CONVERSIONS']
    
    campaign_names = [
        "B2B Bar Tech - {objective}",
        "Restaurant Decision Makers - {type}",
        "Hospitality Leaders - {objective}",
        "Bar Management Innovation - {quarter}",
        "Industry Insights - {objective}"
    ]
    
    quarters = ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
    
    for i in range(num_campaigns):
        campaign_id = generate_campaign_id('linkedin')
        campaign_type = fake.random_element(campaign_types)
        objective = fake.random_element(objectives)
        
        # Generate campaign name
        name_template = fake.random_element(campaign_names)
        name = name_template.format(
            objective=objective.replace('_', ' ').title(),
            type=campaign_type.replace('_', ' ').title(),
            quarter=fake.random_element(quarters)
        )
        
        # Dates and status
        if i < 3:  # Active
            start_date = datetime.now() - timedelta(days=fake.random_int(min=14, max=120))
            end_date = datetime.now() + timedelta(days=fake.random_int(min=30, max=120))
            status = 'ACTIVE'
        else:  # Completed
            start_date = datetime.now() - timedelta(days=fake.random_int(min=120, max=365))
            end_date = start_date + timedelta(days=fake.random_int(min=30, max=90))
            status = 'COMPLETED'
        
        # Budget (LinkedIn is more expensive)
        daily_budget = fake.random_int(min=50, max=500)
        total_budget = daily_budget * (end_date - start_date).days
        
        # Performance
        if status == 'ACTIVE':
            days_running = (datetime.now() - start_date).days
        else:
            days_running = (end_date - start_date).days
        
        impressions = fake.random_int(min=1000, max=20000) * days_running
        ctr = fake.random_int(min=3, max=10) / 1000  # 0.3-1% CTR (lower for LinkedIn)
        clicks = int(impressions * ctr)
        cpc = fake.random_int(min=300, max=1200) / 100  # $3-$12 CPC (higher for LinkedIn)
        cost = clicks * cpc
        
        if objective in ['LEAD_GENERATION', 'WEBSITE_CONVERSIONS']:
            conversion_rate = fake.random_int(min=5, max=15) / 100
            conversions = int(clicks * conversion_rate)
        else:
            conversions = 0
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'status': status,
            'campaign_type': campaign_type,
            'objective_type': objective,
            'created_time': start_date.isoformat(),
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'daily_budget': float(daily_budget),
            'total_budget': float(total_budget),
            'impressions': impressions,
            'clicks': clicks,
            'cost': float(cost),
            'conversions': conversions,
            'created_at': start_date.isoformat()
        }
        
        campaigns.append(campaign)
    
    return campaigns

def generate_iterable_campaigns(num_campaigns=4):
    """Generate Iterable email campaigns."""
    campaigns = []
    
    campaign_types = ['EMAIL', 'PUSH', 'SMS', 'IN_APP']
    message_mediums = ['EMAIL', 'PUSH_NOTIFICATION', 'SMS', 'IN_APP_MESSAGE']
    
    campaign_names = [
        "Monthly Product Update - {month}",
        "Feature Announcement - {feature}",
        "Customer Success Webinar - {topic}",
        "Industry Report - {quarter}"
    ]
    
    months = ['January', 'February', 'March', 'April', 'May', 'June']
    features = ['Inventory Sync', 'Real-time Analytics', 'Mobile App', 'API v2', 'Reporting']
    topics = ['Best Practices', 'ROI Optimization', 'Integration Tips', 'Advanced Features']
    
    for i in range(num_campaigns):
        campaign_id = generate_campaign_id('iterable')
        campaign_type = 'EMAIL'  # Mostly email for B2B
        
        # Generate campaign name
        name_template = fake.random_element(campaign_names)
        name = name_template.format(
            month=fake.random_element(months),
            feature=fake.random_element(features),
            topic=fake.random_element(topics),
            quarter=fake.random_element(['Q1', 'Q2', 'Q3', 'Q4'])
        )
        
        # Dates
        created_at = datetime.now() - timedelta(days=fake.random_int(min=1, max=180))
        updated_at = created_at + timedelta(hours=fake.random_int(min=1, max=48))
        
        # Status
        if (datetime.now() - created_at).days < 30:
            status = 'Running'
        else:
            status = 'Finished'
        
        # Send size (based on customer base)
        send_size = fake.random_int(min=50, max=500)  # B2B has smaller lists
        
        # Labels
        labels = []
        if 'Product Update' in name:
            labels.append('product-updates')
        if 'Webinar' in name:
            labels.append('webinar')
        if 'Feature' in name:
            labels.append('feature-announcement')
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'campaign_type': campaign_type,
            'status': status,
            'created_at_source': created_at.isoformat(),
            'updated_at_source': updated_at.isoformat(),
            'send_size': send_size,
            'message_medium': 'EMAIL',
            'labels': json.dumps(labels) if labels else None,
            'start_at': created_at.isoformat(),
            'ended_at': (created_at + timedelta(hours=24)).isoformat() if status == 'Finished' else None,
            'created_at': created_at.isoformat()
        }
        
        campaigns.append(campaign)
    
    return campaigns

def save_campaigns_mapping(all_campaigns):
    """Save campaigns mapping for future reference."""
    mapping = {
        'google_ads': [],
        'facebook_ads': [],
        'linkedin_ads': [],
        'iterable': []
    }
    
    for platform, campaigns in all_campaigns.items():
        for campaign in campaigns:
            mapping[platform].append({
                'id': campaign['id'],
                'name': campaign['name'],
                'status': campaign['status'],
                'start_date': campaign.get('start_date') or campaign.get('start_time') or campaign.get('created_at'),
                'platform': platform
            })
    
    with open('data/marketing_campaigns_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved marketing campaigns mapping to data/marketing_campaigns_mapping.json")

def main():
    print("=== Generating Marketing Campaigns ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate campaigns for each platform
    print("\nGenerating campaigns...")
    
    google_campaigns = generate_google_ads_campaigns(10)
    print(f"✓ Generated {len(google_campaigns)} Google Ads campaigns")
    
    facebook_campaigns = generate_facebook_ads_campaigns(6)
    print(f"✓ Generated {len(facebook_campaigns)} Facebook Ads campaigns")
    
    linkedin_campaigns = generate_linkedin_ads_campaigns(5)
    print(f"✓ Generated {len(linkedin_campaigns)} LinkedIn Ads campaigns")
    
    iterable_campaigns = generate_iterable_campaigns(4)
    print(f"✓ Generated {len(iterable_campaigns)} Iterable campaigns")
    
    total_campaigns = len(google_campaigns) + len(facebook_campaigns) + len(linkedin_campaigns) + len(iterable_campaigns)
    print(f"\n✓ Total campaigns generated: {total_campaigns}")
    
    # Insert into database
    print("\nInserting into database...")
    
    db_helper.bulk_insert('google_ads_campaigns', google_campaigns)
    print(f"✓ Inserted Google Ads campaigns")
    
    db_helper.bulk_insert('facebook_ads_campaigns', facebook_campaigns)
    print(f"✓ Inserted Facebook Ads campaigns")
    
    db_helper.bulk_insert('linkedin_ads_campaigns', linkedin_campaigns)
    print(f"✓ Inserted LinkedIn Ads campaigns")
    
    db_helper.bulk_insert('iterable_campaigns', iterable_campaigns)
    print(f"✓ Inserted Iterable campaigns")
    
    # Save mapping
    all_campaigns = {
        'google_ads': google_campaigns,
        'facebook_ads': facebook_campaigns,
        'linkedin_ads': linkedin_campaigns,
        'iterable': iterable_campaigns
    }
    save_campaigns_mapping(all_campaigns)
    
    # Show summary
    print("\nCampaign Summary:")
    print(f"  - Google Ads: {len(google_campaigns)} campaigns")
    print(f"  - Facebook Ads: {len(facebook_campaigns)} campaigns")
    print(f"  - LinkedIn Ads: {len(linkedin_campaigns)} campaigns")
    print(f"  - Iterable: {len(iterable_campaigns)} campaigns")
    
    # Calculate total spend
    total_spend = 0
    for c in google_campaigns:
        total_spend += c.get('cost', 0)
    for c in facebook_campaigns:
        total_spend += c.get('spend', 0)
    for c in linkedin_campaigns:
        total_spend += c.get('cost', 0)
    
    print(f"\nTotal advertising spend: ${total_spend:,.2f}")

if __name__ == "__main__":
    main()