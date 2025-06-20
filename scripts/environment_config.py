#!/usr/bin/env python3
"""
Environment size configuration for synthetic data generation.

This module defines the scaling factors for different environments:
- DEV: Small dataset for rapid testing
- QA: Medium dataset for integration testing  
- PRODUCTION: Large dataset for performance testing
"""

import os
from environs import Env
from dataclasses import dataclass

# Initialize environment variable reader
env = Env()
env.read_env()

@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment size"""
    name: str
    # Core entities
    accounts: int
    locations: int
    users: int
    devices: int
    subscriptions: int
    
    # Event data
    tap_events: int
    user_sessions: int
    page_views: int
    feature_usage_events: int
    
    # Stripe billing
    stripe_customers: int
    stripe_subscriptions: int
    stripe_subscription_items: int
    stripe_invoices: int
    stripe_charges: int
    stripe_events: int
    
    # HubSpot CRM
    hubspot_companies: int
    hubspot_contacts: int
    hubspot_deals: int
    hubspot_engagements: int
    hubspot_tickets: int
    
    # Marketing
    campaigns: int
    campaign_performance_records: int
    attribution_touchpoints: int
    marketing_qualified_leads: int
    google_analytics_sessions: int
    
    @property
    def locations_per_account(self):
        return self.locations / self.accounts if self.accounts > 0 else 0
    
    @property
    def users_per_account(self):
        return self.users / self.accounts if self.accounts > 0 else 0
    
    @property
    def devices_per_location(self):
        return self.devices / self.locations if self.locations > 0 else 0
    
    @property
    def tap_events_per_device(self):
        return self.tap_events / self.devices if self.devices > 0 else 0

# Define environment configurations
ENVIRONMENTS = {
    'DEV': EnvironmentConfig(
        name='DEV',
        # Core entities
        accounts=100,
        locations=150,  # ~1.5 per account
        users=300,      # ~3 per account
        devices=450,    # ~3 per location
        subscriptions=125,
        
        # Event data
        tap_events=500_000,  # ~1.1K per device
        user_sessions=50_000,
        page_views=250_000,
        feature_usage_events=150_000,
        
        # Stripe billing  
        stripe_customers=100,
        stripe_subscriptions=125,
        stripe_subscription_items=175,
        stripe_invoices=1_500,
        stripe_charges=1_425,
        stripe_events=10_000,
        
        # HubSpot CRM
        hubspot_companies=125,
        hubspot_contacts=500,
        hubspot_deals=250,
        hubspot_engagements=2_500,
        hubspot_tickets=400,
        
        # Marketing
        campaigns=25,
        campaign_performance_records=7_500,
        attribution_touchpoints=15_000,
        marketing_qualified_leads=200,
        google_analytics_sessions=30_000
    ),
    
    'QA': EnvironmentConfig(
        name='QA',
        # Core entities
        accounts=10_000,
        locations=15_000,  # ~1.5 per account
        users=30_000,      # ~3 per account  
        devices=45_000,    # ~3 per location
        subscriptions=12_500,
        
        # Event data
        tap_events=50_000_000,  # ~1.1K per device
        user_sessions=2_500_000,
        page_views=12_500_000,
        feature_usage_events=7_500_000,
        
        # Stripe billing
        stripe_customers=10_000,
        stripe_subscriptions=12_500,
        stripe_subscription_items=17_500,
        stripe_invoices=150_000,
        stripe_charges=142_500,
        stripe_events=1_000_000,
        
        # HubSpot CRM
        hubspot_companies=12_500,
        hubspot_contacts=50_000,
        hubspot_deals=25_000,
        hubspot_engagements=250_000,
        hubspot_tickets=40_000,
        
        # Marketing
        campaigns=1_250,
        campaign_performance_records=375_000,
        attribution_touchpoints=750_000,
        marketing_qualified_leads=20_000,
        google_analytics_sessions=1_500_000
    ),
    
    'PRODUCTION': EnvironmentConfig(
        name='PRODUCTION',
        # Core entities
        accounts=40_000,
        locations=60_000,   # ~1.5 per account
        users=120_000,      # ~3 per account
        devices=180_000,    # ~3 per location
        subscriptions=50_000,
        
        # Event data
        tap_events=200_000_000,  # ~1.1K per device
        user_sessions=10_000_000,
        page_views=50_000_000,
        feature_usage_events=30_000_000,
        
        # Stripe billing
        stripe_customers=40_000,
        stripe_subscriptions=50_000,
        stripe_subscription_items=70_000,
        stripe_invoices=600_000,
        stripe_charges=570_000,
        stripe_events=4_000_000,
        
        # HubSpot CRM
        hubspot_companies=50_000,
        hubspot_contacts=200_000,
        hubspot_deals=100_000,
        hubspot_engagements=1_000_000,
        hubspot_tickets=160_000,
        
        # Marketing
        campaigns=5_000,
        campaign_performance_records=1_500_000,
        attribution_touchpoints=3_000_000,
        marketing_qualified_leads=80_000,
        google_analytics_sessions=6_000_000
    )
}

def get_environment_config():
    """Get the configuration for the current environment"""
    env_name = env.str('DATAGEN_ENV', default='DEV').upper()
    
    if env_name not in ENVIRONMENTS:
        print(f"⚠️  Warning: Unknown environment '{env_name}', defaulting to DEV")
        env_name = 'DEV'
    
    config = ENVIRONMENTS[env_name]
    print(f"✓ Using {env_name} environment configuration")
    return config

# Create singleton instance
current_env = get_environment_config()

if __name__ == "__main__":
    # Display current environment configuration
    print(f"\n{'='*60}")
    print(f"Environment Configuration: {current_env.name}")
    print(f"{'='*60}")
    
    print("\nCore Entities:")
    print(f"  Accounts: {current_env.accounts:,}")
    print(f"  Locations: {current_env.locations:,} (~{current_env.locations_per_account:.1f} per account)")
    print(f"  Users: {current_env.users:,} (~{current_env.users_per_account:.1f} per account)")
    print(f"  Devices: {current_env.devices:,} (~{current_env.devices_per_location:.1f} per location)")
    print(f"  Subscriptions: {current_env.subscriptions:,}")
    
    print("\nEvent Data:")
    print(f"  Tap Events: {current_env.tap_events:,} (~{current_env.tap_events_per_device:.0f} per device)")
    print(f"  User Sessions: {current_env.user_sessions:,}")
    print(f"  Page Views: {current_env.page_views:,}")
    
    print("\nTotal Records Estimate:")
    total = (current_env.accounts + current_env.locations + current_env.users + 
             current_env.devices + current_env.tap_events + current_env.stripe_events +
             current_env.hubspot_engagements + current_env.google_analytics_sessions)
    print(f"  {total:,} total records across all tables")
