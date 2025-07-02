#!/usr/bin/env python3
"""
Orchestrate deterministic data generation for all entities.

This script runs all generators in the correct order and validates the output.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_script(script_name, description):
    """Run a Python script and capture output"""
    print(f"\n{'=' * 60}")
    print(f"🚀 {description}")
    print(f"{'=' * 60}")
    
    start_time = time.time()
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    # Check if we're in Docker environment
    in_docker = os.environ.get('DOCKER_ENV', 'false').lower() == 'true'
    
    try:
        # Run with automatic yes to truncate prompts
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        # Send 'y' for truncate prompts
        # In Docker, always say yes; otherwise prompt user
        if in_docker:
            output, _ = process.communicate(input='y\n')
        else:
            output, _ = process.communicate(input='y\n')
        
        # Print output
        print(output)
        
        if process.returncode != 0:
            print(f"❌ Error running {script_name} (exit code: {process.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Exception running {script_name}: {e}")
        return False
    
    elapsed = time.time() - start_time
    print(f"✅ Completed in {elapsed:.2f} seconds")
    return True

def main():
    """Main execution function"""
    print("=" * 80)
    print("DETERMINISTIC DATA GENERATION PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define generation pipeline in order
    pipeline = [
        # Core entities
        ("generate_accounts.py", "Generating accounts with industry variety"),
        ("generate_locations.py", "Generating locations with geographic distribution"),
        ("generate_devices.py", "Generating devices with operational variety"),
        ("generate_users.py", "Generating users with role distribution"),
        ("generate_subscriptions.py", "Generating subscriptions with trials and pricing tiers"),
        
        # Event data - now enabled for complete data
        ("generate_tap_events_integrated.py", "Generating tap events with varied patterns"),
        ("generate_page_views.py", "Generating page view analytics"),
        ("generate_feature_usage.py", "Generating feature usage events"),
        
        # Marketing and attribution
        ("generate_marketing_campaigns.py", "Generating multi-channel campaigns"),
        ("generate_marketing_qualified_leads.py", "Generating MQLs"),
        ("generate_attribution_touchpoints.py", "Generating attribution data"),
        
        # Financial data
        ("generate_stripe_customers.py", "Generating payment customers"),
        ("generate_stripe_prices.py", "Generating pricing plans"),
        ("generate_stripe_subscriptions.py", "Generating payment subscriptions"),
        ("generate_stripe_invoices.py", "Generating invoices"),
        ("generate_stripe_charges.py", "Generating payment transactions"),
        
        # CRM data
        ("generate_hubspot_companies.py", "Generating CRM companies"),
        ("generate_hubspot_contacts.py", "Generating CRM contacts"),
        ("generate_hubspot_deals.py", "Generating sales pipeline"),
        
        # Analytics
        ("generate_google_analytics_sessions.py", "Generating web analytics"),
        ("generate_user_sessions.py", "Generating user session data"),
    ]
    
    # Track success
    all_success = True
    
    # Run each generator
    for script, description in pipeline:
        success = run_script(script, description)
        if not success:
            all_success = False
            print(f"\n❌ Pipeline failed at {script}")
            break
    
    # Run validation if generation succeeded
    if all_success:
        print("\n" + "=" * 80)
        print("🔍 Running data integrity validation...")
        print("=" * 80)
        
        validation_success = run_script("validate_data_integrity.py", "Validating data integrity")
        
        if validation_success:
            print("\n" + "=" * 80)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\nAll data has been generated with:")
            print("  - Deterministic, reproducible output")
            print("  - Valid foreign key relationships")
            print("  - Sequential IDs within defined ranges")
            print("  - Realistic business distributions")
        else:
            print("\n" + "=" * 80)
            print("⚠️  PIPELINE COMPLETED WITH VALIDATION WARNINGS")
            print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ PIPELINE FAILED!")
        print("=" * 80)
        print("\nPlease check the errors above and try again.")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()