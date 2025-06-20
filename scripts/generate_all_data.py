#!/usr/bin/env python3
"""
Generate all data for the SaaS platform in the correct order
"""

import subprocess
import sys
import os

# List of generation scripts in dependency order
generators = [
    "generate_accounts.py",        # Core accounts (already done)
    "generate_locations.py",       # Locations for accounts
    "generate_users.py",           # Users for accounts
    "generate_devices.py",         # Devices for locations
    "generate_subscriptions.py",   # Account subscriptions
    
    # Stripe billing data
    "generate_stripe_customers.py",
    "generate_stripe_prices.py",
    "generate_stripe_subscriptions.py",
    "generate_stripe_subscription_items.py",
    "generate_stripe_invoices.py",
    "generate_stripe_charges.py",
    "generate_stripe_events.py",
    
    # HubSpot CRM data
    "generate_hubspot_companies.py",
    "generate_hubspot_contacts.py",
    "generate_hubspot_deals.py",
    "generate_hubspot_engagements.py",
    "generate_hubspot_tickets.py",
    
    # Marketing data
    "generate_marketing_campaigns.py",
    "generate_marketing_qualified_leads.py",
    "generate_campaign_performance.py",
    "generate_attribution_touchpoints.py",
    "generate_google_analytics_sessions.py",
    
    # Usage/telemetry data
    "generate_tap_events.py",
    "generate_user_sessions.py",
    "generate_page_views.py",
    "generate_feature_usage.py",
    "generate_device_telemetry.py"
]

def run_generator(script_name):
    """Run a single generator script"""
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, os.path.join("scripts", script_name)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print last few lines of output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines[-5:]:
            print(f"  {line}")
            
        print(f"✅ {script_name} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with error:")
        print(e.stderr)
        return False

def main():
    """Run all generators"""
    print("🚀 Starting complete data generation")
    print(f"   Generating data for {os.getenv('DATAGEN_ENV', 'DEV')} environment")
    
    # Skip accounts since we already generated them
    generators_to_run = [g for g in generators if g != "generate_accounts.py"]
    
    failed = []
    for generator in generators_to_run:
        if not run_generator(generator):
            failed.append(generator)
    
    print("\n" + "="*60)
    print("📊 Generation Summary")
    print("="*60)
    print(f"✅ Successful: {len(generators_to_run) - len(failed)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed generators:")
        for f in failed:
            print(f"  - {f}")
    else:
        print("\n🎉 All data generated successfully!")

if __name__ == "__main__":
    main()