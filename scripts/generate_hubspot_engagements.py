#!/usr/bin/env python3
"""
Generate synthetic HubSpot engagements data for the bar management SaaS platform.

This script creates:
- 2,500 engagements (calls, emails, meetings)
- Engagement frequency by deal stage
- Rep activity patterns
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

def load_hubspot_deals():
    """Load existing HubSpot deals mapping."""
    with open('data/hubspot_deals_mapping.json', 'r') as f:
        return json.load(f)

def load_hubspot_contacts():
    """Load existing HubSpot contacts mapping."""
    with open('data/hubspot_contacts_mapping.json', 'r') as f:
        return json.load(f)

def generate_hubspot_engagements(env_config):
    """Generate HubSpot engagements data."""
    engagements = []
    deals = load_hubspot_deals()
    contacts = load_hubspot_contacts()
    
    # Engagement types and their properties
    engagement_types = {
        'CALL': {
            'weight': 0.4,
            'avg_duration': 900,  # 15 minutes in seconds
            'outcomes': ['Connected', 'Left voicemail', 'No answer', 'Wrong number']
        },
        'EMAIL': {
            'weight': 0.4,
            'avg_duration': 0,
            'subject_templates': [
                'Follow up on our conversation',
                'Next steps for {company}',
                'Proposal for {company}',
                'Quick question about your requirements',
                'Checking in - {company}',
                'Re: Bar management system discussion'
            ]
        },
        'MEETING': {
            'weight': 0.2,
            'avg_duration': 3600,  # 60 minutes in seconds
            'meeting_types': ['Demo', 'Discovery call', 'Proposal review', 'Contract review', 'Check-in']
        }
    }
    
    # Sales rep names
    sales_reps = [
        {'id': '1', 'name': 'John Smith', 'email': 'john.smith@company.com'},
        {'id': '2', 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com'},
        {'id': '3', 'name': 'Mike Davis', 'email': 'mike.davis@company.com'},
        {'id': '4', 'name': 'Emily Brown', 'email': 'emily.brown@company.com'},
        {'id': '5', 'name': 'Chris Wilson', 'email': 'chris.wilson@company.com'}
    ]
    
    # Generate engagements for each deal
    for deal in deals:
        # Determine number of engagements based on deal stage
        deal_stage = deal['stage']
        if deal_stage == 'closedwon':
            num_engagements = fake.random_int(min=8, max=20)
        elif deal_stage == 'closedlost':
            num_engagements = fake.random_int(min=3, max=8)
        elif deal_stage in ['contractsent', 'decisionmakerboughtin']:
            num_engagements = fake.random_int(min=6, max=12)
        else:
            num_engagements = fake.random_int(min=2, max=6)
        
        # Get deal contacts
        deal_contact_ids = deal.get('contact_ids', [])
        if not deal_contact_ids:
            # Find contacts from the same company
            company_ids = deal.get('company_ids', [])
            if company_ids:
                deal_contacts = [c for c in contacts if c.get('company_id') in company_ids]
                deal_contact_ids = [c['id'] for c in deal_contacts[:2]]  # Max 2 contacts
        
        # Parse deal close date
        close_date = datetime.fromisoformat(deal['closedate'])
        
        # Generate engagements spread over the deal timeline
        for i in range(num_engagements):
            engagement_id = str(uuid.uuid4())
            
            # Select engagement type
            eng_type = fake.random_element(elements=list(engagement_types.keys()))
            
            # Calculate engagement date (spread throughout deal lifecycle)
            if deal_stage in ['closedwon', 'closedlost']:
                # Historical deal - engagements before close date
                days_before_close = fake.random_int(min=1, max=60)
                engagement_date = close_date - timedelta(days=days_before_close)
            else:
                # Active deal - recent engagements
                engagement_date = datetime.now() - timedelta(days=fake.random_int(min=0, max=30))
            
            # Select sales rep
            rep = fake.random_element(sales_reps)
            
            # Build engagement object
            engagement_obj = {
                'type': eng_type,
                'ownerId': rep['id'],
                'timestamp': int(engagement_date.timestamp() * 1000),  # Milliseconds
                'uid': f"{eng_type.lower()}-{engagement_id[:8]}",
                'portalId': '12345',
                'active': True,
                'createdAt': int(engagement_date.timestamp() * 1000),
                'lastUpdated': int((engagement_date + timedelta(hours=1)).timestamp() * 1000),
                'createdBy': rep['id'],
                'modifiedBy': rep['id']
            }
            
            # Build associations
            associations = {
                'contactIds': deal_contact_ids[:1] if deal_contact_ids else [],  # Primary contact
                'companyIds': deal.get('company_ids', []),
                'dealIds': [deal['id']]
            }
            
            # Build metadata based on type
            metadata = {}
            
            if eng_type == 'CALL':
                metadata = {
                    'toNumber': fake.phone_number(),
                    'fromNumber': fake.phone_number(),
                    'status': fake.random_element(['COMPLETED', 'COMPLETED', 'NO_ANSWER', 'BUSY']),
                    'durationMilliseconds': fake.random_int(min=30000, max=1800000),  # 30s to 30min
                    'recordingUrl': None,
                    'body': f"Call notes: {fake.random_element(engagement_types['CALL']['outcomes'])}. {fake.sentence()}",
                    'disposition': fake.random_element(['73857934', '73857935', '73857936'])  # Call outcome IDs
                }
            
            elif eng_type == 'EMAIL':
                company_name = deal.get('dealname', 'Company').split(' - ')[0]
                subject = fake.random_element(engagement_types['EMAIL']['subject_templates']).format(company=company_name)
                metadata = {
                    'from': {
                        'email': rep['email'],
                        'firstName': rep['name'].split()[0],
                        'lastName': rep['name'].split()[1]
                    },
                    'to': [{'email': f"contact{i}@example.com"} for i in range(len(deal_contact_ids[:2]))],
                    'cc': [],
                    'bcc': [],
                    'subject': subject,
                    'html': f"<p>Hi,</p><p>{fake.paragraph()}</p><p>Best regards,<br>{rep['name']}</p>",
                    'text': f"Hi,\n\n{fake.paragraph()}\n\nBest regards,\n{rep['name']}",
                    'status': fake.random_element(['SENT', 'SENT', 'SENT', 'BOUNCED']),
                    'sentVia': 'SALES_EMAIL',
                    'trackerKey': str(uuid.uuid4())
                }
            
            elif eng_type == 'MEETING':
                metadata = {
                    'startTime': int(engagement_date.timestamp() * 1000),
                    'endTime': int((engagement_date + timedelta(hours=1)).timestamp() * 1000),
                    'title': f"{fake.random_element(engagement_types['MEETING']['meeting_types'])} - {deal.get('dealname', 'Company')}",
                    'body': f"Meeting notes: {fake.paragraph()}",
                    'internalMeetingNotes': f"Internal: {fake.sentence()}",
                    'meetingOutcome': fake.random_element(['SCHEDULED', 'COMPLETED', 'NO_SHOW', 'CANCELLED']),
                    'meetingType': fake.random_element(['PHONE', 'IN_PERSON', 'VIDEO_CALL']),
                    'source': 'CRM_UI',
                    'location': fake.city() if fake.random_int(0, 1) else 'Zoom'
                }
            
            # Create engagement record
            engagement = {
                'id': engagement_id,
                'engagement': json.dumps(engagement_obj),
                'associations': json.dumps(associations),
                'metadata': json.dumps(metadata),
                'createdat': engagement_date.isoformat(),
                'updatedat': (engagement_date + timedelta(hours=1)).isoformat(),
                'created_at': engagement_date.isoformat()
            }
            
            engagements.append(engagement)
    
    # Add some standalone engagements (not tied to deals)
    num_standalone = 2500 - len(engagements)
    if num_standalone > 0:
        # Get prospect contacts
        prospect_contacts = [c for c in contacts if c.get('lifecycle_stage') != 'customer']
        
        for i in range(min(num_standalone, len(prospect_contacts) * 2)):
            engagement_id = str(uuid.uuid4())
            contact = fake.random_element(prospect_contacts)
            eng_type = fake.random_element(elements=list(engagement_types.keys()))
            engagement_date = datetime.now() - timedelta(days=fake.random_int(min=0, max=90))
            rep = fake.random_element(sales_reps)
            
            # Build engagement object
            engagement_obj = {
                'type': eng_type,
                'ownerId': rep['id'],
                'timestamp': int(engagement_date.timestamp() * 1000),
                'uid': f"{eng_type.lower()}-{engagement_id[:8]}",
                'portalId': '12345',
                'active': True,
                'createdAt': int(engagement_date.timestamp() * 1000),
                'lastUpdated': int((engagement_date + timedelta(hours=1)).timestamp() * 1000),
                'createdBy': rep['id'],
                'modifiedBy': rep['id']
            }
            
            # Build associations
            associations = {
                'contactIds': [contact['id']],
                'companyIds': [contact.get('company_id')] if contact.get('company_id') else [],
                'dealIds': []
            }
            
            # Simple metadata for standalone engagements
            if eng_type == 'CALL':
                metadata = {
                    'status': 'COMPLETED',
                    'durationMilliseconds': fake.random_int(min=60000, max=600000),
                    'body': f"Initial outreach call. {fake.sentence()}"
                }
            elif eng_type == 'EMAIL':
                metadata = {
                    'subject': f"Introduction - Bar Management Solutions",
                    'status': 'SENT',
                    'sentVia': 'SALES_EMAIL'
                }
            else:  # MEETING
                metadata = {
                    'title': f"Initial Discovery Call - {contact.get('company', 'Prospect')}",
                    'meetingOutcome': 'COMPLETED'
                }
            
            engagement = {
                'id': engagement_id,
                'engagement': json.dumps(engagement_obj),
                'associations': json.dumps(associations),
                'metadata': json.dumps(metadata),
                'createdat': engagement_date.isoformat(),
                'updatedat': engagement_date.isoformat(),
                'created_at': engagement_date.isoformat()
            }
            
            engagements.append(engagement)
    
    return engagements[:2500]  # Ensure exactly 2500

def save_hubspot_engagements_mapping(engagements):
    """Save HubSpot engagements mapping for future reference."""
    mapping = []
    for eng in engagements:
        eng_obj = json.loads(eng['engagement'])
        assocs = json.loads(eng['associations'])
        metadata = json.loads(eng['metadata'])
        
        mapping.append({
            'id': eng['id'],
            'type': eng_obj['type'],
            'owner_id': eng_obj.get('ownerId'),
            'deal_ids': assocs.get('dealIds', []),
            'contact_ids': assocs.get('contactIds', []),
            'company_ids': assocs.get('companyIds', []),
            'created_at': eng['created_at']
        })
    
    with open('data/hubspot_engagements_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved HubSpot engagements mapping to data/hubspot_engagements_mapping.json")

def main():
    print("=== Generating HubSpot Engagements ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate engagements
    print("\nGenerating HubSpot engagements...")
    engagements = generate_hubspot_engagements(env_config)
    print(f"✓ Generated {len(engagements)} HubSpot engagements")
    
    # Show type distribution
    type_counts = {}
    for eng in engagements:
        eng_type = json.loads(eng['engagement'])['type']
        type_counts[eng_type] = type_counts.get(eng_type, 0) + 1
    
    print("\nEngagement type distribution:")
    for eng_type, count in sorted(type_counts.items()):
        percentage = (count / len(engagements)) * 100
        print(f"  - {eng_type}: {count} ({percentage:.1f}%)")
    
    # Show deal vs standalone
    with_deals = len([e for e in engagements if json.loads(e['associations']).get('dealIds')])
    without_deals = len(engagements) - with_deals
    print(f"\nEngagement associations:")
    print(f"  - With deals: {with_deals}")
    print(f"  - Without deals (standalone): {without_deals}")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('hubspot_engagements', engagements)
    
    # Save mapping
    save_hubspot_engagements_mapping(engagements)
    
    # Verify
    count = db_helper.get_row_count('hubspot_engagements')
    print(f"\n✓ Total HubSpot engagements in database: {count}")

if __name__ == "__main__":
    main()