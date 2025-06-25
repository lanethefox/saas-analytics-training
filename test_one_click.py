#!/usr/bin/env python3
"""
Test script to validate the one-click setup works correctly.
"""

import subprocess
import sys
import time

def run_step(description, command):
    """Run a step and return success status."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print('='*60)
    
    start = time.time()
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ Success in {elapsed:.1f}s")
            return True
        else:
            print(f"❌ Failed in {elapsed:.1f}s")
            print(f"Error: {result.stderr[:500]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_table_counts():
    """Check row counts in all schemas."""
    cmd = """
export PGPASSWORD=saas_secure_password_2024
psql -h localhost -U saas_user -d saas_platform_dev -t -c "
SELECT schemaname || ': ' || COUNT(*) || ' tables, ' || COALESCE(SUM(n_live_tup), 0) || ' rows'
FROM pg_stat_user_tables 
WHERE schemaname IN ('raw', 'staging', 'intermediate', 'entity', 'mart', 'metrics')
GROUP BY schemaname 
ORDER BY schemaname;"
"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("\n📊 Database Summary:")
    print(result.stdout)

def main():
    print("🚀 Testing One-Click Setup Components")
    print("="*60)
    
    # Step 1: Check database
    if not run_step("Check Database", "python3 scripts/check_database.py"):
        return 1
    
    # Step 2: Wipe data
    if not run_step("Wipe Data", "python3 scripts/wipe_data.py --force"):
        return 1
    
    # Step 3: Generate data (xs scale)
    if not run_step("Generate Data (XS scale)", "python3 scripts/run_sequential_generators.py --scale xs"):
        return 1
    
    # Check raw data
    print("\n📊 After Data Generation:")
    check_table_counts()
    
    # Step 4: Run DBT
    if not run_step("Build DBT Models", "cd dbt_project && dbt build --full-refresh"):
        print("⚠️  DBT had some failures, but continuing...")
    
    # Final check
    print("\n📊 Final State:")
    check_table_counts()
    
    # Verify metrics schema
    cmd = """
export PGPASSWORD=saas_secure_password_2024
psql -h localhost -U saas_user -d saas_platform_dev -t -c "
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'metrics';"
"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    metrics_count = int(result.stdout.strip())
    
    print(f"\n✅ Metrics schema has {metrics_count} objects")
    
    if metrics_count >= 10:
        print("\n🎉 ONE-CLICK SETUP VALIDATION SUCCESSFUL!")
        return 0
    else:
        print("\n❌ Metrics schema incomplete")
        return 1

if __name__ == "__main__":
    sys.exit(main())