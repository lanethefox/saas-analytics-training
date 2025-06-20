#!/usr/bin/env python3
"""
Generate synthetic Marketing Qualified Leads (MQLs) data for the bar management SaaS platform.

This script creates:
- 200 MQLs with lead scoring progression
- Source attribution
- Conversion funnel metrics
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_hubspot_contacts():
    """Load existing HubSpot contacts mapping."""
    with open('data/hubspot_contacts_mapping.json', 'r') as f:
        return json.load(f)

def load_campaigns_mapping():
    """Load existing campaigns mapping."""
    with open('data/marketing_campaigns_mapping.json', 'r') as f:
        return json.load(f)

def load_attribution_summary():
    """Load attribution touchpoints summary."""
    with open('data/attribution_touchpoints_summary.json', 'r') as f:
        return json.load(f)

def generate_marketing_qualified_leads(env_config):
    """Generate MQL data."""
    mqls = []
    contacts = load_hubspot_contacts()
    campaigns = load_campaigns_mapping()
    
    # Get prospect contacts (not yet customers)
    prospect_contacts = [c for c in contacts if c.get('lifecycle_stage') != 'customer']
    
    # Get contacts who eventually became customers
    customer_contacts = [c for c in contacts if c.get('lifecycle_stage') == 'customer']
    
    # MQL scoring criteria
    scoring_criteria = {
        'behavioral': {
            'website_visits': {'weight': 10, 'threshold': 5},
            'content_downloads': {'weight': 15, 'threshold': 2},
            'email_engagement': {'weight': 20, 'threshold': 3},
            'demo_request': {'weight': 30, 'threshold': 1},
            'pricing_page_view': {'weight': 25, 'threshold': 2}
        },
        'demographic': {
            'job_title_fit': {'weight': 20, 'range': [0, 1]},
            'company_size_fit': {'weight': 15, 'range': [0, 1]},
            'industry_fit': {'weight': 15, 'range': [0, 1]}
        }
    }
    
    # Lead sources
    lead_sources = {
        'Content Marketing': 0.25,
        'Paid Search': 0.20,
        'Social Media': 0.15,
        'Webinar': 0.15,
        'Trade Show': 0.10,
        'Partner Referral': 0.10,
        'Direct Traffic': 0.05
    }
    
    # First, generate MQLs from customer contacts (these converted)
    num_customer_mqls = min(100, len(customer_contacts))
    selected_customers = random.sample(customer_contacts, num_customer_mqls)
    
    for contact in selected_customers:
        mql_id = str(uuid.uuid4())
        
        # MQL date should be before they became a customer
        # Assume 30-90 days before deal close
        days_before_close = random.randint(30, 90)
        mql_date = datetime.now() - timedelta(days=random.randint(120, 500))
        
        # Calculate lead score (higher for those who converted)
        behavioral_score = 0
        for behavior, config in scoring_criteria['behavioral'].items():
            if behavior == 'demo_request':
                value = 1  # They all requested demos
            else:
                value = random.randint(config.get('threshold', 1), config.get('threshold', 1) * 3)
            behavioral_score += min(value * config['weight'] / config.get('threshold', 1), config['weight'])
        
        demographic_score = 0
        for demo, config in scoring_criteria['demographic'].items():
            score = random.uniform(0.7, 1.0)  # Good fit since they converted
            demographic_score += score * config['weight']
        
        total_score = behavioral_score + demographic_score
        mql_score = min(100, total_score)  # Cap at 100
        
        # Engagement score
        engagement_score = random.uniform(70, 95)
        
        # Lead source
        lead_source = random.choices(
            list(lead_sources.keys()),
            weights=list(lead_sources.values())
        )[0]
        
        # Campaign attribution
        campaign_id = None
        all_campaigns = []
        for platform_campaigns in campaigns.values():
            all_campaigns.extend(platform_campaigns)
        
        if lead_source in ['Paid Search', 'Social Media'] and all_campaigns:
            campaign = random.choice(all_campaigns)
            campaign_id = campaign['id']
        
        # Days to MQL (from first touch)
        days_to_mql = random.randint(7, 45)
        
        # Conversion probability (high for those who actually converted)
        conversion_probability = random.uniform(0.7, 0.95)
        
        mql = {
            'id': mql_id,
            'created_at_source': mql_date.isoformat(),
            'contact_id': random.randint(1, 1000000),  # Using integer ID as per schema
            'account_id': random.randint(1, 100),  # Account ID from 1-100
            'mql_date': mql_date.isoformat(),
            'mql_score': float(mql_score),
            'lead_source': lead_source,
            'campaign_id': campaign_id,
            'conversion_probability': float(conversion_probability),
            'days_to_mql': days_to_mql,
            'engagement_score': float(engagement_score),
            'created_at': mql_date.isoformat()
        }
        
        mqls.append(mql)
    
    # Then generate MQLs from prospects (may or may not convert)
    num_prospect_mqls = 200 - len(mqls)
    selected_prospects = random.sample(
        prospect_contacts, 
        min(num_prospect_mqls, len(prospect_contacts))
    )
    
    for contact in selected_prospects:
        mql_id = str(uuid.uuid4())
        
        # Recent MQLs
        mql_date = datetime.now() - timedelta(days=random.randint(1, 90))
        
        # Calculate lead score (more variable for prospects)
        behavioral_score = 0
        for behavior, config in scoring_criteria['behavioral'].items():
            if random.random() < 0.7:  # 70% chance of exhibiting behavior
                value = random.randint(1, config.get('threshold', 1) * 2)
                behavioral_score += min(value * config['weight'] / config.get('threshold', 1), config['weight'])
        
        demographic_score = 0
        for demo, config in scoring_criteria['demographic'].items():
            score = random.uniform(0.4, 0.9)
            demographic_score += score * config['weight']
        
        total_score = behavioral_score + demographic_score
        mql_score = min(100, total_score)
        
        # Engagement score (lower for prospects)
        engagement_score = random.uniform(40, 75)
        
        # Lead source
        lead_source = random.choices(
            list(lead_sources.keys()),
            weights=list(lead_sources.values())
        )[0]
        
        # Campaign attribution
        campaign_id = None
        all_campaigns = []
        for platform_campaigns in campaigns.values():
            all_campaigns.extend(platform_campaigns)
        
        if lead_source in ['Paid Search', 'Social Media', 'Content Marketing'] and all_campaigns:
            campaign = random.choice(all_campaigns)
            campaign_id = campaign['id']
        
        # Days to MQL
        days_to_mql = random.randint(14, 90)
        
        # Conversion probability (lower for prospects)
        conversion_probability = random.uniform(0.1, 0.6)
        
        mql = {
            'id': mql_id,
            'created_at_source': mql_date.isoformat(),
            'contact_id': random.randint(1, 1000000),
            'account_id': random.randint(101, 125),  # Prospect account IDs
            'mql_date': mql_date.isoformat(),
            'mql_score': float(mql_score),
            'lead_source': lead_source,
            'campaign_id': campaign_id,
            'conversion_probability': float(conversion_probability),
            'days_to_mql': days_to_mql,
            'engagement_score': float(engagement_score),
            'created_at': mql_date.isoformat()
        }
        
        mqls.append(mql)
    
    return mqls[:200]  # Ensure exactly 200

def update_attribution_touchpoints_with_mqls(mqls):
    """Update attribution touchpoints with MQL IDs."""
    print("\nLinking MQLs to attribution touchpoints...")
    
    # For now, we'll just note that in a real system, we would update
    # the attribution_touchpoints table to link MQLs to their touchpoints
    # This would involve updating records where the touchpoint led to an MQL
    
    mql_count = len(mqls)
    print(f"✓ Generated {mql_count} MQLs ready for attribution linking")

def save_mql_mapping(mqls):
    """Save MQL mapping for future reference."""
    summary = {
        'total_mqls': len(mqls),
        'lead_sources': {},
        'avg_mql_score': sum(m['mql_score'] for m in mqls) / len(mqls),
        'avg_days_to_mql': sum(m['days_to_mql'] for m in mqls) / len(mqls),
        'avg_conversion_probability': sum(m['conversion_probability'] for m in mqls) / len(mqls)
    }
    
    # Lead source distribution
    for mql in mqls:
        source = mql['lead_source']
        summary['lead_sources'][source] = summary['lead_sources'].get(source, 0) + 1
    
    # Save summary
    with open('data/mql_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save MQL IDs for future reference
    mql_mapping = [{
        'id': mql['id'],
        'contact_id': mql['contact_id'],
        'account_id': mql['account_id'],
        'mql_score': mql['mql_score'],
        'lead_source': mql['lead_source'],
        'conversion_probability': mql['conversion_probability']
    } for mql in mqls]
    
    with open('data/mql_mapping.json', 'w') as f:
        json.dump(mql_mapping, f, indent=2)
    
    print(f"✓ Saved MQL summary to data/mql_summary.json")
    print(f"✓ Saved MQL mapping to data/mql_mapping.json")

def main():
    print("=== Generating Marketing Qualified Leads ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate MQLs
    print("\nGenerating MQLs...")
    mqls = generate_marketing_qualified_leads(env_config)
    print(f"✓ Generated {len(mqls)} MQLs")
    
    # Show statistics
    avg_score = sum(m['mql_score'] for m in mqls) / len(mqls)
    avg_days = sum(m['days_to_mql'] for m in mqls) / len(mqls)
    avg_prob = sum(m['conversion_probability'] for m in mqls) / len(mqls)
    
    print(f"\nMQL Statistics:")
    print(f"  - Average MQL Score: {avg_score:.1f}")
    print(f"  - Average Days to MQL: {avg_days:.1f}")
    print(f"  - Average Conversion Probability: {avg_prob:.2%}")
    
    # Lead source distribution
    sources = {}
    for mql in mqls:
        source = mql['lead_source']
        sources[source] = sources.get(source, 0) + 1
    
    print("\nLead Source Distribution:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(mqls)) * 100
        print(f"  - {source}: {count} ({percentage:.1f}%)")
    
    # Score distribution
    high_score = len([m for m in mqls if m['mql_score'] >= 80])
    medium_score = len([m for m in mqls if 60 <= m['mql_score'] < 80])
    low_score = len([m for m in mqls if m['mql_score'] < 60])
    
    print(f"\nMQL Score Distribution:")
    print(f"  - High (80+): {high_score} ({high_score/len(mqls)*100:.1f}%)")
    print(f"  - Medium (60-79): {medium_score} ({medium_score/len(mqls)*100:.1f}%)")
    print(f"  - Low (<60): {low_score} ({low_score/len(mqls)*100:.1f}%)")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('marketing_qualified_leads', mqls)
    
    # Update attribution touchpoints
    update_attribution_touchpoints_with_mqls(mqls)
    
    # Save mapping
    save_mql_mapping(mqls)
    
    # Verify
    count = db_helper.get_row_count('marketing_qualified_leads')
    print(f"\n✓ Total MQLs in database: {count}")

if __name__ == "__main__":
    main()