#!/usr/bin/env python3
"""
Synthetic Data Generator for Bar Management SaaS Platform
=========================================================

Generates comprehensive, realistic synthetic data for a bar management platform
serving 20,000+ accounts across 30,000+ locations with complete business logic,
seasonal patterns, and cross-system relationships.

Business Context:
- Multi-location bar/restaurant chains
- IoT devices for inventory/POS management
- Subscription-based SaaS model
- Complex marketing attribution
- Customer success management

Architecture:
- Stripe: Billing and subscription management
- HubSpot: CRM and sales pipeline
- Marketing: Multi-channel attribution
- Device: IoT sensor and POS data
"""

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

# Add the current script directory to path for imports
sys.path.append(os.path.dirname(__file__))

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
    def create(cls, scale: str, months_back: int = 60) -> 'PlatformConfig':  # 5 years default
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

class StripeDataGenerator(BusinessEntityGenerator):
    """Generate Stripe billing and subscription data"""
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.subscription_plans = {
            'starter': {'monthly': 49, 'annual': 490},
            'professional': {'monthly': 149, 'annual': 1490},
            'enterprise': {'monthly': 399, 'annual': 3990}
        }
        
    def _safe_timestamp(self, dt_obj) -> int:
        """Safely convert date or datetime to timestamp"""
        if isinstance(dt_obj, datetime):
            return int(dt_obj.timestamp())
        elif isinstance(dt_obj, date):
            return int(datetime.combine(dt_obj, datetime.min.time()).timestamp())
        elif isinstance(dt_obj, str):
            # Handle string dates
            try:
                if 'T' in dt_obj:
                    dt = datetime.fromisoformat(dt_obj.replace('Z', ''))
                else:
                    dt = datetime.fromisoformat(dt_obj)
                return int(dt.timestamp())
            except:
                return int(datetime.now().timestamp())
        else:
            return int(datetime.now().timestamp())
        
    def generate_customers(self, companies: List[Dict]) -> List[Dict]:
        """Generate Stripe customer records"""
        customers = []
        
        for company in companies:
            # Get company email and created date safely
            company_email = company.get('email', f"contact@{fake.company_email()}")
            if 'properties' in company:
                company_name = company['properties'].get('name', fake.company())
                company_email = company['properties'].get('email', company_email)
                created_date = company['properties'].get('createdate', fake.date_between(start_date='-2y', end_date='now'))
            else:
                company_name = company.get('name', fake.company())
                created_date = company.get('created_date', fake.date_between(start_date='-2y', end_date='now'))
            
            customer = {
                'id': f"cus_{fake.lexify(text='??????????????')}",
                'email': company_email,
                'name': company_name,
                'description': f"Customer for {company_name}",
                'created': self._safe_timestamp(created_date),
                'currency': 'usd',
                'delinquent': False,
                'metadata': {
                    'hubspot_company_id': str(company['id']),
                    'business_type': company.get('business_type', 'Restaurant'),
                    'location_count': company.get('location_count', 1)
                }
            }
            customers.append(customer)
            
        logger.info(f"Generated {len(customers)} Stripe customers")
        return customers
        
    def generate_prices(self) -> List[Dict]:
        """Generate Stripe price records for subscription plans"""
        prices = []
        
        for plan, pricing in self.subscription_plans.items():
            for interval, amount in pricing.items():
                price = {
                    'id': f"price_{plan}_{interval}",
                    'object': 'price',
                    'active': True,
                    'billing_scheme': 'per_unit',
                    'created': self._safe_timestamp(self.config.start_date),
                    'currency': 'usd',
                    'metadata': {
                        'plan_name': plan,
                        'billing_interval': interval
                    },
                    'nickname': f"{plan.title()} {interval.title()}",
                    'product': f"prod_{plan}",
                    'recurring': {
                        'interval': 'month' if interval == 'monthly' else 'year',
                        'interval_count': 1,
                        'usage_type': 'licensed'
                    },
                    'tax_behavior': 'exclusive',
                    'type': 'recurring',
                    'unit_amount': amount * 100,  # Stripe uses cents
                    'unit_amount_decimal': str(amount * 100)
                }
                prices.append(price)
                
        logger.info(f"Generated {len(prices)} Stripe prices")
        return prices
        
    def generate_subscriptions(self, customers: List[Dict], locations_data: List[Dict]) -> List[Dict]:
        """Generate subscription lifecycle with realistic business patterns"""
        subscriptions = []
        
        # Group locations by customer for subscription logic
        customer_locations = {}
        for location in locations_data:
            customer_id = str(location['customer_id'])
            if customer_id not in customer_locations:
                customer_locations[customer_id] = []
            customer_locations[customer_id].append(location)
            
        for customer in customers:
            customer_stripe_id = customer['id']
            hubspot_id = customer['metadata']['hubspot_company_id']
            locations = customer_locations.get(hubspot_id, [])
            
            # Determine subscription plan based on location count
            location_count = len(locations)
            if location_count <= 2:
                plan = 'starter'
            elif location_count <= 10:
                plan = 'professional'
            else:
                plan = 'enterprise'
                
            # Determine billing interval (70% monthly, 30% annual)
            interval = 'monthly' if random.random() < 0.7 else 'annual'
            price_id = f"price_{plan}_{interval}"
            
            # Create subscription with realistic lifecycle
            subscription_start = fake.date_time_between(
                start_date=datetime.fromtimestamp(customer['created']),
                end_date='now'
            )
            subscription_id = f"sub_{fake.lexify(text='??????????????')}"
            
            # Trial period (14 days)
            trial_end = subscription_start + timedelta(days=14)
            
            # Determine if customer converts from trial
            converts_from_trial = random.random() < self.config.trial_conversion_rate
            
            if converts_from_trial:
                status = 'active'
                current_period_start = trial_end
                
                # Check for churn during subscription period
                months_since_start = (datetime.now() - trial_end).days // 30
                churn_probability = 1 - (1 - self.config.monthly_churn_rate) ** max(1, months_since_start)
                
                if random.random() < churn_probability:
                    # Customer churned at some point
                    churn_month = random.randint(1, max(1, months_since_start))
                    churn_date = trial_end + timedelta(days=churn_month * 30)
                    status = 'canceled'
                    canceled_at = churn_date
                else:
                    canceled_at = None
                    
            else:
                # Customer didn't convert from trial
                status = 'canceled'
                current_period_start = trial_end
                canceled_at = trial_end
                
            subscription = {
                'id': subscription_id,
                'object': 'subscription',
                'application_fee_percent': None,
                'billing_cycle_anchor': self._safe_timestamp(trial_end),
                'billing_thresholds': None,
                'cancel_at': None,
                'cancel_at_period_end': False,
                'canceled_at': self._safe_timestamp(canceled_at) if canceled_at else None,
                'collection_method': 'charge_automatically',
                'created': self._safe_timestamp(subscription_start),
                'current_period_end': self._safe_timestamp(current_period_start + timedelta(days=30 if interval == 'monthly' else 365)),
                'current_period_start': self._safe_timestamp(current_period_start),
                'customer': customer_stripe_id,
                'days_until_due': None,
                'default_payment_method': f"pm_{fake.lexify(text='??????????????')}",
                'discount': None,
                'ended_at': self._safe_timestamp(canceled_at) if canceled_at else None,
                'items': {
                    'object': 'list',
                    'data': [
                        {
                            'id': f"si_{fake.lexify(text='??????????????')}",
                            'object': 'subscription_item',
                            'billing_thresholds': None,
                            'created': self._safe_timestamp(subscription_start),
                            'metadata': {},
                            'price': {
                                'id': price_id,
                                'object': 'price',
                                'active': True,
                                'billing_scheme': 'per_unit',
                                'created': self._safe_timestamp(self.config.start_date),
                                'currency': 'usd',
                                'metadata': {},
                                'nickname': f"{plan.title()} {interval.title()}",
                                'product': f"prod_{plan}",
                                'recurring': {
                                    'interval': 'month' if interval == 'monthly' else 'year',
                                    'interval_count': 1,
                                    'usage_type': 'licensed'
                                },
                                'tax_behavior': 'exclusive',
                                'type': 'recurring',
                                'unit_amount': self.subscription_plans[plan][interval] * 100,
                                'unit_amount_decimal': str(self.subscription_plans[plan][interval] * 100)
                            },
                            'quantity': max(1, location_count),  # One license per location
                            'subscription': subscription_id,
                            'tax_rates': []
                        }
                    ],
                    'has_more': False,
                    'total_count': 1,
                    'url': f"/v1/subscription_items?subscription={subscription_id}"
                },
                'latest_invoice': f"in_{fake.lexify(text='??????????????')}",
                'livemode': False,
                'metadata': {
                    'hubspot_company_id': hubspot_id,
                    'plan_name': plan,
                    'location_count': str(location_count)
                },
                'next_pending_invoice_item_invoice': None,
                'pause_collection': None,
                'payment_settings': {
                    'payment_method_options': None,
                    'payment_method_types': None,
                    'save_default_payment_method': 'off'
                },
                'pending_invoice_item_interval': None,
                'pending_setup_intent': None,
                'pending_update': None,
                'schedule': None,
                'start_date': self._safe_timestamp(subscription_start),
                'status': status,
                'transfer_data': None,
                'trial_end': self._safe_timestamp(trial_end),
                'trial_start': self._safe_timestamp(subscription_start)
            }
            
            subscriptions.append(subscription)
            
        logger.info(f"Generated {len(subscriptions)} Stripe subscriptions")
        return subscriptions

    def generate_charges(self, subscriptions: List[Dict]) -> List[Dict]:
        """Generate Stripe charges with correct schema"""
        charges = []
        
        for subscription in subscriptions:
            # Generate 1-12 charges per subscription (billing history)
            num_charges = random.randint(1, 12)
            
            for _ in range(num_charges):
                amount = random.choice([4999, 9999, 19999, 39999])  # in cents
                
                charge = {
                    'id': f"ch_{fake.lexify(text='?' * 24)}",
                    'object': 'charge',
                    'amount': amount,
                    'currency': 'usd',
                    'customer': subscription.get('customer', ''),
                    'description': 'Subscription payment',
                    'created': self._safe_timestamp(fake.date_time_between(start_date='-2y', end_date='now')),
                    'paid': True,
                    'status': 'succeeded'
                }
                charges.append(charge)
        
        logger.info(f"Generated {len(charges)} Stripe charges")
        return charges
    
    def generate_events(self, count: int = None) -> List[Dict]:
        """Generate Stripe webhook events"""
        if count is None:
            count = min(1000, self.config.customers * 2)  # Scale with customer count
            
        events = []
        
        event_types = [
            'customer.created', 'customer.updated', 'charge.succeeded',
            'invoice.payment_succeeded', 'subscription.created'
        ]
        
        for i in range(count):
            event = {
                'id': f"evt_{fake.lexify(text='?' * 24)}",
                'object': 'event',
                'type': random.choice(event_types),
                'created': self._safe_timestamp(fake.date_time_between(start_date='-2y', end_date='now')),
                'data': {'object': {'id': 'placeholder'}},
                'livemode': False
            }
            events.append(event)
        
        logger.info(f"Generated {len(events)} Stripe events")
        return events
    
    def generate_invoices(self, subscriptions: List[Dict]) -> List[Dict]:
        """Generate Stripe invoices"""
        invoices = []
        
        for subscription in subscriptions:
            # Generate 1-6 invoices per subscription
            num_invoices = random.randint(1, 6)
            
            for _ in range(num_invoices):
                amount = random.choice([4999, 9999, 19999])
                
                invoice = {
                    'id': f"in_{fake.lexify(text='?' * 24)}",
                    'object': 'invoice',
                    'amount_due': amount,
                    'amount_paid': amount,
                    'currency': 'usd',
                    'customer': subscription.get('customer', ''),
                    'created': self._safe_timestamp(fake.date_time_between(start_date='-2y', end_date='now')),
                    'status': random.choice(['paid', 'open']),
                    'subscription': subscription.get('id', '')
                }
                invoices.append(invoice)
        
        logger.info(f"Generated {len(invoices)} Stripe invoices")
        return invoices
    
    def generate_payment_intents(self, customers: List[Dict], count: int = None) -> List[Dict]:
        """Generate Stripe payment intents"""
        if count is None:
            count = min(50, len(customers) // 2)  # Scale with customer count
        
        payment_intents = []
        
        for i in range(count):
            customer = random.choice(customers)
            
            intent = {
                'id': f"pi_{fake.lexify(text='?' * 24)}",
                'object': 'payment_intent',
                'amount': random.choice([4999, 9999, 19999]),
                'currency': 'usd',
                'customer': customer['id'],
                'created': self._safe_timestamp(fake.date_time_between(start_date='-2y', end_date='now')),
                'status': 'succeeded'
            }
            payment_intents.append(intent)
        
        logger.info(f"Generated {len(payment_intents)} Stripe payment intents")
        return payment_intents
    
    def generate_subscription_items(self, subscriptions: List[Dict]) -> List[Dict]:
        """Generate Stripe subscription items"""
        subscription_items = []
        
        for subscription in subscriptions:
            # Each subscription has 1-2 items
            num_items = random.randint(1, 2)
            
            for _ in range(num_items):
                item = {
                    'id': f"si_{fake.lexify(text='?' * 24)}",
                    'object': 'subscription_item',
                    'subscription': subscription.get('id', ''),
                    'quantity': random.randint(1, 5),
                    'created': self._safe_timestamp(fake.date_time_between(start_date='-2y', end_date='now'))
                }
                subscription_items.append(item)
        
        logger.info(f"Generated {len(subscription_items)} Stripe subscription items")
        return subscription_items

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate synthetic data for bar management SaaS platform')
    parser.add_argument('scale', choices=['xs', 'small', 'enterprise'], nargs='?', default='xs',
                      help='Data generation scale: xs (100), small (1K), or enterprise (40K customers)')
    parser.add_argument('--months', type=int, default=60,
                      help='Months of historical data (default: 60 = 5 years)')
    parser.add_argument('--output', default='/Users/lane/Development/Active/data-platform/data/synthetic',
                      help='Output directory for generated data')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                      help='Output format (default: json)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = PlatformConfig.create(args.scale, args.months)
    logger.info(f"Generating {config.scale.value} scale data for {args.months} months")
    logger.info(f"Date range: {config.start_date} to {config.end_date}")
    logger.info(f"Target customers: {config.customers}")
    
    # Create output directory structure
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(f"{args.output}/hubspot", exist_ok=True)
    os.makedirs(f"{args.output}/stripe", exist_ok=True)
    os.makedirs(f"{args.output}/marketing", exist_ok=True)
    os.makedirs(f"{args.output}/devices", exist_ok=True)
    
    # Import additional generators
    sys.path.append('/Users/lane/Development/Active/data-platform/scripts')
    from hubspot_generator import HubSpotDataGenerator
    from marketing_generator import MarketingDataGenerator
    from device_generator import DeviceDataGenerator
    
    # Initialize all generators
    logger.info("Initializing data generators...")
    hubspot_gen = HubSpotDataGenerator(config)
    stripe_gen = StripeDataGenerator(config)
    marketing_gen = MarketingDataGenerator(config)
    device_gen = DeviceDataGenerator(config)
    
    # Step 1: Generate HubSpot CRM data (foundation)
    logger.info("🏗️  Step 1: Generating HubSpot CRM data...")
    companies = hubspot_gen.generate_companies()
    contacts = hubspot_gen.generate_contacts(companies)
    deals = hubspot_gen.generate_deals(companies, contacts)
    tickets = hubspot_gen.generate_tickets(companies, contacts)
    owners = hubspot_gen.generate_owners()
    engagements = hubspot_gen.generate_engagements(companies, contacts, deals)
    
    # Step 2: Generate location and device data
    logger.info("📍 Step 2: Generating locations and IoT devices...")
    locations = device_gen.generate_locations(companies)
    devices = device_gen.generate_devices(locations)
    users = device_gen.generate_user_activity(companies, locations)
    
    # Generate additional app database tables
    logger.info("📱 Step 2a: Generating app database analytics...")
    feature_usage = device_gen.generate_feature_usage(users)
    page_views = device_gen.generate_page_views(users)
    user_sessions = device_gen.generate_user_sessions(users)
    app_subscriptions = device_gen.generate_app_subscriptions(companies)
    
    # Step 3: Generate Stripe billing data
    logger.info("💳 Step 3: Generating Stripe billing data...")
    stripe_customers = stripe_gen.generate_customers(companies)
    stripe_prices = stripe_gen.generate_prices()
    stripe_subscriptions = stripe_gen.generate_subscriptions(stripe_customers, locations)
    
    # Generate additional Stripe tables
    logger.info("💳 Step 3a: Generating additional Stripe data...")
    stripe_charges = stripe_gen.generate_charges(stripe_subscriptions)
    stripe_events = stripe_gen.generate_events()
    stripe_invoices = stripe_gen.generate_invoices(stripe_subscriptions)
    stripe_payment_intents = stripe_gen.generate_payment_intents(stripe_customers)
    stripe_subscription_items = stripe_gen.generate_subscription_items(stripe_subscriptions)
    
    # Step 4: Generate marketing attribution data
    logger.info("📈 Step 4: Generating marketing campaigns...")
    google_ads_campaigns = marketing_gen.generate_google_ads_campaigns(companies)
    facebook_ads_campaigns = marketing_gen.generate_facebook_ads_campaigns(companies)
    linkedin_ads_campaigns = marketing_gen.generate_linkedin_ads_campaigns(companies)
    iterable_campaigns = marketing_gen.generate_iterable_campaigns(companies)
    google_analytics_sessions = marketing_gen.generate_google_analytics_sessions(companies)
    
    # Combine campaign data for attribution
    campaigns_data = {
        'google_ads': google_ads_campaigns,
        'facebook_ads': facebook_ads_campaigns,
        'linkedin_ads': linkedin_ads_campaigns,
        'iterable': iterable_campaigns
    }
    
    mqls = marketing_gen.generate_marketing_qualified_leads(companies, campaigns_data)
    attribution_touchpoints = marketing_gen.generate_attribution_touchpoints(companies, mqls, campaigns_data)
    
    # Step 5: Save all data
    logger.info("💾 Step 5: Saving generated data...")
    
    def save_data(data, filename, subfolder=None):
        """Save data in specified format"""
        if subfolder:
            filepath = f"{args.output}/{subfolder}/{filename}"
        else:
            filepath = f"{args.output}/{filename}"
            
        if args.format == 'json':
            with open(f"{filepath}.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:  # csv
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df.to_csv(f"{filepath}.csv", index=False)
    
    # Save HubSpot data
    save_data(companies, "companies", "hubspot")
    save_data(contacts, "contacts", "hubspot")
    save_data(deals, "deals", "hubspot")
    save_data(tickets, "tickets", "hubspot")
    save_data(owners, "owners", "hubspot")
    save_data(engagements, "engagements", "hubspot")
    
    # Save Stripe data
    save_data(stripe_customers, "customers", "stripe")
    save_data(stripe_prices, "prices", "stripe")
    save_data(stripe_subscriptions, "subscriptions", "stripe")
    save_data(stripe_charges, "charges", "stripe")
    save_data(stripe_events, "events", "stripe")
    save_data(stripe_invoices, "invoices", "stripe")
    save_data(stripe_payment_intents, "payment_intents", "stripe")
    save_data(stripe_subscription_items, "subscription_items", "stripe")
    
    # Save marketing data
    save_data(google_ads_campaigns, "google_ads_campaigns", "marketing")
    save_data(facebook_ads_campaigns, "facebook_ads_campaigns", "marketing")
    save_data(linkedin_ads_campaigns, "linkedin_ads_campaigns", "marketing")
    save_data(iterable_campaigns, "iterable_campaigns", "marketing")
    save_data(google_analytics_sessions, "google_analytics_sessions", "marketing")
    save_data(mqls, "marketing_qualified_leads", "marketing")
    save_data(attribution_touchpoints, "attribution_touchpoints", "marketing")
    
    # Save device and location data
    save_data(locations, "locations", "devices")
    save_data(devices, "devices", "devices")
    save_data(users, "users", "devices")
    save_data(feature_usage, "feature_usage", "devices")
    save_data(page_views, "page_views", "devices")
    save_data(user_sessions, "user_sessions", "devices")
    save_data(app_subscriptions, "subscriptions", "devices")
    
    # Step 6: Generate device events (large dataset - handle separately)
    logger.info("📊 Step 6: Generating device event streams...")
    event_batches_saved = 0
    
    for event_batch in device_gen.generate_device_events(devices):
        batch_filename = f"device_events_batch_{event_batches_saved:03d}"
        save_data(event_batch, batch_filename, "devices")
        event_batches_saved += 1
        
    logger.info(f"Generated {event_batches_saved} batches of device events")
    
    # Step 7: Generate summary statistics
    logger.info("📈 Step 7: Generating summary statistics...")
    
    summary_stats = {
        'generation_config': {
            'scale': config.scale.value,
            'date_range': {
                'start_date': config.start_date.isoformat(),
                'end_date': config.end_date.isoformat(),
                'total_days': (config.end_date - config.start_date).days
            },
            'generation_timestamp': datetime.now().isoformat()
        },
        'data_volumes': {
            'companies': len(companies),
            'contacts': len(contacts),
            'deals': len(deals),
            'tickets': len(tickets),
            'owners': len(owners),
            'engagements': len(engagements),
            'locations': len(locations),
            'devices': len(devices),
            'users': len(users),
            'feature_usage': len(feature_usage),
            'page_views': len(page_views),
            'user_sessions': len(user_sessions),
            'app_subscriptions': len(app_subscriptions),
            'stripe_customers': len(stripe_customers),
            'stripe_subscriptions': len(stripe_subscriptions),
            'stripe_charges': len(stripe_charges),
            'stripe_events': len(stripe_events),
            'stripe_invoices': len(stripe_invoices),
            'stripe_payment_intents': len(stripe_payment_intents),
            'stripe_subscription_items': len(stripe_subscription_items),
            'google_ads_campaigns': len(google_ads_campaigns),
            'facebook_ads_campaigns': len(facebook_ads_campaigns),
            'linkedin_ads_campaigns': len(linkedin_ads_campaigns),
            'iterable_campaigns': len(iterable_campaigns),
            'marketing_qualified_leads': len(mqls),
            'attribution_touchpoints': len(attribution_touchpoints),
            'device_event_batches': event_batches_saved
        },
        'business_metrics': {
            'total_locations': len(locations),
            'total_devices': len(devices),
            'avg_devices_per_location': len(devices) / len(locations) if locations else 0,
            'avg_locations_per_customer': len(locations) / len(companies) if companies else 0,
            'total_campaigns': len(google_ads_campaigns) + len(facebook_ads_campaigns) + len(linkedin_ads_campaigns),
            'total_marketing_spend': sum([
                sum([c.get('performance_stats', {}).get('cost', 0) for c in google_ads_campaigns]),
                sum([c.get('performance_stats', {}).get('spend', 0) for c in facebook_ads_campaigns]),
                sum([c.get('performance_stats', {}).get('cost_in_usd', 0) for c in linkedin_ads_campaigns])
            ])
        }
    }
    
    save_data(summary_stats, "generation_summary")
    
    logger.info("🎉 Synthetic data generation completed successfully!")
    logger.info(f"📊 Generated data for {len(companies)} companies with {len(locations)} locations")
    logger.info(f"💻 Created {len(devices)} IoT devices with {event_batches_saved} event batches")
    logger.info(f"📈 Built {len(mqls)} marketing qualified leads from {len(attribution_touchpoints)} touchpoints")
    logger.info(f"📱 Generated {len(feature_usage)} feature usage, {len(page_views)} page views, {len(user_sessions)} user sessions")
    logger.info(f"💳 Created complete Stripe data: {len(stripe_charges)} charges, {len(stripe_invoices)} invoices, {len(stripe_events)} events")
    logger.info(f"💾 All data saved to: {args.output}")

if __name__ == "__main__":
    main()
