#!/usr/bin/env python3
"""
Complete Superset Setup Runner
Executes all parts to create datasets and dashboards
"""

import subprocess
import sys
import time

def run_script(script_name):
    """Run a Python script and return success status"""
    print(f"\n🚀 Running {script_name}...")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Main execution"""
    print("🎯 Complete Superset Setup")
    print("=" * 60)
    print("This will create:")
    print("  • All entity and mart layer datasets")
    print("  • Interactive charts and visualizations")
    print("  • 5 domain-specific dashboards with documentation")
    print("=" * 60)
    
    # Run Part 1: Create Datasets
    if not run_script("setup_superset_part1.py"):
        print("\n❌ Failed to create datasets. Exiting.")
        sys.exit(1)
    
    print("\n✅ Datasets created successfully!")
    time.sleep(2)
    
    # Run Part 3: Create Dashboards (includes charts)
    if not run_script("setup_superset_part3_dashboards.py"):
        print("\n❌ Failed to create dashboards. Check logs above.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📊 What was created:")
    print("  • ~30 datasets from entity and mart layers")
    print("  • ~25 interactive charts across domains")
    print("  • 5 comprehensive dashboards:")
    print("    - Customer Success Command Center")
    print("    - Sales Pipeline & Performance")
    print("    - Marketing Attribution & Performance")
    print("    - Product Adoption & Usage Analytics")
    print("    - Operations Command Center")
    print("\n🔗 Access your dashboards at:")
    print(f"  http://localhost:8088")
    print("\n📝 Login credentials:")
    print("  Username: admin")
    print("  Password: admin_password_2024")
    print("\n🎯 Recommended next steps:")
    print("  1. Explore each dashboard")
    print("  2. Try the interactive filters")
    print("  3. Set up email reports for key metrics")
    print("  4. Create alerts for critical thresholds")
    print("  5. Customize charts for your specific needs")

if __name__ == "__main__":
    main()