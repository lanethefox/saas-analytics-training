#!/usr/bin/env python3
"""
Validate data quality after deployment
"""

import psycopg2
from database_config import DatabaseConfig

def validate_data_quality():
    """Check key data quality metrics"""
    db_config = DatabaseConfig()
    
    with db_config.get_connection() as conn:
        with conn.cursor() as cur:
            # Check customer variety
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT industry) as industries,
                    COUNT(DISTINCT customer_tier) as tiers,
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN customer_health_score = 0 THEN 1 END) as zero_health,
                    COUNT(DISTINCT customer_health_score) as unique_health_scores
                FROM entity.entity_customers
            """)
            customer_stats = cur.fetchone()
            
            # Check device variety
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT overall_health_score) as unique_health_scores,
                    COUNT(*) as total_devices,
                    COUNT(CASE WHEN overall_health_score = 0.2 THEN 1 END) as default_health
                FROM entity.entity_devices
            """)
            device_stats = cur.fetchone()
            
            # Check campaign data
            cur.execute("""
                SELECT COUNT(*) FROM entity.entity_campaigns
            """)
            campaign_count = cur.fetchone()[0]
            
            # Check subscription trials
            cur.execute("""
                SELECT 
                    COUNT(*) as total_subs,
                    COUNT(trial_start_date) as with_trials,
                    COUNT(DISTINCT plan_type) as plan_types
                FROM entity.entity_subscriptions
            """)
            sub_stats = cur.fetchone()
            
            # Check event data
            cur.execute("""
                SELECT 
                    COUNT(*) as tap_events,
                    COUNT(DISTINCT device_id) as devices_with_events
                FROM raw.app_database_tap_events
            """)
            event_stats = cur.fetchone()
            
            print("\n📊 DATA QUALITY VALIDATION REPORT")
            print("=" * 50)
            
            print(f"\n✓ Customer Data:")
            print(f"  - Industries: {customer_stats[0]} (Target: 5+)")
            print(f"  - Tiers: {customer_stats[1]} (Target: 4)")
            print(f"  - Total: {customer_stats[2]:,}")
            print(f"  - Health Score Variety: {customer_stats[4]} unique values")
            
            print(f"\n✓ Device Data:")
            print(f"  - Total: {device_stats[1]:,}")
            print(f"  - Health Score Variety: {device_stats[0]} unique values")
            print(f"  - Default Health (0.2): {device_stats[2]:,} ({device_stats[2]/device_stats[1]*100:.1f}%)")
            
            print(f"\n✓ Campaign Data:")
            print(f"  - Total Campaigns: {campaign_count}")
            
            print(f"\n✓ Subscription Data:")
            print(f"  - Total: {sub_stats[0]:,}")
            print(f"  - With Trials: {sub_stats[1]:,} ({sub_stats[1]/sub_stats[0]*100:.1f}%)")
            print(f"  - Plan Types: {sub_stats[2]}")
            
            print(f"\n✓ Event Data:")
            print(f"  - Tap Events: {event_stats[0]:,}")
            print(f"  - Devices with Events: {event_stats[1]:,}")
            
            # Summary
            print("\n" + "=" * 50)
            issues = []
            
            if customer_stats[1] < 4:
                issues.append("❌ Customer tiers not varied (all tier 4)")
            if device_stats[0] == 1:
                issues.append("❌ Device health scores not varied")
            if campaign_count == 0:
                issues.append("❌ No campaign data generated")
            if event_stats[0] == 0:
                issues.append("❌ No tap events generated")
                
            if issues:
                print("ISSUES FOUND:")
                for issue in issues:
                    print(f"  {issue}")
            else:
                print("✅ ALL DATA QUALITY CHECKS PASSED!")

if __name__ == "__main__":
    validate_data_quality()