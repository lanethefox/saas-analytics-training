#!/usr/bin/env python3
"""
Generate all data for the SaaS platform in the correct order
Supports multiple scale options: xs, small, medium, large
Now with resume capability and parallel processing
"""

import subprocess
import sys
import os
import argparse
import time
import json
import psycopg2
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'saas_platform_dev'),
    'user': os.getenv('POSTGRES_USER', 'saas_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'saas_secure_password_2024')
}

# Map generators to their target tables for resume functionality
GENERATOR_TABLE_MAP = {
    "generate_accounts.py": "raw.app_database_accounts",
    "generate_locations.py": "raw.app_database_locations",
    "generate_users.py": "raw.app_database_users",
    "generate_devices.py": "raw.app_database_devices",
    "generate_subscriptions.py": "raw.app_database_subscriptions",
    "generate_stripe_customers.py": "raw.stripe_customers",
    "generate_stripe_prices.py": "raw.stripe_prices",
    "generate_stripe_subscriptions.py": "raw.stripe_subscriptions",
    "generate_stripe_subscription_items.py": "raw.stripe_subscription_items",
    "generate_stripe_invoices.py": "raw.stripe_invoices",
    "generate_stripe_charges.py": "raw.stripe_charges",
    "generate_stripe_events.py": "raw.stripe_events",
    "generate_hubspot_companies.py": "raw.hubspot_companies",
    "generate_hubspot_contacts.py": "raw.hubspot_contacts",
    "generate_hubspot_deals.py": "raw.hubspot_deals",
    "generate_hubspot_engagements.py": "raw.hubspot_engagements",
    "generate_hubspot_tickets.py": "raw.hubspot_tickets",
    "generate_marketing_campaigns.py": "raw.marketing_campaigns",
    "generate_marketing_qualified_leads.py": "raw.marketing_qualified_leads",
    "generate_campaign_performance.py": "raw.campaign_performance",
    "generate_attribution_touchpoints.py": "raw.attribution_touchpoints",
    "generate_google_analytics_sessions.py": "raw.google_analytics_sessions",
    "generate_tap_events.py": "raw.app_database_tap_events",
    "generate_user_sessions.py": "raw.app_database_user_sessions",
    "generate_page_views.py": "raw.app_database_page_views",
    "generate_feature_usage.py": "raw.app_database_feature_usage",
    "generate_device_telemetry.py": "raw.device_telemetry",
    "generate_stripe_payment_intents.py": "raw.stripe_payment_intents",
    "generate_hubspot_owners.py": "raw.hubspot_owners",
    "generate_facebook_ads_campaigns.py": "raw.facebook_ads_campaigns",
    "generate_google_ads_campaigns.py": "raw.google_ads_campaigns",
    "generate_linkedin_ads_campaigns.py": "raw.linkedin_ads_campaigns",
    "generate_iterable_campaigns.py": "raw.iterable_campaigns"
}

# Define generator groups for parallel execution
# Each group contains generators that can run in parallel (no dependencies between them)
GENERATOR_GROUPS = [
    # Group 1: Core entities (must run first)
    ["generate_accounts.py"],
    
    # Group 2: Dependent on accounts
    ["generate_locations.py", "generate_users.py", "generate_subscriptions.py", 
     "generate_stripe_customers.py", "generate_stripe_prices.py"],
    
    # Group 3: Dependent on locations/users
    ["generate_devices.py", "generate_stripe_subscriptions.py"],
    
    # Group 4: Stripe billing (dependent on subscriptions)
    ["generate_stripe_subscription_items.py", "generate_stripe_invoices.py"],
    
    # Group 5: Stripe charges and events
    ["generate_stripe_charges.py", "generate_stripe_events.py", "generate_stripe_payment_intents.py"],
    
    # Group 6: HubSpot data (can run in parallel)
    ["generate_hubspot_owners.py", "generate_hubspot_companies.py", "generate_hubspot_contacts.py", 
     "generate_hubspot_deals.py", "generate_hubspot_engagements.py", 
     "generate_hubspot_tickets.py"],
    
    # Group 7: Marketing data (can run in parallel)
    ["generate_marketing_campaigns.py", "generate_marketing_qualified_leads.py",
     "generate_campaign_performance.py", "generate_attribution_touchpoints.py",
     "generate_google_analytics_sessions.py", "generate_facebook_ads_campaigns.py",
     "generate_google_ads_campaigns.py", "generate_linkedin_ads_campaigns.py",
     "generate_iterable_campaigns.py"],
    
    # Group 8: Usage/telemetry data (heavy, run last)
    ["generate_tap_events.py", "generate_user_sessions.py", 
     "generate_page_views.py", "generate_feature_usage.py", 
     "generate_device_telemetry.py"]
]

