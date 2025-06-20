#!/usr/bin/env python3
"""
Generate synthetic HubSpot companies data for the bar management SaaS platform.

This script creates:
- All 100 accounts as HubSpot companies
- 25 additional prospect companies (not yet customers)
- Total: 125 companies
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

def load_accounts():
    """Load existing accounts data."""
    with open('data/generated_accounts.json', 'r') as f:
        return json.load(f)

def generate_hubspot_companies(env_config):
    """Generate HubSpot companies data."""
    companies = []
    accounts = load_accounts()
    
    # First, create companies for all existing accounts
    for account in accounts:
        company_id = str(uuid.uuid4())
        
        # Build properties JSON
        company_slug = account['company_name'].lower().replace(' ', '-').replace(',', '').replace('.', '').replace("'", '')
        properties = {
            'account_id': account['id'],
            'industry': account['industry'],
            'domain': f"{company_slug}.com",
            'numberofemployees': account['employee_count'],
            'annualrevenue': account['monthly_recurring_revenue'] * 12,
            'lifecycle_stage': 'customer',
            'tier': account['subscription_tier'],
            'mrr': account['monthly_recurring_revenue'],
            'location_count': account.get('location_count', 1),
            'device_count': account.get('device_count', 0),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip': fake.zipcode(),
            'country': 'United States',
            'phone': fake.phone_number(),
            'website': account.get('website', f"https://{company_slug}.com")
        }
        
        # Calculate created_date based on account creation
        account_created = datetime.fromisoformat(account['created_at'].replace('Z', ''))
        # HubSpot company created 1-7 days before account (during sales process)
        created_date = account_created - timedelta(days=fake.random_int(min=1, max=7))
        
        company = {
            'id': company_id,
            'properties': json.dumps(properties),  # JSONB field needs JSON string
            'name': account['company_name'],
            'business_type': account['industry'],
            'location_count': account.get('location_count', 1),
            'created_date': created_date.date().isoformat(),
            'createdat': created_date.isoformat(),
            'updatedat': (created_date + timedelta(days=fake.random_int(min=0, max=30))).isoformat(),
            'archived': False,
            'created_at': created_date.isoformat()
        }
        
        companies.append(company)
    
    # Generate 25 prospect companies
    prospect_industries = ['Restaurant', 'Bar', 'Hotel', 'Retail', 'Other']
    
    for i in range(25):
        company_id = str(uuid.uuid4())
        industry = fake.random_element(prospect_industries)
        company_name = fake.company()
        
        # Prospects have potential revenue but no MRR yet
        potential_mrr = fake.random_element([299, 999, 2999])
        employee_count = fake.random_int(min=5, max=200)
        
        properties = {
            'industry': industry,
            'domain': f"{company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')}.com",
            'numberofemployees': employee_count,
            'annualrevenue': potential_mrr * 12 * fake.random_int(min=1, max=3),  # Estimated based on size
            'lifecycle_stage': 'lead',
            'lead_status': fake.random_element(['new', 'contacted', 'qualified', 'unqualified']),
            'potential_mrr': potential_mrr,
            'location_count': fake.random_int(min=1, max=5),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip': fake.zipcode(),
            'country': 'United States',
            'phone': fake.phone_number(),
            'website': f"https://{company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')}.com",
            'source': fake.random_element(['Organic Search', 'Paid Search', 'Social Media', 'Direct', 'Referral'])
        }
        
        # Prospects created within last 90 days
        created_date = datetime.now() - timedelta(days=fake.random_int(min=1, max=90))
        
        company = {
            'id': company_id,
            'properties': json.dumps(properties),  # JSONB field needs JSON string
            'name': company_name,
            'business_type': industry,
            'location_count': properties['location_count'],
            'created_date': created_date.date().isoformat(),
            'createdat': created_date.isoformat(),
            'updatedat': (created_date + timedelta(days=fake.random_int(min=0, max=7))).isoformat(),
            'archived': False,
            'created_at': created_date.isoformat()
        }
        
        companies.append(company)
    
    return companies

def save_hubspot_companies_mapping(companies):
    """Save HubSpot companies mapping for future reference."""
    mapping = []
    for company in companies:
        props = json.loads(company['properties'])
        mapping.append({
            'id': company['id'],
            'name': company['name'],
            'account_id': props.get('account_id'),
            'lifecycle_stage': props.get('lifecycle_stage'),
            'industry': company['business_type']
        })
    
    with open('data/hubspot_companies_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Saved HubSpot companies mapping to data/hubspot_companies_mapping.json")

def main():
    print("=== Generating HubSpot Companies ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate companies
    print("\nGenerating HubSpot companies...")
    companies = generate_hubspot_companies(env_config)
    print(f"✓ Generated {len(companies)} HubSpot companies")
    
    # Separate customers and prospects
    customers = [c for c in companies if json.loads(c['properties']).get('lifecycle_stage') == 'customer']
    prospects = [c for c in companies if json.loads(c['properties']).get('lifecycle_stage') != 'customer']
    print(f"  - Customers: {len(customers)}")
    print(f"  - Prospects: {len(prospects)}")
    
    # Show industry distribution
    industry_counts = {}
    for company in companies:
        industry = company['business_type']
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    print("\nIndustry distribution:")
    for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(companies)) * 100
        print(f"  - {industry}: {count} ({percentage:.1f}%)")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('hubspot_companies', companies)
    
    # Save mapping
    save_hubspot_companies_mapping(companies)
    
    # Verify
    count = db_helper.get_row_count('hubspot_companies')
    print(f"\n✓ Total HubSpot companies in database: {count}")

if __name__ == "__main__":
    main()