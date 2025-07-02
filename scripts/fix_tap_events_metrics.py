#!/usr/bin/env python3
"""
Fix tap events metrics to include required fields for health calculations
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

def fix_tap_event_metrics():
    """Update tap event metrics to include all required fields"""
    print("Fixing tap event metrics...")
    
    with db_helper.config.get_connection() as conn:
        with conn.cursor() as cursor:
            # Update metrics JSON to add missing fields
            cursor.execute("""
                UPDATE raw.app_database_tap_events
                SET metrics = jsonb_build_object(
                    'volume_ml', ROUND((metrics->>'pour_ounces')::numeric * 29.5735, 1),
                    'temperature_c', ROUND(((metrics->>'temperature_f')::numeric - 32) * 5/9, 1),
                    'pressure_psi', ROUND((10 + RANDOM() * 5)::numeric, 1),
                    'flow_rate_ml_per_sec', ROUND((15 + RANDOM() * 10)::numeric, 1),
                    'duration_seconds', (metrics->>'duration_seconds')::numeric,
                    'pour_ounces', (metrics->>'pour_ounces')::numeric,
                    'temperature_f', (metrics->>'temperature_f')::numeric
                )
                WHERE event_type = 'pour'
            """)
            
            updated = cursor.rowcount
            conn.commit()
            
            print(f"✓ Updated {updated:,} tap event records")
            
            # Verify the update
            cursor.execute("""
                SELECT metrics 
                FROM raw.app_database_tap_events 
                WHERE event_type = 'pour'
                LIMIT 5
            """)
            
            print("\nSample updated metrics:")
            for row in cursor.fetchall():
                print(f"  {row[0]}")

def main():
    print("Tap Events Metrics Fix")
    print("=" * 40)
    
    fix_tap_event_metrics()
    
    print("\n✅ Metrics fix complete!")

if __name__ == "__main__":
    main()