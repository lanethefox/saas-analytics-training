#!/usr/bin/env python3
"""
Generate synthetic HubSpot tickets data for the bar management SaaS platform.

This script creates:
- 400 support tickets
- Priority distribution
- Resolution time patterns
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

def generate_hubspot_tickets(env_config):
    """Generate HubSpot tickets data."""
    tickets = []
    companies = load_hubspot_companies()
    contacts = load_hubspot_contacts()
    
    # Only customers create support tickets
    customer_companies = [c for c in companies if c['lifecycle_stage'] == 'customer']
    customer_contacts = [c for c in contacts if c['lifecycle_stage'] == 'customer']
    
    # Ticket categories and subjects
    ticket_categories = {
        'Technical Issue': {
            'weight': 0.4,
            'subjects': [
                'Device offline - urgent',
                'Cannot access dashboard',
                'Data sync issues',
                'API connection error',
                'Device not reporting data',
                'Login problems',
                'Performance issues',
                'Integration not working'
            ],
            'priority_weights': {'HIGH': 0.3, 'MEDIUM': 0.5, 'LOW': 0.2}
        },
        'Feature Request': {
            'weight': 0.2,
            'subjects': [
                'Request for new report type',
                'Feature suggestion: Inventory alerts',
                'Mobile app enhancement request',
                'Dashboard customization request',
                'Export functionality needed',
                'Integration request'
            ],
            'priority_weights': {'HIGH': 0.1, 'MEDIUM': 0.6, 'LOW': 0.3}
        },
        'Billing Question': {
            'weight': 0.15,
            'subjects': [
                'Invoice question',
                'Billing cycle inquiry',
                'Payment method update',
                'Subscription change request',
                'Billing discrepancy',
                'Add-on pricing question'
            ],
            'priority_weights': {'HIGH': 0.2, 'MEDIUM': 0.6, 'LOW': 0.2}
        },
        'Training Request': {
            'weight': 0.15,
            'subjects': [
                'New user training needed',
                'Advanced features training',
                'Onboarding assistance',
                'Best practices consultation',
                'Report building help'
            ],
            'priority_weights': {'HIGH': 0.1, 'MEDIUM': 0.7, 'LOW': 0.2}
        },
        'General Question': {
            'weight': 0.1,
            'subjects': [
                'How to export data?',
                'User permissions question',
                'Device installation help',
                'General inquiry',
                'Documentation request'
            ],
            'priority_weights': {'HIGH': 0.05, 'MEDIUM': 0.3, 'LOW': 0.65}
        }
    }
    
    # Pipeline stages and average resolution times (hours)
    pipeline_stages = {
        'new': {'duration': 0.5, 'next': 'waiting-on-contact'},
        'waiting-on-contact': {'duration': 2, 'next': 'waiting-on-us'},
        'waiting-on-us': {'duration': 4, 'next': 'closed'},
        'closed': {'duration': 0, 'next': None}
    }
    
    # Generate tickets
    for i in range(400):
        ticket_id = str(uuid.uuid4())
        
        # Select a customer company and contact
        company = fake.random_element(customer_companies)
        company_contacts = [c for c in customer_contacts if c['company_id'] == company['id']]
        if not company_contacts:
            company_contacts = customer_contacts[:10]  # Fallback
        contact = fake.random_element(company_contacts)
        
        # Select category and subject
        category = fake.random_element(elements=list(ticket_categories.keys()))
        category_info = ticket_categories[category]
        subject = fake.random_element(category_info['subjects'])
        
        # Determine priority
        priority_weights = category_info['priority_weights']
        priority_choices = []
        for p, weight in priority_weights.items():
            priority_choices.extend([p] * int(weight * 100))
        priority = fake.random_element(priority_choices)
        
        # Generate content based on category
        if category == 'Technical Issue':
            content = f"""Customer reported: {subject}
            
Device/Location affected: {fake.random_element(['All locations', 'Main location', 'Device #' + str(fake.random_int(100, 999))])}
Error message: {fake.sentence() if fake.random_int(0, 1) else 'No error message'}
When did this start: {fake.random_element(['Today', 'Yesterday', 'Last week', '2 days ago'])}
Impact: {fake.random_element(['Cannot operate', 'Partial functionality', 'Minor inconvenience'])}

Additional details:
{fake.paragraph()}"""
        
        elif category == 'Feature Request':
            content = f"""Feature request: {subject}

Business case:
{fake.paragraph()}

Expected benefit:
{fake.sentence()}

Priority for our business: {fake.random_element(['Critical', 'High', 'Medium', 'Nice to have'])}"""
        
        elif category == 'Billing Question':
            content = f"""Billing inquiry: {subject}

Account details:
- Company: {company['name']}
- Current plan: {fake.random_element(['Basic', 'Pro', 'Enterprise'])}
- Billing cycle: {fake.random_element(['Monthly', 'Annual'])}

Question:
{fake.paragraph()}"""
        
        elif category == 'Training Request':
            content = f"""Training request: {subject}

Number of users: {fake.random_int(1, 10)}
Preferred format: {fake.random_element(['Live session', 'Recorded video', 'Documentation'])}
Availability: {fake.random_element(['This week', 'Next week', 'Flexible'])}