def check_table_has_data(table_name):
    """Check if a table already has data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Handle schema.table format
        if '.' in table_name:
            schema, table = table_name.split('.')
            query = f"SELECT COUNT(*) FROM {schema}.{table} LIMIT 1"
        else:
            query = f"SELECT COUNT(*) FROM {table_name} LIMIT 1"
            
        cursor.execute(query)
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count > 0
    except Exception as e:
        # Table might not exist yet
        return False

def run_generator(script_name, progress_info=None):
    """Run a single generator script"""
    if progress_info:
        current, total = progress_info
        print(f"\n[{current}/{total}] {'='*50}")
    else:
        print(f"\n{'='*60}")
    print(f"🔄 Running {script_name}...")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, os.path.join("scripts", script_name)],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        # Print last few lines of output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines[-5:]:
            print(f"  {line}")
        
        elapsed = time.time() - start_time
        print(f"✅ {script_name} completed in {elapsed:.1f}s")
        return (script_name, True, elapsed)
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ {script_name} failed after {elapsed:.1f}s")
        print(f"Error: {e.stderr}")
        return (script_name, False, elapsed)

def save_progress(completed_generators, progress_file='.datagen_progress.json'):
    """Save progress to a file"""
    progress_data = {
        'timestamp': datetime.now().isoformat(),
        'completed': completed_generators
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f, indent=2)

def load_progress(progress_file='.datagen_progress.json'):
    """Load progress from file"""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return set(data.get('completed', []))
        except:
            return set()
    return set()

def main():
    """Run all generators with resume and parallel capabilities"""
    parser = argparse.ArgumentParser(
        description='Generate all synthetic data for the B2B SaaS platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scale options:
  xs      Extra small dataset (~100 accounts) - for quick testing
  small   Small dataset (~10K accounts) - for development
  medium  Medium dataset (~40K accounts) - for integration testing  
  large   Large dataset (~100K accounts) - for performance testing

Features:
  --resume         Resume from where the last run stopped
  --parallel       Run independent generators in parallel (default)
  --sequential     Run generators one at a time
  --skip-existing  Skip generators for tables that already have data

Examples:
  python scripts/generate_all_data.py --scale small
  python scripts/generate_all_data.py --scale large --resume
  python scripts/generate_all_data.py --scale medium --skip-existing
        """
    )
    
    parser.add_argument(
        '--scale',
        choices=['xs', 'small', 'medium', 'large'],
        default='small',
        help='Dataset scale (default: small)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last successful generator'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Run independent generators in parallel (default)'
    )
    
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Run generators sequentially'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip generators for tables that already have data'
    )
    
    args = parser.parse_args()
    
    # Handle parallel/sequential conflict
    if args.sequential:
        args.parallel = False
    
    # Set environment variable based on scale
    os.environ['DATAGEN_ENV'] = args.scale
    
    start_time = time.time()
    
    print("🚀 Starting data generation")
    print(f"   Dataset scale: {args.scale}")
    print(f"   Target database: {DB_CONFIG['host']}")
    print(f"   Execution mode: {'Parallel' if args.parallel else 'Sequential'}")
    if args.resume:
        print("   Resume mode: Enabled")
    if args.skip_existing:
        print("   Skip existing: Enabled")
    
    # Load progress if resuming
    completed = load_progress() if args.resume else set()
    
    # Flatten generator groups for sequential mode
    all_generators = []
    for group in GENERATOR_GROUPS:
        all_generators.extend(group)
    
    # Determine which generators to run
    generators_to_run = []
    skipped_existing = []
    skipped_completed = []
    
    for generator in all_generators:
        if generator in completed:
            skipped_completed.append(generator)
            continue
            
        if args.skip_existing:
            table_name = GENERATOR_TABLE_MAP.get(generator)
            if table_name and check_table_has_data(table_name):
                skipped_existing.append(generator)
                completed.add(generator)
                save_progress(list(completed))
                continue
        
        generators_to_run.append(generator)
    
    # Print skip summary
    if skipped_completed:
        print(f"\n📝 Skipping {len(skipped_completed)} previously completed generators")
    if skipped_existing:
        print(f"📊 Skipping {len(skipped_existing)} generators (tables already have data)")
    
    print(f"\n🎯 Running {len(generators_to_run)} generators")
    
    failed = []
    success_count = 0
    
    if args.parallel and generators_to_run:
        # Parallel execution by groups
        print("\n🚦 Running generators in parallel groups...")
        
        for group_idx, group in enumerate(GENERATOR_GROUPS):
            # Filter group to only include generators we need to run
            group_to_run = [g for g in group if g in generators_to_run]
            
            if not group_to_run:
                continue
            
            print(f"\n📦 Group {group_idx + 1}: {len(group_to_run)} generators")
            
            with ProcessPoolExecutor(max_workers=min(len(group_to_run), 4)) as executor:
                futures = {
                    executor.submit(run_generator, gen, (i+1, len(group_to_run))): gen 
                    for i, gen in enumerate(group_to_run)
                }
                
                for future in as_completed(futures):
                    generator_name = futures[future]
                    try:
                        name, success, elapsed = future.result()
                        if success:
                            success_count += 1
                            completed.add(name)
                            save_progress(list(completed))
                        else:
                            failed.append(name)
                    except Exception as e:
                        print(f"❌ {generator_name} failed with exception: {e}")
                        failed.append(generator_name)
    
    else:
        # Sequential execution
        for idx, generator in enumerate(generators_to_run):
            result = run_generator(generator, (idx + 1, len(generators_to_run)))
            name, success, elapsed = result
            
            if success:
                success_count += 1
                completed.add(name)
                save_progress(list(completed))
            else:
                failed.append(name)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Generation Summary")
    print("="*60)
    print(f"✅ Successful: {success_count}")
    print(f"⏩ Skipped (existing): {len(skipped_existing)}")
    print(f"📝 Skipped (completed): {len(skipped_completed)}")
    print(f"❌ Failed: {len(failed)}")
    
    elapsed = time.time() - start_time
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
    
    if failed:
        print("\nFailed generators:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n🎉 All data generated successfully!")
        # Clean up progress file on successful completion
        if os.path.exists('.datagen_progress.json'):
            os.remove('.datagen_progress.json')

if __name__ == "__main__":
    main()