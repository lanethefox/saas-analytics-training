import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from typing import Dict, List, Tuple, Optional
import logging

# Add parent directory to path to import base class
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

fake = Faker()
logger = logging.getLogger(__name__)

class BusinessEntityGenerator:
    """Base class for generating business entities with realistic patterns"""
    
    def __init__(self, config):
        self.config = config
        self.business_types = [
            'Restaurant', 'Sports Bar', 'Brewery', 'Wine Bar', 'Cocktail Lounge',
            'Sports Grill', 'Pub', 'Nightclub', 'Rooftop Bar', 'Dive Bar'
        ]
        
    def generate_business_name(self, business_type: str) -> str:
        """Generate realistic business names"""
        prefixes = {
            'Restaurant': ['The', 'Villa', 'Casa', 'Chez'],
            'Sports Bar': ['Sports', 'Champions', 'MVP', 'Stadium'],
            'Brewery': ['Craft', 'Local', 'Artisan', 'Barrel'],
            'Wine Bar': ['Vintage', 'Cork', 'Grape', 'Cellar'],
            'Cocktail Lounge': ['Mixology', 'Craft', 'Premium', 'Elite'],
            'Sports Grill': ['Grill', 'BBQ', 'Fire', 'Smoke'],
            'Pub': ['Irish', 'Corner', 'Local', 'Traditional'],
            'Nightclub': ['Club', 'Neon', 'Electric', 'Pulse'],
            'Rooftop Bar': ['Sky', 'Rooftop', 'Heights', 'View'],
            'Dive Bar': ['Corner', 'Local', 'Neighborhood', 'Classic']
        }
        
        suffixes = {
            'Restaurant': ['Bistro', 'Kitchen', 'Table', 'House'],
            'Sports Bar': ['Sports Bar', 'Grill', 'Tavern'],
            'Brewery': ['Brewing', 'Brewery', 'Beer Co'],
            'Wine Bar': ['Wine Bar', 'Cellars', 'Vintners'],
            'Cocktail Lounge': ['Lounge', 'Bar', 'Cocktails'],
            'Sports Grill': ['Grill', 'BBQ', 'Kitchen'],
            'Pub': ['Pub', 'Tavern', 'Inn'],
            'Nightclub': ['Club', 'Lounge', 'Scene'],
            'Rooftop Bar': ['Rooftop', 'Sky Bar', 'Heights'],
            'Dive Bar': ['Bar', 'Tavern', 'Saloon']
        }
        
        prefix = random.choice(prefixes.get(business_type, ['The']))
        name = fake.company().replace('Group', '').replace('Inc', '').replace('LLC', '').strip()
        suffix = random.choice(suffixes.get(business_type, ['Bar']))
        
        return f"{prefix} {name} {suffix}"

import os
import sys
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from typing import Dict, List, Tuple, Optional
import uuid
import argparse
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker with consistent seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

class DataScale(Enum):
    """Data generation scale options"""
    XS = "xs"               # 100 customers for quick testing
    SMALL = "small"         # 1,000 customers for testing
    ENTERPRISE = "enterprise" # 40,000 customers for full enterprise scale

@dataclass
class PlatformConfig:
    """Configuration for synthetic data generation"""
    scale: DataScale
    start_date: date
    end_date: date
    
    # Scale-based sizing
    customers: int
    locations_per_customer: Tuple[int, int]  # (min, max)
    devices_per_location: Tuple[int, int]    # (min, max)
    
    # Business parameters
    trial_conversion_rate: float = 0.65
    monthly_churn_rate: float = 0.08
    expansion_probability: float = 0.15
    support_ticket_rate: float = 0.12  # tickets per customer per month

    @classmethod
    def create(cls, scale: str, months_back: int = 24) -> 'PlatformConfig':
        """Create configuration based on scale"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)
        
        scale_enum = DataScale(scale)
        
        if scale_enum == DataScale.XS:
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=100,
                locations_per_customer=(1, 4),
                devices_per_location=(2, 8)
            )
        elif scale_enum == DataScale.SMALL:
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=1000,
                locations_per_customer=(1, 8),
                devices_per_location=(3, 15)
            )
        else:  # ENTERPRISE
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=40000,
                locations_per_customer=(1, 20),
                devices_per_location=(3, 30)
            )

class BusinessEntityGenerator:
    """Base class for generating business entities with realistic patterns"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.business_types = [
            'Restaurant', 'Sports Bar', 'Brewery', 'Wine Bar', 'Cocktail Lounge',
            'Sports Grill', 'Pub', 'Nightclub', 'Rooftop Bar', 'Dive Bar'
        ]
        
        self.device_types = [
            'POS Terminal', 'Inventory Scanner', 'Temperature Monitor', 
            'Security Camera', 'Music System', 'Payment Terminal',
            'Kitchen Display', 'Order Tablet', 'Cash Register'
        ]
        
    def generate_business_name(self, business_type: str) -> str:
        """Generate realistic business names"""
        prefixes = {
            'Restaurant': ['The', 'Villa', 'Casa', 'Chez'],
            'Sports Bar': ['Sports', 'Champions', 'MVP', 'Stadium'],
            'Brewery': ['Craft', 'Local', 'Artisan', 'Barrel'],
            'Wine Bar': ['Vintage', 'Cork', 'Grape', 'Cellar'],
            'Cocktail Lounge': ['Mixology', 'Craft', 'Premium', 'Elite'],
            'Sports Grill': ['Grill', 'BBQ', 'Fire', 'Smoke'],
            'Pub': ['Irish', 'Corner', 'Local', 'Traditional'],
            'Nightclub': ['Club', 'Neon', 'Electric', 'Pulse'],
            'Rooftop Bar': ['Sky', 'Rooftop', 'Heights', 'View'],
            'Dive Bar': ['Corner', 'Local', 'Neighborhood', 'Classic']
        }
        
        suffixes = {
            'Restaurant': ['Bistro', 'Kitchen', 'Table', 'House'],
            'Sports Bar': ['Sports Bar', 'Grill', 'Tavern'],
            'Brewery': ['Brewing', 'Brewery', 'Beer Co'],
            'Wine Bar': ['Wine Bar', 'Cellars', 'Vintners'],
            'Cocktail Lounge': ['Lounge', 'Bar', 'Cocktails'],
            'Sports Grill': ['Grill', 'BBQ', 'Kitchen'],
            'Pub': ['Pub', 'Tavern', 'Inn'],
            'Nightclub': ['Club', 'Lounge', 'Scene'],
            'Rooftop Bar': ['Rooftop', 'Sky Bar', 'Heights'],
            'Dive Bar': ['Bar', 'Tavern', 'Saloon']
        }
        
        prefix = random.choice(prefixes.get(business_type, ['The']))
        name = fake.company().replace('Group', '').replace('Inc', '').replace('LLC', '').strip()
        suffix = random.choice(suffixes.get(business_type, ['Bar']))
        
        return f"{prefix} {name} {suffix}"

