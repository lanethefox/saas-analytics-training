#!/usr/bin/env python3
"""
Generate synthetic HubSpot contacts data for the bar management SaaS platform.

This script creates:
- 500 contacts with multiple per company
- Role-based email patterns
- Lead scoring distribution
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

def generate_hubspot_contacts(env_config):
    """Generate HubSpot contacts data."""
    contacts = []
    companies = load_hubspot_companies()
    
    # Role titles for contacts
    customer_roles = [
        'Owner', 'General Manager', 'Operations Manager', 'Bar Manager',
        'Restaurant Manager', 'Purchasing Manager', 'Finance Director',
        'Marketing Manager', 'IT Manager', 'Head of Operations'
    ]
    
    prospect_roles = [
        'CEO', 'COO', 'CFO', 'VP of Operations', 'Director of Operations',
        'Director of Finance', 'Director of IT', 'Owner', 'Managing Partner'
    ]
    
    # Generate contacts for each company
    for company in companies:
        # Determine number of contacts based on lifecycle stage
        if company['lifecycle_stage'] == 'customer':
            num_contacts = fake.random_int(min=2, max=6)
            roles = customer_roles
        else:
            num_contacts = fake.random_int(min=1, max=3)
            roles = prospect_roles
        
        # Get company name for email domain
        company_domain = company['name'].lower().replace(' ', '').replace(',', '').replace('.', '').replace("'", '')
        
        used_roles = []
        for i in range(num_contacts):
            contact_id = str(uuid.uuid4())
            
            # Generate name
            firstname = fake.first_name()
            lastname = fake.last_name()
            
            # Select role (avoid duplicates within company)
            available_roles = [r for r in roles if r not in used_roles]
            if not available_roles:
                available_roles = roles
            role = fake.random_element(available_roles)
            used_roles.append(role)
            
            # Generate email
            email_format = fake.random_element([
                f"{firstname.lower()}.{lastname.lower()}@{company_domain}.com",
                f"{firstname[0].lower()}{lastname.lower()}@{company_domain}.com",
                f"{firstname.lower()}@{company_domain}.com"
            ])
            
            # Lead scoring (higher for decision makers)
            if any(title in role.upper() for title in ['CEO', 'COO', 'CFO', 'OWNER', 'DIRECTOR', 'VP']):
                lead_score = fake.random_int(min=70, max=100)
            elif 'MANAGER' in role.upper():
                lead_score = fake.random_int(min=40, max=70)
            else:
                lead_score = fake.random_int(min=10, max=40)
            
            # Build properties
            properties = {
                'company_id': company['id'],
                'jobtitle': role,
                'lifecycle_stage': company['lifecycle_stage'],
                'lead_score': lead_score,
                'phone': fake.phone_number(),
                'mobilephone': fake.phone_number() if fake.random_int(0, 1) else None,
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip': fake.zipcode(),
                'country': 'United States',
                'website': f"https://{company_domain}.com",
                'linkedin': f"https://linkedin.com/in/{firstname.lower()}-{lastname.lower()}" if fake.random_int(0, 1) else None,
                'last_contacted': None,
                'notes': f"Contact at {company['name']} - {role}",
                'source': fake.random_element(['Direct', 'Referral', 'Website', 'Trade Show', 'Cold Call'])
            }
            
            # Create date (same as or after company creation)
            # Get company creation from the mapping
            if company['lifecycle_stage'] == 'customer':
                # Customer contacts created around same time as company
                base_date = datetime.now() - timedelta(days=fake.random_int(min=365, max=1825))  # 1-5 years
                created_date = base_date + timedelta(days=fake.random_int(min=-7, max=30))
            else:
                # Prospect contacts created recently
                created_date = datetime.now() - timedelta(days=fake.random_int(min=1, max=90))
            
            contact = {
                'id': contact_id,
                'properties': json.dumps(properties),
                'firstname': firstname,
                'lastname': lastname,
                'email': email_format,
                'company': company['name'],
                'phone': properties['phone'],
                'createdat': created_date.isoformat(),
                'updatedat': (created_date + timedelta(days=fake.random_int(min=0, max=30))).isoformat(),
                'archived': False,
                'created_at': created_date.isoformat()
            }
            
            contacts.append(contact)
    
    return contacts

def save_hubspot_contacts_mapping(contacts):
    """Save HubSpot contacts mapping for future reference."""
    mapping = []
    for contact in contacts:
        props = json.loads(contact['properties'])
        mapping.append({
            'id': contact['id'],
            'name': f"{contact['firstname']} {contact['lastname']}",
            'email': contact['email'],
            'company_id': props.get('company_id'),
            'company': contact['company'],
            'role': props.get('jobtitle'),
            'lifecycle_stage': props.get('lifecycle_stage')
        })
    
    with open('data/hubspot_contacts_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved HubSpot contacts mapping to data/hubspot_contacts_mapping.json")

def main():
    print("=== Generating HubSpot Contacts ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate contacts
    print("\nGenerating HubSpot contacts...")
    contacts = generate_hubspot_contacts(env_config)
    print(f"✓ Generated {len(contacts)} HubSpot contacts")
    
    # Show distribution
    customers = [c for c in contacts if json.loads(c['properties']).get('lifecycle_stage') == 'customer']
    prospects = [c for c in contacts if json.loads(c['properties']).get('lifecycle_stage') != 'customer']
    print(f"  - Customer contacts: {len(customers)}")
    print(f"  - Prospect contacts: {len(prospects)}")
    
    # Show role distribution (top 10)
    role_counts = {}
    for contact in contacts:
        role = json.loads(contact['properties']).get('jobtitle')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print("\nTop 10 roles:")
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {role}: {count}")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('hubspot_contacts', contacts)
    
    # Save mapping
    save_hubspot_contacts_mapping(contacts)
    
    # Verify
    count = db_helper.get_row_count('hubspot_contacts')
    print(f"\n✓ Total HubSpot contacts in database: {count}")

if __name__ == "__main__":
    main()