#!/usr/bin/env python3
"""
Pipeline Scheduler
Sets up scheduled runs of the analytics pipeline
"""

import os
import sys
import subprocess

def setup_cron():
    """Set up cron job for daily pipeline runs"""
    
    # Create cron entry
    cron_entry = "0 2 * * * cd /Users/lane/Development/Active/data-platform && /usr/bin/python3 scripts/run_analytics_pipeline.py >> logs/cron.log 2>&1"
    
    print("Setting up daily pipeline schedule...")
    print(f"Cron entry: {cron_entry}")
    
    # Write to temporary file
    with open("/tmp/analytics_cron", "w") as f:
        # Get existing crontab
        try:
            existing = subprocess.check_output(["crontab", "-l"], text=True)
            # Remove any existing analytics pipeline entries
            for line in existing.split('\n'):
                if 'run_analytics_pipeline' not in line and line.strip():
                    f.write(line + '\n')
        except subprocess.CalledProcessError:
            # No existing crontab
            pass
        
        # Add new entry
        f.write(cron_entry + '\n')
    
    # Install new crontab
    subprocess.run(["crontab", "/tmp/analytics_cron"], check=True)
    os.remove("/tmp/analytics_cron")
    
    print("✅ Cron job installed successfully!")
    print("\nSchedule:")
    print("  - Daily at 2:00 AM local time")
    print("\nTo view scheduled jobs: crontab -l")
    print("To remove schedule: crontab -r")
    print("\nTo run manually: python3 scripts/run_analytics_pipeline.py")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        print("Removing cron schedule...")
        subprocess.run(["crontab", "-r"], check=True)
        print("✅ Schedule removed")
    else:
        setup_cron()

if __name__ == "__main__":
    main()