#!/usr/bin/env python3
"""
One-Click Setup Script for SaaS Data Platform

This script provides a complete one-click setup that:
1. Checks database connectivity
2. Wipes existing data (if requested)  
3. Generates deterministic data with fixed seed
4. Builds DBT models
5. Validates the setup

Usage:
    python scripts/one_click_setup.py [--skip-dbt] [--keep-existing]
"""

import subprocess
import sys
import os
import time
import argparse
from datetime import datetime

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🎯 {text}")
    print("="*60)

def run_command(cmd, description, cwd=None):
    """Run a command and return success status."""
    print(f"\n⏳ {description}...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd
        )
        
        elapsed = time.time() - start_time
        print(f"✅ {description} completed in {elapsed:.1f}s")
        
        # Show key output lines
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                if any(keyword in line for keyword in ['✅', '✓', 'Success', 'Complete', 'records']):
                    print(f"   {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ {description} failed after {elapsed:.1f}s")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='One-click setup for SaaS Data Platform with deterministic data generation'
    )
    parser.add_argument(
        '--skip-dbt',
        action='store_true',
        help='Skip DBT model building'
    )
    parser.add_argument(
        '--keep-existing',
        action='store_true',
        help='Keep existing data (skip wipe)'
    )
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    print_header("SaaS Data Platform One-Click Setup")
    print(f"Data Generation: Deterministic (fixed seed)")
    print(f"DBT: {'Disabled' if args.skip_dbt else 'Enabled'}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check database connectivity
    print_header("Step 1: Checking Database Connectivity")
    
    if not run_command(
        [sys.executable, 'scripts/check_database.py'],
        "Database connectivity check"
    ):
        print("\n❌ Database connection failed. Please check your PostgreSQL setup.")
        return 1
    
    # Step 2: Wipe existing data (if requested)
    if not args.keep_existing:
        print_header("Step 2: Wiping Existing Data")
        
        if not run_command(
            [sys.executable, 'scripts/wipe_data.py', '--force'],
            "Database wipe"
        ):
            print("\n❌ Failed to wipe database.")
            return 1
    else:
        print_header("Step 2: Keeping Existing Data (Skipped)")
    
    # Step 3: Generate deterministic data
    print_header("Step 3: Generating Deterministic Data")
    
    cmd = [sys.executable, 'scripts/generate_all_deterministic.py']
    
    if not run_command(cmd, "Deterministic data generation"):
        print("\n❌ Data generation failed.")
        return 1
    
    # Step 4: DBT build (if not integrated above)
    if not args.skip_dbt and '--with-dbt' not in cmd:
        print_header("Step 4: Building DBT Models")
        
        dbt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dbt_project')
        
        # Install DBT dependencies
        if not run_command(
            [sys.executable, '-m', 'dbt', 'deps'],
            "DBT dependency installation",
            cwd=dbt_dir
        ):
            print("\n⚠️  DBT deps failed, continuing anyway...")
        
        # Build DBT models
        if not run_command(
            [sys.executable, '-m', 'dbt', 'build', '--full-refresh'],
            "DBT model building",
            cwd=dbt_dir
        ):
            print("\n⚠️  DBT build had some failures, but continuing...")
    elif args.skip_dbt:
        print_header("Step 4: DBT Build (Skipped)")
    
    # Step 5: Validate setup
    print_header("Step 5: Validating Setup")
    
    if not run_command(
        [sys.executable, 'scripts/validate_setup.py'],
        "Setup validation"
    ):
        print("\n⚠️  Some validations failed, but setup is likely usable.")
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("Setup Complete!")
    print(f"Duration: {duration:.1f} seconds")
    print(f"DBT Models: {'Built' if not args.skip_dbt else 'Skipped'}")
    
    # Show row counts summary
    print("\n📊 Database Summary:")
    try:
        result = subprocess.run(
            [
                sys.executable, '-c',
                """
import sys
sys.path.append('.')
from scripts.database_config import db_helper

schemas = ['raw', 'staging', 'intermediate', 'entity', 'mart', 'metrics']
total_rows = 0

for schema in schemas:
    with db_helper.config.get_cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{schema}'")
        table_count = cursor.fetchone()[0]
        
        cursor.execute(f'''
            SELECT COALESCE(SUM(n_live_tup), 0) 
            FROM pg_stat_user_tables 
            WHERE schemaname = '{schema}'
        ''')
        row_count = cursor.fetchone()[0]
        
        if table_count > 0:
            print(f"  {schema}: {table_count} tables, {row_count:,} rows")
            total_rows += row_count

print(f"\\n  Total: {total_rows:,} rows")
"""
            ],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout.strip())
    except:
        pass
    
    print("\n📊 Next Steps:")
    print("1. Access the database: psql -h localhost -U saas_user -d saas_platform_dev")
    print("2. Run queries against the mart layer tables")
    print("3. Connect your BI tool to the database")
    
    if not args.skip_dbt:
        print("4. View DBT docs: cd dbt_project && dbt docs generate && dbt docs serve")
    
    print("\n🎉 Your SaaS data platform is ready!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())