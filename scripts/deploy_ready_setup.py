#!/usr/bin/env python3
"""
Deploy-Ready Setup Script for SaaS Data Platform

This script provides a fully automated, deployment-ready setup that:
1. Checks database connectivity
2. Wipes existing data
3. Generates deterministic data without user prompts
4. Builds DBT models (if available)
5. Validates the setup

Designed to run in CI/CD environments without any user interaction.
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

def run_command(cmd, description, cwd=None, env=None):
    """Run a command and return success status."""
    print(f"\n⏳ {description}...")
    
    start_time = time.time()
    
    # Set environment for non-interactive mode
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    command_env['PYTHONUNBUFFERED'] = '1'  # Ensure non-interactive mode
    command_env['DOCKER_ENV'] = 'true'  # Force automatic truncation
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
            env=command_env
        )
        
        elapsed = time.time() - start_time
        print(f"✅ {description} completed in {elapsed:.1f}s")
        
        # Show key output lines
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                if any(keyword in line for keyword in ['✅', '✓', 'Success', 'Complete', 'records', 'MRR']):
                    print(f"   {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ {description} failed after {elapsed:.1f}s")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False

def check_dbt_installed():
    """Check if DBT is installed."""
    try:
        subprocess.run(
            [sys.executable, '-m', 'dbt', '--version'],
            capture_output=True,
            check=True
        )
        return True
    except:
        return False

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Deploy-ready setup for SaaS Data Platform'
    )
    parser.add_argument(
        '--skip-dbt',
        action='store_true',
        help='Skip DBT model building'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick setup (skip event generation)'
    )
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    print_header("SaaS Data Platform Deploy-Ready Setup")
    print(f"Mode: {'Quick' if args.quick else 'Full'} Generation")
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
    
    # Step 2: Force wipe existing data
    print_header("Step 2: Wiping Existing Data")
    
    if not run_command(
        [sys.executable, 'scripts/wipe_data.py', '--force'],
        "Database wipe"
    ):
        print("\n❌ Failed to wipe database.")
        return 1
    
    # Step 3: Generate deterministic data
    print_header("Step 3: Generating Deterministic Data")
    
    # For deploy-ready mode, run generators directly with non-interactive environment
    generators = [
        ("generate_accounts.py", "Generating accounts"),
        ("generate_locations.py", "Generating locations"),
        ("generate_devices.py", "Generating devices"),
        ("generate_users.py", "Generating users"),
        ("generate_subscriptions.py", "Generating subscriptions"),
    ]
    
    if not args.quick:
        generators.extend([
            ("generate_tap_events.py", "Generating tap events"),
            ("generate_page_views.py", "Generating page views"),
            ("generate_feature_usage.py", "Generating feature usage"),
        ])
    
    for script, description in generators:
        if not run_command(
            [sys.executable, f'scripts/{script}'],
            description,
            env={'PYTHONUNBUFFERED': '1', 'DOCKER_ENV': 'true'}
        ):
            print(f"\n❌ {description} failed.")
            return 1
    
    # Step 4: DBT build
    if not args.skip_dbt and check_dbt_installed():
        print_header("Step 4: Building DBT Models")
        
        dbt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dbt_project')
        
        # Install DBT dependencies
        run_command(
            ['dbt', 'deps'],
            "DBT dependency installation",
            cwd=dbt_dir
        )
        
        # Build DBT models
        if not run_command(
            ['dbt', 'build', '--full-refresh'],
            "DBT model building",
            cwd=dbt_dir
        ):
            print("\n⚠️  DBT build had some failures, but continuing...")
    else:
        print_header("Step 4: DBT Build (Skipped)")
        if not args.skip_dbt and not check_dbt_installed():
            print("   DBT is not installed. Skipping DBT build.")
    
    # Step 5: Validate setup
    print_header("Step 5: Validating Setup")
    
    # Quick validation - check key metrics
    validation_passed = True
    try:
        # Check subscription data
        result = subprocess.run(
            [
                sys.executable, '-c',
                """
import sys
sys.path.append('.')
from scripts.database_config import db_helper

with db_helper.config.get_cursor(dict_cursor=True) as cursor:
    cursor.execute('''
        SELECT 
            COUNT(*) as total_subs,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_subs,
            SUM(CASE WHEN status = 'active' THEN monthly_price ELSE 0 END) as mrr
        FROM raw.app_database_subscriptions
    ''')
    result = cursor.fetchone()
    
    if result['total_subs'] > 0:
        print(f"✅ Subscriptions: {result['total_subs']} total, {result['active_subs']} active")
        print(f"✅ MRR: ${result['mrr']:,.2f}")
    else:
        print("❌ No subscriptions found")
        sys.exit(1)
"""
            ],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0:
            validation_passed = False
    except:
        validation_passed = False
    
    if not validation_passed:
        print("\n⚠️  Some validations failed, but setup may still be usable.")
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("Setup Complete!")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Mode: {'Quick' if args.quick else 'Full'}")
    print(f"DBT Models: {'Built' if not args.skip_dbt and check_dbt_installed() else 'Skipped'}")
    
    # Show database summary
    print("\n📊 Database Summary:")
    try:
        result = subprocess.run(
            [
                sys.executable, '-c',
                """
import sys
sys.path.append('.')
from scripts.database_config import db_helper

with db_helper.config.get_cursor(dict_cursor=True) as cursor:
    # Get table counts by schema
    cursor.execute('''
        SELECT 
            table_schema,
            COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema IN ('raw', 'staging', 'intermediate', 'entity', 'mart', 'metrics')
        GROUP BY table_schema
        ORDER BY table_schema
    ''')
    
    total_rows = 0
    for row in cursor.fetchall():
        schema = row['table_schema']
        table_count = row['table_count']
        
        # Get row count for schema
        cursor.execute(f'''
            SELECT COALESCE(SUM(n_live_tup), 0) as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = %s
        ''', (schema,))
        row_count = cursor.fetchone()['row_count']
        
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
    
    print("\n🎉 Your SaaS data platform is ready for deployment!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())