class HubSpotDataGenerator(BusinessEntityGenerator):
    """Generate HubSpot CRM and sales pipeline data"""
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.deal_stages = [
            'Lead', 'Marketing Qualified Lead', 'Sales Qualified Lead', 
            'Discovery', 'Demo Scheduled', 'Proposal', 'Negotiation',
            'Closed Won', 'Closed Lost'
        ]
        
        self.lead_sources = [
            'Website', 'Google Ads', 'Facebook Ads', 'LinkedIn Ads',
            'Content Marketing', 'Webinar', 'Trade Show', 'Referral',
            'Cold Outreach', 'Organic Search'
        ]
        
        self.support_categories = [
            'Technical Issue', 'Billing Question', 'Feature Request',
            'Training', 'Integration Support', 'Account Management',
            'Bug Report', 'General Inquiry'
        ]
        
    def generate_companies(self) -> List[Dict]:
        """Generate HubSpot company records with realistic business attributes"""
        companies = []
        
        for i in range(self.config.customers):
            business_type = random.choice(self.business_types)
            company_name = self.generate_business_name(business_type)
            
            # Create realistic company creation date (spread over time period)
            days_back = random.randint(0, (self.config.end_date - self.config.start_date).days)
            created_date = self.config.end_date - timedelta(days=days_back)
            
            # Determine number of locations for this customer
            min_locs, max_locs = self.config.locations_per_customer
            location_count = random.randint(min_locs, max_locs)
            
            # Generate realistic business attributes
            annual_revenue = self._generate_annual_revenue(location_count)
            employee_count = self._generate_employee_count(location_count)
            
            company = {
                'id': str(10000000 + i),  # HubSpot-style numeric IDs
                'properties': {
                    'name': company_name,
                    'email': f"contact@{company_name.lower().replace(' ', '').replace('&', 'and')[:20]}.com",
                    'domain': f"{company_name.lower().replace(' ', '').replace('&', 'and')[:20]}.com",
                    'createdate': created_date.isoformat() + 'Z',
                    'hs_lastmodifieddate': created_date.isoformat() + 'Z',
                    'industry': self._map_business_type_to_industry(business_type),
                    'annualrevenue': str(annual_revenue),
                    'numberofemployees': str(employee_count),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'country': 'United States',
                    'zip': fake.zipcode(),
                    'phone': fake.phone_number(),
                    'website': f"https://{company_name.lower().replace(' ', '').replace('&', 'and')[:20]}.com",
                    'description': f"A {business_type.lower()} business with {location_count} location{'s' if location_count > 1 else ''}",
                    'lifecyclestage': 'customer',
                    'lead_source': random.choice(self.lead_sources),
                    'customer_tier': self._determine_customer_tier(location_count, annual_revenue),
                    'business_type': business_type,
                    'location_count': str(location_count)
                },
                # Additional attributes for internal use
                'name': company_name,
                'business_type': business_type,
                'location_count': location_count,
                'annual_revenue': annual_revenue,
                'employee_count': employee_count,
                'created_date': created_date,
                'email': f"contact@{company_name.lower().replace(' ', '').replace('&', 'and')[:20]}.com"
            }
            
            companies.append(company)
            
        logger.info(f"Generated {len(companies)} HubSpot companies")
        return companies
        
    def generate_contacts(self, companies: List[Dict]) -> List[Dict]:
        """Generate realistic contacts for each company"""
        contacts = []
        contact_id = 20000000  # Starting contact ID
        
        for company in companies:
            # Generate 1-4 contacts per company based on size
            num_contacts = min(4, max(1, company['location_count'] // 2 + random.randint(0, 2)))
            
            # Primary contact (decision maker)
            primary_contact = self._generate_contact(
                contact_id, company, is_primary=True, role='decision_maker'
            )
            contacts.append(primary_contact)
            contact_id += 1
            
            # Additional contacts
            roles = ['user', 'influencer', 'technical', 'financial']
            for i in range(num_contacts - 1):
                role = random.choice(roles)
                contact = self._generate_contact(contact_id, company, is_primary=False, role=role)
                contacts.append(contact)
                contact_id += 1
                
        logger.info(f"Generated {len(contacts)} HubSpot contacts")
        return contacts
        
    def generate_deals(self, companies: List[Dict], contacts: List[Dict]) -> List[Dict]:
        """Generate sales pipeline with realistic deal progression"""
        deals = []
        deal_id = 30000000  # Starting deal ID
        
        # Group contacts by company
        company_contacts = {}
        for contact in contacts:
            company_id = contact['properties']['associatedcompanyid']
            if company_id not in company_contacts:
                company_contacts[company_id] = []
            company_contacts[company_id].append(contact)
            
        for company in companies:
            company_id = company['id']
            company_contacts_list = company_contacts.get(company_id, [])
            
            # Determine deal value based on company size and plan
            deal_value = self._calculate_deal_value(company)
            
            # Create sales deal with realistic progression
            deal_created = company['created_date'] - timedelta(days=random.randint(7, 45))
            
            # Determine deal outcome and stage progression
            won_probability = self._calculate_win_probability(company)
            deal_won = random.random() < won_probability
            
            if deal_won:
                deal_stage = 'Closed Won'
                close_date = company['created_date']
            else:
                # Lost deal - determine where it stalled
                lost_stages = ['Discovery', 'Demo Scheduled', 'Proposal', 'Negotiation', 'Closed Lost']
                stage_index = random.randint(0, len(lost_stages) - 1)
                deal_stage = lost_stages[stage_index]
                close_date = deal_created + timedelta(days=random.randint(14, 90))
                
            deal = {
                'id': str(deal_id),
                'properties': {
                    'dealname': f"{company['name']} - Bar Management Platform",
                    'amount': str(deal_value),
                    'dealstage': deal_stage,
                    'createdate': deal_created.isoformat() + 'Z',
                    'closedate': close_date.isoformat() + 'Z' if close_date else None,
                    'hs_lastmodifieddate': close_date.isoformat() + 'Z' if close_date else deal_created.isoformat() + 'Z',
                    'pipeline': 'default',
                    'dealtype': 'newbusiness',
                    'lead_source': company['properties']['lead_source'],
                    'dealowner': str(random.randint(40000000, 40000010)),  # Sales rep ID
                    'hs_deal_stage_probability': self._get_stage_probability(deal_stage),
                    'num_associated_contacts': str(len(company_contacts_list)),
                    'hs_analytics_source': company['properties']['lead_source'],
                    'hubspot_owner_id': str(random.randint(40000000, 40000010))
                },
                'associations': {
                    'companies': [company_id],
                    'contacts': [contact['id'] for contact in company_contacts_list[:2]]  # Associate first 2 contacts
                }
            }
            
            deals.append(deal)
            deal_id += 1
            
        logger.info(f"Generated {len(deals)} HubSpot deals")
        return deals
        
    def generate_tickets(self, companies: List[Dict], contacts: List[Dict]) -> List[Dict]:
        """Generate support tickets with realistic patterns"""
        tickets = []
        ticket_id = 50000000  # Starting ticket ID
        
        # Group contacts by company
        company_contacts = {}
        for contact in contacts:
            company_id = contact['properties']['associatedcompanyid']
            if company_id not in company_contacts:
                company_contacts[company_id] = []
            company_contacts[company_id].append(contact)
            
        for company in companies:
            company_id = company['id']
            company_contacts_list = company_contacts.get(company_id, [])
            
            # Calculate number of tickets based on company size and time period
            months_active = (self.config.end_date - company['created_date']).days / 30
            expected_tickets = int(months_active * self.config.support_ticket_rate * company['location_count'])
            num_tickets = max(0, np.random.poisson(expected_tickets))
            
            for i in range(num_tickets):
                # Generate ticket date after company creation
                days_after_creation = random.randint(1, max(1, (self.config.end_date - company['created_date']).days))
                ticket_date = company['created_date'] + timedelta(days=days_after_creation)
                
                # Determine ticket attributes
                category = random.choice(self.support_categories)
                priority = self._determine_ticket_priority(category)
                status = self._determine_ticket_status(ticket_date)
                
                # Select contact who submitted ticket
                submitter_contact = random.choice(company_contacts_list) if company_contacts_list else None
                
                ticket = {
                    'id': str(ticket_id),
                    'properties': {
                        'subject': self._generate_ticket_subject(category),
                        'content': self._generate_ticket_content(category, company),
                        'hs_ticket_category': category,
                        'hs_ticket_priority': priority,
                        'hs_pipeline_stage': status,
                        'createdate': ticket_date.isoformat() + 'Z',
                        'hs_lastmodifieddate': ticket_date.isoformat() + 'Z',
                        'hubspot_owner_id': str(random.randint(60000000, 60000010)),  # Support rep ID
                        'source_type': random.choice(['EMAIL', 'CHAT', 'PHONE', 'FORM']),
                        'hs_resolution': 'RESOLVED' if status == 'Closed' else 'PENDING'
                    },
                    'associations': {
                        'companies': [company_id],
                        'contacts': [submitter_contact['id']] if submitter_contact else []
                    }
                }
                
                tickets.append(ticket)
                ticket_id += 1
                
        logger.info(f"Generated {len(tickets)} HubSpot support tickets")
        return tickets
        
    def generate_owners(self) -> List[Dict]:
        """Generate sales reps and customer success managers"""
        owners = []
        
        # Sales reps
        for i in range(10):
            owner_id = 40000000 + i
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            owner = {
                'id': str(owner_id),
                'email': f"{first_name.lower()}.{last_name.lower()}@barmanagementco.com",
                'firstName': first_name,
                'lastName': last_name,
                'type': 'PERSON',
                'activeUserId': owner_id,
                'remoteList': [
                    {
                        'id': owner_id,
                        'portalId': 12345678,
                        'ownerId': owner_id,
                        'type': 'SALESPERSON',
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': f"{first_name.lower()}.{last_name.lower()}@barmanagementco.com",
                        'signature': f"Best regards,\\n{first_name} {last_name}\\nSales Representative",
                        'isActive': True
                    }
                ]
            }
            owners.append(owner)
            
        # Support reps
        for i in range(10):
            owner_id = 60000000 + i
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            owner = {
                'id': str(owner_id),
                'email': f"{first_name.lower()}.{last_name.lower()}@barmanagementco.com",
                'firstName': first_name,
                'lastName': last_name,
                'type': 'PERSON',
                'activeUserId': owner_id,
                'remoteList': [
                    {
                        'id': owner_id,
                        'portalId': 12345678,
                        'ownerId': owner_id,
                        'type': 'SUPPORT',
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': f"{first_name.lower()}.{last_name.lower()}@barmanagementco.com",
                        'signature': f"Best regards,\\n{first_name} {last_name}\\nCustomer Success",
                        'isActive': True
                    }
                ]
            }
            owners.append(owner)
            
        logger.info(f"Generated {len(owners)} HubSpot owners")
        return owners
        
    def generate_engagements(self, companies: List[Dict], contacts: List[Dict], deals: List[Dict]) -> List[Dict]:
        """Generate sales and customer success engagements"""
        engagements = []
        engagement_id = 70000000
        
        # Group data by company
        company_contacts = {}
        company_deals = {}
        
        for contact in contacts:
            company_id = contact['properties']['associatedcompanyid']
            if company_id not in company_contacts:
                company_contacts[company_id] = []
            company_contacts[company_id].append(contact)
            
        for deal in deals:
            for company_id in deal['associations']['companies']:
                if company_id not in company_deals:
                    company_deals[company_id] = []
                company_deals[company_id].append(deal)
                
        for company in companies:
            company_id = company['id']
            contacts_list = company_contacts.get(company_id, [])
            deals_list = company_deals.get(company_id, [])
            
            # Generate engagements based on company lifecycle
            months_active = (self.config.end_date - company['created_date']).days / 30
            
            # Sales engagements (pre-close)
            sales_engagements = max(1, int(months_active * 0.5))  # Bi-weekly during sales cycle
            
            # Customer success engagements (post-close)
            cs_engagements = max(0, int(months_active * 0.25))  # Monthly post-close
            
            # Generate sales engagements
            for i in range(sales_engagements):
                engagement_date = datetime.combine(company['created_date'], datetime.min.time()) - timedelta(days=random.randint(0, 60))
                
                engagement_type = random.choice(['EMAIL', 'CALL', 'MEETING', 'NOTE'])
                
                engagement = {
                    'id': str(engagement_id),
                    'engagement': {
                        'id': engagement_id,
                        'portalId': 12345678,
                        'active': True,
                        'createdAt': int(engagement_date.timestamp() * 1000),
                        'lastUpdated': int(engagement_date.timestamp() * 1000),
                        'type': engagement_type,
                        'ownerId': random.randint(40000000, 40000009),  # Sales rep
                        'source': 'CRM_UI',
                        'sourceId': 'userId:12345'
                    },
                    'associations': {
                        'companyIds': [int(company_id)],
                        'contactIds': [int(contact['id']) for contact in contacts_list[:1]],
                        'dealIds': [int(deal['id']) for deal in deals_list[:1]]
                    },
                    'metadata': {
                        'subject': self._generate_engagement_subject(engagement_type, 'sales'),
                        'body': self._generate_engagement_body(engagement_type, company, 'sales')
                    }
                }
                
                engagements.append(engagement)
                engagement_id += 1
                
            # Generate customer success engagements
            for i in range(cs_engagements):
                engagement_date = datetime.combine(company['created_date'], datetime.min.time()) + timedelta(days=random.randint(30, int(months_active * 30)))
                
                if engagement_date > datetime.combine(self.config.end_date, datetime.min.time()):
                    continue
                    
                engagement_type = random.choice(['EMAIL', 'CALL', 'MEETING', 'NOTE'])
                
                engagement = {
                    'id': str(engagement_id),
                    'engagement': {
                        'id': engagement_id,
                        'portalId': 12345678,
                        'active': True,
                        'createdAt': int(engagement_date.timestamp() * 1000),
                        'lastUpdated': int(engagement_date.timestamp() * 1000),
                        'type': engagement_type,
                        'ownerId': random.randint(60000000, 60000009),  # CS rep
                        'source': 'CRM_UI',
                        'sourceId': 'userId:12345'
                    },
                    'associations': {
                        'companyIds': [int(company_id)],
                        'contactIds': [int(contact['id']) for contact in contacts_list[:1]]
                    },
                    'metadata': {
                        'subject': self._generate_engagement_subject(engagement_type, 'customer_success'),
                        'body': self._generate_engagement_body(engagement_type, company, 'customer_success')
                    }
                }
                
                engagements.append(engagement)
                engagement_id += 1
                
        logger.info(f"Generated {len(engagements)} HubSpot engagements")
        return engagements
        
    # Helper methods for HubSpot data generation
    def _generate_annual_revenue(self, location_count: int) -> int:
        """Generate realistic annual revenue based on location count"""
        base_revenue_per_location = random.randint(500000, 2000000)  # $500K - $2M per location
        return location_count * base_revenue_per_location + random.randint(-100000, 500000)
        
    def _generate_employee_count(self, location_count: int) -> int:
        """Generate realistic employee count"""
        base_employees = random.randint(8, 25)  # Base employees per location
        return max(1, location_count * base_employees + random.randint(-5, 10))
        
    def _map_business_type_to_industry(self, business_type: str) -> str:
        """Map business type to HubSpot industry categories"""
        industry_mapping = {
            'Restaurant': 'Restaurant',
            'Sports Bar': 'Restaurant', 
            'Brewery': 'Food & Beverage',
            'Wine Bar': 'Restaurant',
            'Cocktail Lounge': 'Entertainment',
            'Sports Grill': 'Restaurant',
            'Pub': 'Restaurant',
            'Nightclub': 'Entertainment',
            'Rooftop Bar': 'Entertainment',
            'Dive Bar': 'Restaurant'
        }
        return industry_mapping.get(business_type, 'Restaurant')
        
    def _determine_customer_tier(self, location_count: int, annual_revenue: int) -> str:
        """Determine customer tier based on size"""
        if location_count >= 10 or annual_revenue >= 10000000:
            return 'Enterprise'
        elif location_count >= 3 or annual_revenue >= 2000000:
            return 'Mid-Market'
        else:
            return 'SMB'
            
    def _generate_contact(self, contact_id: int, company: Dict, is_primary: bool, role: str) -> Dict:
        """Generate individual contact record"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Role-based titles
        titles = {
            'decision_maker': ['Owner', 'General Manager', 'CEO', 'COO'],
            'user': ['Manager', 'Assistant Manager', 'Supervisor', 'Staff'],
            'influencer': ['Operations Manager', 'District Manager', 'Regional Manager'],
            'technical': ['IT Manager', 'Systems Administrator', 'Tech Coordinator'],
            'financial': ['Controller', 'Accountant', 'Financial Manager', 'CFO']
        }
        
        title = random.choice(titles.get(role, ['Manager']))
        
        contact = {
            'id': str(contact_id),
            'properties': {
                'firstname': first_name,
                'lastname': last_name,
                'email': f"{first_name.lower()}.{last_name.lower()}@{company['properties']['domain']}",
                'jobtitle': title,
                'phone': fake.phone_number(),
                'lifecyclestage': 'customer',
                'createdate': company['created_date'].isoformat() + 'Z',
                'hs_lastmodifieddate': company['created_date'].isoformat() + 'Z',
                'associatedcompanyid': company['id'],
                'hubspot_owner_id': str(random.randint(40000000, 40000009)),
                'contact_role': role,
                'is_primary_contact': str(is_primary).lower(),
                'hs_analytics_source': company['properties']['lead_source']
            }
        }
        
        return contact

    def _calculate_deal_value(self, company: Dict) -> int:
        """Calculate realistic deal value based on company characteristics"""
        location_count = company['location_count']
        business_type = company['business_type']
        
        # Base pricing per location per year
        base_price_mapping = {
            'Restaurant': 1800,      # Higher complexity
            'Sports Bar': 1600,      
            'Brewery': 2000,         # Complex inventory
            'Wine Bar': 1400,        
            'Cocktail Lounge': 1500,
            'Sports Grill': 1700,
            'Pub': 1300,
            'Nightclub': 1900,       # Complex operations
            'Rooftop Bar': 1600,
            'Dive Bar': 1200        # Simpler operations
        }
        
        base_price = base_price_mapping.get(business_type, 1500)
        
        # Volume discounts for larger customers
        if location_count >= 10:
            discount = 0.20  # 20% discount for enterprise
        elif location_count >= 5:
            discount = 0.10  # 10% discount for mid-market
        else:
            discount = 0.0   # No discount for SMB
            
        annual_value = int(base_price * location_count * (1 - discount))
        
        # Add some randomness
        variance = random.uniform(0.8, 1.2)
        return int(annual_value * variance)
        
    def _calculate_win_probability(self, company: Dict) -> float:
        """Calculate deal win probability based on company characteristics"""
        base_probability = 0.35  # Base 35% win rate
        
        # Adjust based on company size (larger companies harder to close)
        if company['location_count'] >= 10:
            size_modifier = -0.10
        elif company['location_count'] >= 5:
            size_modifier = 0.0
        else:
            size_modifier = 0.15  # SMB easier to close
            
        # Adjust based on lead source
        source_modifiers = {
            'Referral': 0.25,
            'Website': 0.10,
            'Content Marketing': 0.15,
            'Google Ads': 0.05,
            'Facebook Ads': 0.0,
            'LinkedIn Ads': 0.05,
            'Webinar': 0.20,
            'Trade Show': 0.10,
            'Cold Outreach': -0.15,
            'Organic Search': 0.05
        }
        
        source_modifier = source_modifiers.get(company['properties']['lead_source'], 0.0)
        
        final_probability = base_probability + size_modifier + source_modifier
        return max(0.1, min(0.8, final_probability))  # Clamp between 10-80%
        
    def _get_stage_probability(self, stage: str) -> str:
        """Get probability percentage for deal stage"""
        stage_probabilities = {
            'Lead': '5',
            'Marketing Qualified Lead': '10', 
            'Sales Qualified Lead': '20',
            'Discovery': '30',
            'Demo Scheduled': '40',
            'Proposal': '60',
            'Negotiation': '80',
            'Closed Won': '100',
            'Closed Lost': '0'
        }
        return stage_probabilities.get(stage, '25')
        
    def _determine_ticket_priority(self, category: str) -> str:
        """Determine ticket priority based on category"""
        priority_mapping = {
            'Technical Issue': random.choice(['HIGH', 'MEDIUM', 'MEDIUM', 'LOW']),  # Tech issues often urgent
            'Billing Question': random.choice(['MEDIUM', 'LOW', 'LOW']),
            'Feature Request': 'LOW',
            'Training': 'LOW',
            'Integration Support': random.choice(['HIGH', 'MEDIUM', 'MEDIUM']),
            'Account Management': 'MEDIUM',
            'Bug Report': random.choice(['HIGH', 'HIGH', 'MEDIUM']),  # Bugs often high priority
            'General Inquiry': 'LOW'
        }
        return priority_mapping.get(category, 'MEDIUM')
        
    def _determine_ticket_status(self, ticket_date) -> str:
        """Determine ticket status based on age"""
        # Handle both datetime and date objects
        if hasattr(ticket_date, 'date'):
            ticket_date_obj = ticket_date.date()
        else:
            ticket_date_obj = ticket_date
            
        days_old = (datetime.now().date() - ticket_date_obj).days
        
        if days_old > 30:
            return 'Closed'  # Old tickets are likely closed
        elif days_old > 7:
            return random.choice(['Closed', 'Waiting on customer', 'In progress'])
        else:
            return random.choice(['New', 'In progress', 'Waiting on customer'])
            
    def _generate_ticket_subject(self, category: str) -> str:
        """Generate realistic ticket subjects"""
        subjects = {
            'Technical Issue': [
                'POS System Not Responding',
                'Inventory Scanner Connection Error', 
                'Payment Terminal Offline',
                'Kitchen Display Not Updating',
                'Network Connectivity Issues'
            ],
            'Billing Question': [
                'Question About Recent Invoice',
                'Need Copy of Previous Billing Statement',
                'Pricing Inquiry for Additional Location',
                'Payment Method Update Required'
            ],
            'Feature Request': [
                'Request for Custom Reporting Feature',
                'Integration with Existing POS System',
                'Mobile App Enhancement Request',
                'Custom Dashboard Requirements'
            ],
            'Training': [
                'New Staff Training Session Request',
                'Advanced Features Training Needed',
                'Manager Training for New Location',
                'Refresher Training on Inventory Management'
            ],
            'Integration Support': [
                'Help with QuickBooks Integration',
                'Third-party POS System Setup',
                'API Integration Questions',
                'Data Migration Assistance'
            ],
            'Account Management': [
                'Account Review Meeting Request',
                'Contract Renewal Discussion',
                'Account Expansion Planning',
                'Service Level Review'
            ],
            'Bug Report': [
                'Data Not Syncing Properly',
                'Report Generation Error',
                'Dashboard Display Issue',
                'Mobile App Crash Report'
            ],
            'General Inquiry': [
                'General Product Questions',
                'Service Availability Inquiry',
                'Reference Request',
                'Industry Best Practices Question'
            ]
        }
        
        return random.choice(subjects.get(category, ['General Support Request']))
        
    def _generate_ticket_content(self, category: str, company: Dict) -> str:
        """Generate realistic ticket content"""
        templates = {
            'Technical Issue': f"We're experiencing technical difficulties at {company['name']}. Our {random.choice(['POS system', 'inventory scanner', 'payment terminal'])} has been {random.choice(['unresponsive', 'showing errors', 'disconnecting frequently'])} since {random.choice(['yesterday', 'this morning', 'last night'])}. This is impacting our {random.choice(['daily operations', 'customer service', 'sales processing'])}. Please help resolve this as soon as possible.",
            
            'Billing Question': f"Hi, I'm reviewing our account for {company['name']} and have a question about {random.choice(['our recent invoice', 'the billing cycle', 'payment methods', 'pricing structure'])}. Could someone please {random.choice(['explain the charges', 'provide clarification', 'send documentation', 'schedule a call'])} to help us understand this better?",
            
            'Feature Request': f"Our team at {company['name']} would like to request a new feature for {random.choice(['reporting', 'inventory management', 'staff scheduling', 'customer analytics'])}. Specifically, we need {random.choice(['custom dashboard capabilities', 'integration with our existing systems', 'mobile access', 'automated reporting'])}. This would help us {random.choice(['improve efficiency', 'better serve customers', 'streamline operations', 'make data-driven decisions'])}.",
            
            'Training': f"We need to schedule training for our team at {company['name']}. We have {random.choice(['new staff members', 'a new location opening', 'team members who need refreshers'])} and would like to arrange {random.choice(['on-site training', 'virtual training sessions', 'customized training materials'])}. Please let us know your availability.",
            
            'Integration Support': f"We're trying to integrate our existing {random.choice(['POS system', 'accounting software', 'inventory system', 'scheduling platform'])} with your platform at {company['name']}. We need assistance with {random.choice(['API configuration', 'data mapping', 'testing the connection', 'troubleshooting errors'])}. Can someone from your technical team help us with this?",
            
            'Account Management': f"I'd like to schedule an account review for {company['name']}. We want to discuss {random.choice(['our current service level', 'expansion plans', 'contract renewal', 'additional features'])} and ensure we're getting the most value from our partnership. Please let me know when we can schedule a meeting.",
            
            'Bug Report': f"We've discovered what appears to be a bug in the system at {company['name']}. The issue occurs when {random.choice(['generating reports', 'processing payments', 'updating inventory', 'accessing the dashboard'])} and results in {random.choice(['incorrect data', 'system errors', 'unexpected behavior', 'data not saving'])}. We can reproduce this consistently and have screenshots available.",
            
            'General Inquiry': f"Hi, I have a general question about {random.choice(['your service offerings', 'industry best practices', 'system capabilities', 'future roadmap'])} for {company['name']}. We're {random.choice(['evaluating options', 'planning for growth', 'looking to optimize', 'considering changes'])} and would appreciate any guidance you can provide."
        }
        
        return templates.get(category, f"General support request for {company['name']}.")
        
    def _generate_engagement_subject(self, engagement_type: str, context: str) -> str:
        """Generate realistic engagement subjects"""
        if context == 'sales':
            subjects = {
                'EMAIL': [
                    'Follow-up on Bar Management Demo',
                    'Pricing Proposal for Your Locations',
                    'Next Steps for Implementation',
                    'ROI Analysis for Your Review'
                ],
                'CALL': [
                    'Discovery Call - Bar Management Needs',
                    'Demo Scheduling Call',
                    'Pricing Discussion',
                    'Implementation Planning Call'
                ],
                'MEETING': [
                    'Product Demo Meeting',
                    'Stakeholder Alignment Meeting', 
                    'Contract Discussion Meeting',
                    'Implementation Kickoff Meeting'
                ],
                'NOTE': [
                    'Prospect Research Notes',
                    'Discovery Call Summary',
                    'Demo Feedback Notes',
                    'Decision Timeline Notes'
                ]
            }
        else:  # customer_success
            subjects = {
                'EMAIL': [
                    'Monthly Check-in',
                    'Feature Adoption Review',
                    'Account Health Assessment',
                    'Expansion Opportunity Discussion'
                ],
                'CALL': [
                    'Quarterly Business Review',
                    'Support Resolution Follow-up',
                    'Feature Training Call',
                    'Expansion Planning Call'
                ],
                'MEETING': [
                    'Quarterly Business Review Meeting',
                    'Success Planning Meeting',
                    'Training Session',
                    'Strategy Alignment Meeting'
                ],
                'NOTE': [
                    'Account Health Notes',
                    'Feature Usage Analysis',
                    'Expansion Readiness Assessment',
                    'Risk Mitigation Notes'
                ]
            }
            
        return random.choice(subjects.get(engagement_type, ['General Communication']))
        
    def _generate_engagement_body(self, engagement_type: str, company: Dict, context: str) -> str:
        """Generate realistic engagement content"""
        if context == 'sales':
            if engagement_type == 'EMAIL':
                return f"Following up on our conversation about implementing bar management solutions for {company['name']}. Based on your {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, I've prepared a customized proposal that addresses your specific operational needs."
            elif engagement_type == 'CALL':
                return f"Discovery call with {company['name']} to understand their current challenges with managing {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Discussed pain points around inventory management, POS integration, and operational efficiency."
            elif engagement_type == 'MEETING':
                return f"Product demonstration for {company['name']} stakeholders. Showed key features relevant to {company['business_type'].lower()} operations including real-time inventory tracking, analytics dashboard, and multi-location management capabilities."
            else:  # NOTE
                return f"Researched {company['name']} - {company['business_type'].lower()} with {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Key decision makers identified, competitive landscape analyzed, and initial pain points documented."
        else:  # customer_success
            if engagement_type == 'EMAIL':
                return f"Monthly check-in for {company['name']}. Account is performing well with {company['location_count']} active location{'s' if company['location_count'] > 1 else ''}. Identified opportunities for feature adoption improvement and potential expansion."
            elif engagement_type == 'CALL':
                return f"Quarterly business review with {company['name']}. Reviewed performance metrics, discussed ROI achieved, and planned for upcoming quarter. Account health is strong with opportunities for growth."
            elif engagement_type == 'MEETING':
                return f"Success planning meeting with {company['name']} leadership. Aligned on business objectives, reviewed feature utilization across {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, and identified expansion opportunities."
            else:  # NOTE
                return f"Account health assessment for {company['name']}. Strong engagement across locations, good feature adoption, low support ticket volume. Account is healthy with expansion potential identified."
    # Helper methods for HubSpot data generation
    def _calculate_deal_value(self, company: Dict) -> int:
        """Calculate realistic deal value based on company characteristics"""
        location_count = company['location_count']
        business_type = company['business_type']
        
        # Base pricing per location per year
        base_price_mapping = {
            'Restaurant': 1800,      # Higher complexity
            'Sports Bar': 1600,      
            'Brewery': 2000,         # Complex inventory
            'Wine Bar': 1400,        
            'Cocktail Lounge': 1500,
            'Sports Grill': 1700,
            'Pub': 1300,
            'Nightclub': 1900,       # Complex operations
            'Rooftop Bar': 1600,
            'Dive Bar': 1200        # Simpler operations
        }
        
        base_price = base_price_mapping.get(business_type, 1500)
        
        # Volume discounts for larger customers
        if location_count >= 10:
            discount = 0.20  # 20% discount for enterprise
        elif location_count >= 5:
            discount = 0.10  # 10% discount for mid-market
        else:
            discount = 0.0   # No discount for SMB
            
        annual_value = int(base_price * location_count * (1 - discount))
        
        # Add some randomness
        variance = random.uniform(0.8, 1.2)
        return int(annual_value * variance)
        
    def _calculate_win_probability(self, company: Dict) -> float:
        """Calculate deal win probability based on company characteristics"""
        base_probability = 0.35  # Base 35% win rate
        
        # Adjust based on company size (larger companies harder to close)
        if company['location_count'] >= 10:
            size_modifier = -0.10
        elif company['location_count'] >= 5:
            size_modifier = 0.0
        else:
            size_modifier = 0.15  # SMB easier to close
            
        # Adjust based on lead source
        source_modifiers = {
            'Referral': 0.25,
            'Website': 0.10,
            'Content Marketing': 0.15,
            'Google Ads': 0.05,
            'Facebook Ads': 0.0,
            'LinkedIn Ads': 0.05,
            'Webinar': 0.20,
            'Trade Show': 0.10,
            'Cold Outreach': -0.15,
            'Organic Search': 0.05
        }
        
        source_modifier = source_modifiers.get(company['properties']['lead_source'], 0.0)
        
        final_probability = base_probability + size_modifier + source_modifier
        return max(0.1, min(0.8, final_probability))  # Clamp between 10-80%
        
    def _get_stage_probability(self, stage: str) -> str:
        """Get probability percentage for deal stage"""
        stage_probabilities = {
            'Lead': '5',
            'Marketing Qualified Lead': '10', 
            'Sales Qualified Lead': '20',
            'Discovery': '30',
            'Demo Scheduled': '40',
            'Proposal': '60',
            'Negotiation': '80',
            'Closed Won': '100',
            'Closed Lost': '0'
        }
        return stage_probabilities.get(stage, '25')
        
    def _determine_ticket_priority(self, category: str) -> str:
        """Determine ticket priority based on category"""
        priority_mapping = {
            'Technical Issue': random.choice(['HIGH', 'MEDIUM', 'MEDIUM', 'LOW']),  # Tech issues often urgent
            'Billing Question': random.choice(['MEDIUM', 'LOW', 'LOW']),
            'Feature Request': 'LOW',
            'Training': 'LOW',
            'Integration Support': random.choice(['HIGH', 'MEDIUM', 'MEDIUM']),
            'Account Management': 'MEDIUM',
            'Bug Report': random.choice(['HIGH', 'HIGH', 'MEDIUM']),  # Bugs often high priority
            'General Inquiry': 'LOW'
        }
        return priority_mapping.get(category, 'MEDIUM')
        
    def _determine_ticket_status(self, ticket_date) -> str:
        """Determine ticket status based on age"""
        # Handle both datetime and date objects
        if hasattr(ticket_date, 'date'):
            ticket_date_obj = ticket_date.date()
        else:
            ticket_date_obj = ticket_date
            
        days_old = (datetime.now().date() - ticket_date_obj).days
        
        if days_old > 30:
            return 'Closed'  # Old tickets are likely closed
        elif days_old > 7:
            return random.choice(['Closed', 'Waiting on customer', 'In progress'])
        else:
            return random.choice(['New', 'In progress', 'Waiting on customer'])
            
    def _generate_ticket_subject(self, category: str) -> str:
        """Generate realistic ticket subjects"""
        subjects = {
            'Technical Issue': [
                'POS System Not Responding',
                'Inventory Scanner Connection Error', 
                'Payment Terminal Offline',
                'Kitchen Display Not Updating',
                'Network Connectivity Issues'
            ],
            'Billing Question': [
                'Question About Recent Invoice',
                'Need Copy of Previous Billing Statement',
                'Pricing Inquiry for Additional Location',
                'Payment Method Update Required'
            ],
            'Feature Request': [
                'Request for Custom Reporting Feature',
                'Integration with Existing POS System',
                'Mobile App Enhancement Request',
                'Custom Dashboard Requirements'
            ],
            'Training': [
                'New Staff Training Session Request',
                'Advanced Features Training Needed',
                'Manager Training for New Location',
                'Refresher Training on Inventory Management'
            ],
            'Integration Support': [
                'Help with QuickBooks Integration',
                'Third-party POS System Setup',
                'API Integration Questions',
                'Data Migration Assistance'
            ],
            'Account Management': [
                'Account Review Meeting Request',
                'Contract Renewal Discussion',
                'Account Expansion Planning',
                'Service Level Review'
            ],
            'Bug Report': [
                'Data Not Syncing Properly',
                'Report Generation Error',
                'Dashboard Display Issue',
                'Mobile App Crash Report'
            ],
            'General Inquiry': [
                'General Product Questions',
                'Service Availability Inquiry',
                'Reference Request',
                'Industry Best Practices Question'
            ]
        }
        
        return random.choice(subjects.get(category, ['General Support Request']))
        
    def _generate_ticket_content(self, category: str, company: Dict) -> str:
        """Generate realistic ticket content"""
        templates = {
            'Technical Issue': f"We're experiencing technical difficulties at {company['name']}. Our {random.choice(['POS system', 'inventory scanner', 'payment terminal'])} has been {random.choice(['unresponsive', 'showing errors', 'disconnecting frequently'])} since {random.choice(['yesterday', 'this morning', 'last night'])}. This is impacting our {random.choice(['daily operations', 'customer service', 'sales processing'])}. Please help resolve this as soon as possible.",
            
            'Billing Question': f"Hi, I'm reviewing our account for {company['name']} and have a question about {random.choice(['our recent invoice', 'the billing cycle', 'payment methods', 'pricing structure'])}. Could someone please {random.choice(['explain the charges', 'provide clarification', 'send documentation', 'schedule a call'])} to help us understand this better?",
            
            'Feature Request': f"Our team at {company['name']} would like to request a new feature for {random.choice(['reporting', 'inventory management', 'staff scheduling', 'customer analytics'])}. Specifically, we need {random.choice(['custom dashboard capabilities', 'integration with our existing systems', 'mobile access', 'automated reporting'])}. This would help us {random.choice(['improve efficiency', 'better serve customers', 'streamline operations', 'make data-driven decisions'])}.",
            
            'Training': f"We need to schedule training for our team at {company['name']}. We have {random.choice(['new staff members', 'a new location opening', 'team members who need refreshers'])} and would like to arrange {random.choice(['on-site training', 'virtual training sessions', 'customized training materials'])}. Please let us know your availability.",
            
            'Integration Support': f"We're trying to integrate our existing {random.choice(['POS system', 'accounting software', 'inventory system', 'scheduling platform'])} with your platform at {company['name']}. We need assistance with {random.choice(['API configuration', 'data mapping', 'testing the connection', 'troubleshooting errors'])}. Can someone from your technical team help us with this?",
            
            'Account Management': f"I'd like to schedule an account review for {company['name']}. We want to discuss {random.choice(['our current service level', 'expansion plans', 'contract renewal', 'additional features'])} and ensure we're getting the most value from our partnership. Please let me know when we can schedule a meeting.",
            
            'Bug Report': f"We've discovered what appears to be a bug in the system at {company['name']}. The issue occurs when {random.choice(['generating reports', 'processing payments', 'updating inventory', 'accessing the dashboard'])} and results in {random.choice(['incorrect data', 'system errors', 'unexpected behavior', 'data not saving'])}. We can reproduce this consistently and have screenshots available.",
            
            'General Inquiry': f"Hi, I have a general question about {random.choice(['your service offerings', 'industry best practices', 'system capabilities', 'future roadmap'])} for {company['name']}. We're {random.choice(['evaluating options', 'planning for growth', 'looking to optimize', 'considering changes'])} and would appreciate any guidance you can provide."
        }
        
        return templates.get(category, f"General support request for {company['name']}.")
        
    def _generate_engagement_subject(self, engagement_type: str, context: str) -> str:
        """Generate realistic engagement subjects"""
        if context == 'sales':
            subjects = {
                'EMAIL': [
                    'Follow-up on Bar Management Demo',
                    'Pricing Proposal for Your Locations',
                    'Next Steps for Implementation',
                    'ROI Analysis for Your Review'
                ],
                'CALL': [
                    'Discovery Call - Bar Management Needs',
                    'Demo Scheduling Call',
                    'Pricing Discussion',
                    'Implementation Planning Call'
                ],
                'MEETING': [
                    'Product Demo Meeting',
                    'Stakeholder Alignment Meeting', 
                    'Contract Discussion Meeting',
                    'Implementation Kickoff Meeting'
                ],
                'NOTE': [
                    'Prospect Research Notes',
                    'Discovery Call Summary',
                    'Demo Feedback Notes',
                    'Decision Timeline Notes'
                ]
            }
        else:  # customer_success
            subjects = {
                'EMAIL': [
                    'Monthly Check-in',
                    'Feature Adoption Review',
                    'Account Health Assessment',
                    'Expansion Opportunity Discussion'
                ],
                'CALL': [
                    'Quarterly Business Review',
                    'Support Resolution Follow-up',
                    'Feature Training Call',
                    'Expansion Planning Call'
                ],
                'MEETING': [
                    'Quarterly Business Review Meeting',
                    'Success Planning Meeting',
                    'Training Session',
                    'Strategy Alignment Meeting'
                ],
                'NOTE': [
                    'Account Health Notes',
                    'Feature Usage Analysis',
                    'Expansion Readiness Assessment',
                    'Risk Mitigation Notes'
                ]
            }
            
        return random.choice(subjects.get(engagement_type, ['General Communication']))
        
    def _generate_engagement_body(self, engagement_type: str, company: Dict, context: str) -> str:
        """Generate realistic engagement content"""
        if context == 'sales':
            if engagement_type == 'EMAIL':
                return f"Following up on our conversation about implementing bar management solutions for {company['name']}. Based on your {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, I've prepared a customized proposal that addresses your specific operational needs."
            elif engagement_type == 'CALL':
                return f"Discovery call with {company['name']} to understand their current challenges with managing {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Discussed pain points around inventory management, POS integration, and operational efficiency."
            elif engagement_type == 'MEETING':
                return f"Product demonstration for {company['name']} stakeholders. Showed key features relevant to {company['business_type'].lower()} operations including real-time inventory tracking, analytics dashboard, and multi-location management capabilities."
            else:  # NOTE
                return f"Researched {company['name']} - {company['business_type'].lower()} with {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Key decision makers identified, competitive landscape analyzed, and initial pain points documented."
        else:  # customer_success
            if engagement_type == 'EMAIL':
                return f"Monthly check-in for {company['name']}. Account is performing well with {company['location_count']} active location{'s' if company['location_count'] > 1 else ''}. Identified opportunities for feature adoption improvement and potential expansion."
            elif engagement_type == 'CALL':
                return f"Quarterly business review with {company['name']}. Reviewed performance metrics, discussed ROI achieved, and planned for upcoming quarter. Account health is strong with opportunities for growth."
            elif engagement_type == 'MEETING':
                return f"Success planning meeting with {company['name']} leadership. Aligned on business objectives, reviewed feature utilization across {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, and identified expansion opportunities."
            else:  # NOTE
                return f"Account health assessment for {company['name']}. Strong engagement across locations, good feature adoption, low support ticket volume. Account is healthy with expansion potential identified."