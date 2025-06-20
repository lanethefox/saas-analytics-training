#!/usr/bin/env python3
"""
Generate synthetic HubSpot deals data for the bar management SaaS platform.

This script creates:
- 250 deals with sales pipeline progression
- Win rate 25%
- Deal values correlated with company size
- Stage duration patterns
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

def load_hubspot_companies():
    """Load existing HubSpot companies mapping."""
    with open('data/hubspot_companies_mapping.json', 'r') as f:
        return json.load(f)

def load_hubspot_contacts():
    """Load existing HubSpot contacts mapping."""
    with open('data/hubspot_contacts_mapping.json', 'r') as f:
        return json.load(f)

def generate_hubspot_deals(env_config):
    """Generate HubSpot deals data."""
    deals = []
    companies = load_hubspot_companies()
    contacts = load_hubspot_contacts()
    
    # Deal stages and their typical durations (days)
    pipeline_stages = {
        'appointmentscheduled': {'duration': 1, 'win_probability': 0.10},
        'qualifiedtobuy': {'duration': 3, 'win_probability': 0.20},
        'presentationscheduled': {'duration': 5, 'win_probability': 0.40},
        'decisionmakerboughtin': {'duration': 7, 'win_probability': 0.60},
        'contractsent': {'duration': 3, 'win_probability': 0.80},
        'closedwon': {'duration': 1, 'win_probability': 1.00},
        'closedlost': {'duration': 1, 'win_probability': 0.00}
    }
    
    # Create deals for customers (historical won deals)
    customer_companies = [c for c in companies if c['lifecycle_stage'] == 'customer']
    for company in customer_companies:
        deal_id = str(uuid.uuid4())
        
        # Get primary contact for this company
        company_contacts = [c for c in contacts if c['company_id'] == company['id']]
        primary_contact = company_contacts[0] if company_contacts else None
        
        # Deal amount based on tier
        tier = company['industry']
        if 'Hotel' in tier:
            base_amount = fake.random_int(min=5000, max=15000)
        elif 'Restaurant' in tier:
            base_amount = fake.random_int(min=3000, max=8000)
        else:
            base_amount = fake.random_int(min=2000, max=6000)
        
        # Add variations based on locations
        location_multiplier = 1 + (fake.random_int(1, 5) * 0.1)
        deal_amount = base_amount * location_multiplier
        
        # Historical deal - closed 1-5 years ago
        days_ago = fake.random_int(min=365, max=1825)
        close_date = datetime.now() - timedelta(days=days_ago)
        
        # Work backwards from close date through stages
        create_date = close_date - timedelta(days=30)  # Average sales cycle
        
        # Build associations
        associations = {
            'company_ids': [company['id']],
            'contact_ids': [primary_contact['id']] if primary_contact else []
        }
        
        # Build properties
        properties = {
            'dealtype': 'newbusiness',
            'description': f"New customer acquisition - {company['name']}",
            'hubspot_owner_id': fake.random_element(['1', '2', '3', '4', '5']),  # 5 sales reps
            'num_notes': fake.random_int(min=5, max=20),
            'num_meetings': fake.random_int(min=2, max=5),
            'hs_priority': 'medium',
            'hs_deal_stage_probability': 1.0,
            'days_to_close': (close_date - create_date).days,
            'closed_won_reason': fake.random_element(['Good fit', 'Strong ROI case', 'Competitive pricing']),
            'competitor': fake.random_element(['None', 'Competitor A', 'Competitor B', 'Manual Process'])
        }
        
        deal = {
            'id': deal_id,
            'properties': json.dumps(properties),
            'associations': json.dumps(associations),
            'dealname': f"{company['name']} - New System",
            'amount': float(deal_amount),
            'dealstage': 'closedwon',
            'pipeline': 'default',
            'closedate': close_date.date().isoformat(),
            'createdat': create_date.isoformat(),
            'updatedat': close_date.isoformat(),
            'archived': False,
            'created_at': create_date.isoformat()
        }
        
        deals.append(deal)
    
    # Create active deals for prospects and expansion opportunities
    # Prospects
    prospect_companies = [c for c in companies if c['lifecycle_stage'] != 'customer']
    num_prospect_deals = min(len(prospect_companies), 50)  # Up to 50 prospect deals
    
    for company in prospect_companies[:num_prospect_deals]:
        deal_id = str(uuid.uuid4())
        
        # Get contacts
        company_contacts = [c for c in contacts if c['company_id'] == company['id']]
        primary_contact = company_contacts[0] if company_contacts else None
        
        # Deal amount
        base_amount = fake.random_int(min=2000, max=10000)
        
        # Current stage (weighted towards early stages)
        stage = fake.random_element(elements=(
            'appointmentscheduled', 'appointmentscheduled',
            'qualifiedtobuy', 'qualifiedtobuy', 'qualifiedtobuy',
            'presentationscheduled', 'presentationscheduled',
            'decisionmakerboughtin',
            'contractsent',
            'closedlost', 'closedlost'
        ))
        
        # Calculate dates based on stage
        create_date = datetime.now() - timedelta(days=fake.random_int(min=1, max=60))
        if stage == 'closedlost':
            close_date = create_date + timedelta(days=fake.random_int(min=10, max=30))
            is_closed = True
        elif stage == 'closedwon':
            close_date = create_date + timedelta(days=fake.random_int(min=20, max=40))
            is_closed = True
        else:
            # Projected close date
            days_in_stage = fake.random_int(min=1, max=pipeline_stages[stage]['duration'])
            close_date = datetime.now() + timedelta(days=fake.random_int(min=7, max=45))
            is_closed = False
        
        # Build associations
        associations = {
            'company_ids': [company['id']],
            'contact_ids': [primary_contact['id']] if primary_contact else []
        }
        
        # Build properties
        properties = {
            'dealtype': 'newbusiness',
            'description': f"Prospective customer - {company['name']}",
            'hubspot_owner_id': fake.random_element(['1', '2', '3', '4', '5']),
            'num_notes': fake.random_int(min=1, max=10),
            'num_meetings': fake.random_int(min=0, max=3),
            'hs_priority': fake.random_element(['low', 'medium', 'high']),
            'hs_deal_stage_probability': pipeline_stages[stage]['win_probability'],
            'next_step': fake.random_element(['Follow up call', 'Send proposal', 'Schedule demo', 'Get budget approval']),
            'competitor': fake.random_element(['Competitor A', 'Competitor B', 'Manual Process', 'None'])
        }
        
        if stage == 'closedlost':
            properties['closed_lost_reason'] = fake.random_element([
                'Budget', 'Timing', 'Competitor', 'No decision', 'Poor fit'
            ])
        
        deal = {
            'id': deal_id,
            'properties': json.dumps(properties),
            'associations': json.dumps(associations),
            'dealname': f"{company['name']} - Opportunity",
            'amount': float(base_amount),
            'dealstage': stage,
            'pipeline': 'default',
            'closedate': close_date.date().isoformat(),
            'createdat': create_date.isoformat(),
            'updatedat': datetime.now().isoformat(),
            'archived': is_closed,
            'created_at': create_date.isoformat()
        }
        
        deals.append(deal)
    
    # Create expansion deals for existing customers (upsell/cross-sell)
    num_expansion_deals = 250 - len(deals)  # Fill to 250 total
    expansion_customers = fake.random_elements(
        elements=customer_companies,
        length=min(num_expansion_deals, len(customer_companies)),
        unique=True
    )
    
    for company in expansion_customers:
        if len(deals) >= 250:
            break
            
        deal_id = str(uuid.uuid4())
        
        # Get contacts
        company_contacts = [c for c in contacts if c['company_id'] == company['id']]
        primary_contact = company_contacts[0] if company_contacts else None
        
        # Expansion deal amount (smaller than initial)
        base_amount = fake.random_int(min=1000, max=5000)
        
        # Stage
        stage = fake.random_element(elements=(
            'qualifiedtobuy', 'qualifiedtobuy',
            'presentationscheduled', 'presentationscheduled',
            'decisionmakerboughtin', 'decisionmakerboughtin',
            'contractsent',
            'closedwon',
            'closedlost'
        ))
        
        # Dates
        create_date = datetime.now() - timedelta(days=fake.random_int(min=1, max=30))
        if stage in ['closedwon', 'closedlost']:
            close_date = create_date + timedelta(days=fake.random_int(min=5, max=20))
            is_closed = True
        else:
            close_date = datetime.now() + timedelta(days=fake.random_int(min=7, max=30))
            is_closed = False
        
        # Build associations
        associations = {
            'company_ids': [company['id']],
            'contact_ids': [primary_contact['id']] if primary_contact else []
        }
        
        # Build properties
        properties = {
            'dealtype': 'existingbusiness',
            'description': f"Expansion opportunity - {company['name']}",
            'hubspot_owner_id': fake.random_element(['1', '2', '3', '4', '5']),
            'num_notes': fake.random_int(min=2, max=8),
            'num_meetings': fake.random_int(min=1, max=3),
            'hs_priority': 'high',  # Existing customers get high priority
            'hs_deal_stage_probability': pipeline_stages[stage]['win_probability'],
            'expansion_type': fake.random_element(['Add locations', 'Add devices', 'Upgrade tier', 'Add features'])
        }
        
        deal = {
            'id': deal_id,
            'properties': json.dumps(properties),
            'associations': json.dumps(associations),
            'dealname': f"{company['name']} - Expansion",
            'amount': float(base_amount),
            'dealstage': stage,
            'pipeline': 'default',
            'closedate': close_date.date().isoformat(),
            'createdat': create_date.isoformat(),
            'updatedat': datetime.now().isoformat(),
            'archived': is_closed,
            'created_at': create_date.isoformat()
        }
        
        deals.append(deal)
    
    return deals[:250]  # Ensure exactly 250 deals

def save_hubspot_deals_mapping(deals):
    """Save HubSpot deals mapping for future reference."""
    mapping = []
    for deal in deals:
        props = json.loads(deal['properties'])
        assocs = json.loads(deal['associations'])
        mapping.append({
            'id': deal['id'],
            'dealname': deal['dealname'],
            'amount': deal['amount'],
            'stage': deal['dealstage'],
            'company_ids': assocs.get('company_ids', []),
            'contact_ids': assocs.get('contact_ids', []),
            'dealtype': props.get('dealtype'),
            'closedate': deal['closedate']
        })
    
    with open('data/hubspot_deals_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved HubSpot deals mapping to data/hubspot_deals_mapping.json")

def main():
    print("=== Generating HubSpot Deals ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate deals
    print("\nGenerating HubSpot deals...")
    deals = generate_hubspot_deals(env_config)
    print(f"✓ Generated {len(deals)} HubSpot deals")
    
    # Show stage distribution
    stage_counts = {}
    for deal in deals:
        stage = deal['dealstage']
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    print("\nDeal stage distribution:")
    for stage, count in sorted(stage_counts.items()):
        percentage = (count / len(deals)) * 100
        print(f"  - {stage}: {count} ({percentage:.1f}%)")
    
    # Show type distribution
    type_counts = {}
    total_value = 0
    for deal in deals:
        deal_type = json.loads(deal['properties']).get('dealtype')
        type_counts[deal_type] = type_counts.get(deal_type, 0) + 1
        total_value += deal['amount']
    
    print("\nDeal type distribution:")
    for deal_type, count in sorted(type_counts.items()):
        print(f"  - {deal_type}: {count}")
    
    print(f"\nTotal deal value: ${total_value:,.2f}")
    print(f"Average deal value: ${total_value/len(deals):,.2f}")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('hubspot_deals', deals)
    
    # Save mapping
    save_hubspot_deals_mapping(deals)
    
    # Verify
    count = db_helper.get_row_count('hubspot_deals')
    print(f"\n✓ Total HubSpot deals in database: {count}")

if __name__ == "__main__":
    main()