Specific topics to cover:
{fake.paragraph()}"""
        
        else:  # General Question
            content = f"""Question: {subject}

Details:
{fake.paragraph()}"""
        
        # Determine ticket age and status
        is_closed = fake.random_int(0, 100) < 75  # 75% of tickets are closed
        resolution_hours = None
        
        if is_closed:
            # Closed ticket - created in the past
            created_days_ago = fake.random_int(min=7, max=365)
            created_date = datetime.now() - timedelta(days=created_days_ago)
            
            # Resolution time based on priority
            if priority == 'HIGH':
                resolution_hours = fake.random_int(min=2, max=24)
            elif priority == 'MEDIUM':
                resolution_hours = fake.random_int(min=4, max=72)
            else:
                resolution_hours = fake.random_int(min=8, max=168)
            
            closed_date = created_date + timedelta(hours=resolution_hours)
            current_stage = 'closed'
            
        else:
            # Open ticket - created recently
            created_hours_ago = fake.random_int(min=1, max=168)  # Within last week
            created_date = datetime.now() - timedelta(hours=created_hours_ago)
            closed_date = None
            
            # Determine current stage based on age
            if created_hours_ago < 4:
                current_stage = 'new'
            elif created_hours_ago < 24:
                current_stage = 'waiting-on-contact'
            else:
                current_stage = 'waiting-on-us'
        
        # Build properties
        properties = {
            'hs_ticket_category': category,
            'hs_resolution_time': resolution_hours if is_closed else None,
            'closed_date': closed_date.isoformat() if closed_date else None,
            'hubspot_owner_id': fake.random_element(['6', '7', '8']),  # Support team IDs
            'hs_custom_object_id': ticket_id,
            'hs_created_by_user_id': contact['id'],
            'source_type': fake.random_element(['EMAIL', 'FORM', 'CHAT', 'PHONE']),
            'hs_object_id': int(fake.numerify('#########')),
            'hs_ticket_id': int(fake.numerify('#####'))
        }
        
        # Build associations
        associations = {
            'contact_ids': [contact['id']],
            'company_ids': [company['id']],
            'deal_ids': []  # Tickets typically not associated with deals
        }
        
        # Create ticket
        ticket = {
            'id': ticket_id,
            'properties': json.dumps(properties),
            'associations': json.dumps(associations),
            'subject': f"[{category}] {subject}",
            'content': content,
            'hs_pipeline': 'support-pipeline',
            'hs_pipeline_stage': current_stage,
            'hs_ticket_priority': priority,
            'createdate': created_date.isoformat(),
            'hs_lastmodifieddate': (closed_date or datetime.now()).isoformat(),
            'archived': is_closed,
            'created_at': created_date.isoformat()
        }
        
        tickets.append(ticket)
    
    return tickets

def save_hubspot_tickets_mapping(tickets):
    """Save HubSpot tickets mapping for future reference."""
    mapping = []
    for ticket in tickets:
        props = json.loads(ticket['properties'])
        assocs = json.loads(ticket['associations'])
        
        mapping.append({
            'id': ticket['id'],
            'subject': ticket['subject'],
            'category': props.get('hs_ticket_category'),
            'priority': ticket['hs_ticket_priority'],
            'stage': ticket['hs_pipeline_stage'],
            'company_ids': assocs.get('company_ids', []),
            'contact_ids': assocs.get('contact_ids', []),
            'created_at': ticket['created_at'],
            'is_closed': ticket['archived']
        })
    
    with open('data/hubspot_tickets_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved HubSpot tickets mapping to data/hubspot_tickets_mapping.json")

def main():
    print("=== Generating HubSpot Tickets ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate tickets
    print("\nGenerating HubSpot tickets...")
    tickets = generate_hubspot_tickets(env_config)
    print(f"✓ Generated {len(tickets)} HubSpot tickets")
    
    # Show category distribution
    category_counts = {}
    for ticket in tickets:
        category = json.loads(ticket['properties']).get('hs_ticket_category')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\nTicket category distribution:")
    for category, count in sorted(category_counts.items()):
        percentage = (count / len(tickets)) * 100
        print(f"  - {category}: {count} ({percentage:.1f}%)")
    
    # Show priority distribution
    priority_counts = {}
    for ticket in tickets:
        priority = ticket['hs_ticket_priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    print("\nTicket priority distribution:")
    for priority, count in sorted(priority_counts.items()):
        percentage = (count / len(tickets)) * 100
        print(f"  - {priority}: {count} ({percentage:.1f}%)")
    
    # Show status
    open_tickets = len([t for t in tickets if not t['archived']])
    closed_tickets = len([t for t in tickets if t['archived']])
    print(f"\nTicket status:")
    print(f"  - Open: {open_tickets}")
    print(f"  - Closed: {closed_tickets}")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('hubspot_tickets', tickets)
    
    # Save mapping
    save_hubspot_tickets_mapping(tickets)
    
    # Verify
    count = db_helper.get_row_count('hubspot_tickets')
    print(f"\n✓ Total HubSpot tickets in database: {count}")

if __name__ == "__main__":
    main()