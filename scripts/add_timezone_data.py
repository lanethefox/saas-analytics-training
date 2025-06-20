#!/usr/bin/env python3
"""
Add timezone data to locations based on their state.

This script:
- Adds timezone information to all locations
- Maps US states to their primary timezones
- Updates the locations table with timezone data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

# US State to Timezone mapping
STATE_TIMEZONES = {
    # Eastern Time
    'CT': 'America/New_York',
    'DE': 'America/New_York',
    'FL': 'America/New_York',  # Most of Florida
    'GA': 'America/New_York',
    'ME': 'America/New_York',
    'MD': 'America/New_York',
    'MA': 'America/New_York',
    'NH': 'America/New_York',
    'NJ': 'America/New_York',
    'NY': 'America/New_York',
    'NC': 'America/New_York',
    'OH': 'America/New_York',
    'PA': 'America/New_York',
    'RI': 'America/New_York',
    'SC': 'America/New_York',
    'VT': 'America/New_York',
    'VA': 'America/New_York',
    'WV': 'America/New_York',
    'DC': 'America/New_York',
    
    # Central Time
    'AL': 'America/Chicago',
    'AR': 'America/Chicago',
    'IL': 'America/Chicago',
    'IN': 'America/Chicago',  # Most of Indiana
    'IA': 'America/Chicago',
    'KS': 'America/Chicago',  # Most of Kansas
    'KY': 'America/Chicago',  # Western Kentucky
    'LA': 'America/Chicago',
    'MN': 'America/Chicago',
    'MS': 'America/Chicago',
    'MO': 'America/Chicago',
    'NE': 'America/Chicago',  # Most of Nebraska
    'ND': 'America/Chicago',  # Most of North Dakota
    'OK': 'America/Chicago',
    'SD': 'America/Chicago',  # Most of South Dakota
    'TN': 'America/Chicago',  # Most of Tennessee
    'TX': 'America/Chicago',  # Most of Texas
    'WI': 'America/Chicago',
    
    # Mountain Time
    'AZ': 'America/Phoenix',   # Arizona doesn't observe DST
    'CO': 'America/Denver',
    'ID': 'America/Denver',    # Southern Idaho
    'MT': 'America/Denver',
    'NM': 'America/Denver',
    'UT': 'America/Denver',
    'WY': 'America/Denver',
    
    # Pacific Time
    'CA': 'America/Los_Angeles',
    'NV': 'America/Los_Angeles',  # Most of Nevada
    'OR': 'America/Los_Angeles',  # Most of Oregon
    'WA': 'America/Los_Angeles',
    
    # Alaska & Hawaii
    'AK': 'America/Anchorage',
    'HI': 'Pacific/Honolulu',
}

# Default timezone for unmapped states
DEFAULT_TIMEZONE = 'America/Chicago'

def add_timezone_column():
    """Add timezone column if it doesn't exist."""
    with db_helper.config.get_cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_locations'
            AND column_name = 'timezone'
        """)
        
        if cursor.rowcount == 0:
            print("Adding timezone column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_locations 
                ADD COLUMN timezone VARCHAR(50)
            """)
            cursor.connection.commit()
            return True
        return False

def update_location_timezones():
    """Update all locations with timezone data."""
    with db_helper.config.get_cursor() as cursor:
        # Get all locations
        cursor.execute("""
            SELECT id, state, city
            FROM raw.app_database_locations
            ORDER BY id
        """)
        locations = cursor.fetchall()
        
        print(f"Updating timezones for {len(locations)} locations...")
        
        # Update each location
        updates = []
        timezone_counts = {}
        
        for location_id, state, city in locations:
            timezone = STATE_TIMEZONES.get(state, DEFAULT_TIMEZONE)
            updates.append((timezone, location_id))
            
            # Track distribution
            timezone_counts[timezone] = timezone_counts.get(timezone, 0) + 1
        
        # Batch update
        cursor.executemany("""
            UPDATE raw.app_database_locations
            SET timezone = %s
            WHERE id = %s
        """, updates)
        
        cursor.connection.commit()
        
        return timezone_counts

def save_timezone_summary():
    """Save summary of timezone distribution."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT timezone, COUNT(*) as count,
                   STRING_AGG(DISTINCT state, ', ' ORDER BY state) as states
            FROM raw.app_database_locations
            GROUP BY timezone
            ORDER BY count DESC
        """)
        
        timezone_data = []
        total_locations = 0
        
        for row in cursor.fetchall():
            count = row[1]
            total_locations += count
            timezone_data.append({
                'timezone': row[0],
                'location_count': count,
                'states': row[2]
            })
        
        # Calculate UTC offsets
        utc_offsets = {
            'America/New_York': 'UTC-5 (UTC-4 during DST)',
            'America/Chicago': 'UTC-6 (UTC-5 during DST)',
            'America/Denver': 'UTC-7 (UTC-6 during DST)',
            'America/Los_Angeles': 'UTC-8 (UTC-7 during DST)',
            'America/Phoenix': 'UTC-7 (no DST)',
            'America/Anchorage': 'UTC-9 (UTC-8 during DST)',
            'Pacific/Honolulu': 'UTC-10 (no DST)'
        }
        
        # Add UTC offset info
        for tz_info in timezone_data:
            tz_info['utc_offset'] = utc_offsets.get(tz_info['timezone'], 'Unknown')
            tz_info['percentage'] = round((tz_info['location_count'] / total_locations) * 100, 1)
        
        summary = {
            'total_locations': total_locations,
            'unique_timezones': len(timezone_data),
            'timezone_distribution': timezone_data
        }
        
        with open('data/location_timezones_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✓ Saved timezone summary to data/location_timezones_summary.json")

def main():
    print("=== Adding Timezone Data ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Add timezone column if needed
    column_added = add_timezone_column()
    if column_added:
        print("✓ Added timezone column to locations table")
    
    # Update timezones
    print("\nUpdating location timezones...")
    timezone_counts = update_location_timezones()
    
    print("\nTimezone distribution:")
    for timezone, count in sorted(timezone_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {timezone}: {count} locations")
    
    # Save summary
    save_timezone_summary()
    
    # Show sample
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT city, state, timezone
            FROM raw.app_database_locations
            WHERE timezone IS NOT NULL
            LIMIT 5
        """)
        
        print("\nSample locations with timezones:")
        for city, state, timezone in cursor.fetchall():
            print(f"  - {city}, {state}: {timezone}")
    
    # Verify all updated
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(timezone) as with_timezone
            FROM raw.app_database_locations
        """)
        total, with_tz = cursor.fetchone()
        
        if total == with_tz:
            print(f"\n✓ Successfully updated all {total} locations with timezone data")
        else:
            print(f"\n⚠ Updated {with_tz} out of {total} locations with timezone data")
    
    print("\n✓ Task 33 complete!")

if __name__ == "__main__":
    main()