#!/usr/bin/env python3
"""
Generate production dataset (40,000 accounts) for the SaaS platform
"""

import subprocess
import sys
import os
import time

# Core generators needed for production dataset
generators = [
    ("generate_accounts.py", "Generating 40,000 accounts"),
    ("generate_locations.py", "Generating ~85,000 locations"),
    ("generate_users.py", "Generating ~120,000 users"),
    ("generate_devices.py", "Generating ~180,000 devices"),
    ("generate_subscriptions.py", "Generating ~68,000 subscriptions"),
]

def run_generator(script_name, description):
    """Run a single generator script"""
    print(f"\n{'='*60}")
    print(f"📊 {description}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, os.path.join("scripts", script_name)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print last few lines of output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines[-10:]:
            if line.strip():
                print(f"  {line}")
        
        elapsed = time.time() - start_time
        print(f"\n✅ Completed in {elapsed:.1f} seconds")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed with error:")
        print(e.stderr)
        return False

def main():
    """Generate production dataset"""
    print("🚀 Starting PRODUCTION data generation")
    print(f"   Environment: {os.getenv('DATAGEN_ENV', 'PRODUCTION')}")
    print(f"   Target: 40,000 accounts with full related data")
    
    start_time = time.time()
    
    # Verify environment
    if os.getenv('DATAGEN_ENV') != 'PRODUCTION':
        print("\n⚠️  WARNING: DATAGEN_ENV is not set to PRODUCTION")
        print("   Please set DATAGEN_ENV=PRODUCTION in .env file")
        return
    
    # Run generators
    failed = []
    for generator, description in generators:
        if not run_generator(generator, description):
            failed.append(generator)
            print(f"\n⚠️  Stopping due to failure in {generator}")
            break
    
    # Summary
    elapsed_total = time.time() - start_time
    print("\n" + "="*60)
    print("📊 Generation Summary")
    print("="*60)
    
    if not failed:
        print(f"✅ All generators completed successfully!")
        print(f"⏱️  Total time: {elapsed_total/60:.1f} minutes")
        print(f"\n🎯 Next steps:")
        print("   1. Run additional data generators if needed (Stripe, HubSpot, etc.)")
        print("   2. Run dbt models: docker exec saas_platform_dbt_core bash -c 'cd /opt/dbt_project && dbt run'")
        print("   3. Verify data in PostgreSQL")
    else:
        print(f"❌ Generation failed at: {failed[0]}")
        print(f"   Please check the error and retry")

if __name__ == "__main__":
    main()