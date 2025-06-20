#!/usr/bin/env python3
"""
Generate synthetic campaign performance data for the bar management SaaS platform.

This script:
- Updates existing campaigns with realistic daily performance metrics
- Creates time-based progression of impressions, clicks, spend
- Implements seasonal variations and budget pacing
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from decimal import Decimal
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_campaigns_mapping():
    """Load existing campaigns mapping."""
    with open('data/marketing_campaigns_mapping.json', 'r') as f:
        return json.load(f)

def calculate_daily_performance(campaign, platform, day_of_week, season_factor):
    """Calculate realistic daily performance based on platform and timing."""
    
    # Base performance rates by platform
    platform_rates = {
        'google_ads': {
            'ctr': 0.02,  # 2% CTR
            'cpc': 2.50,   # $2.50 CPC
            'conversion_rate': 0.03  # 3% conversion
        },
        'facebook_ads': {
            'ctr': 0.01,  # 1% CTR
            'cpm': 25.00,  # $25 CPM
            'conversion_rate': 0.02  # 2% conversion
        },
        'linkedin_ads': {
            'ctr': 0.005,  # 0.5% CTR
            'cpc': 8.00,   # $8.00 CPC
            'conversion_rate': 0.05  # 5% conversion (higher quality leads)
        }
    }
    
    # Day of week factors (higher on weekdays for B2B)
    dow_factors = {
        0: 1.2,  # Monday
        1: 1.1,  # Tuesday
        2: 1.15, # Wednesday
        3: 1.1,  # Thursday
        4: 0.9,  # Friday
        5: 0.6,  # Saturday
        6: 0.5   # Sunday
    }
    
    dow_factor = dow_factors.get(day_of_week, 1.0)
    
    # Random daily variance
    daily_variance = random.uniform(0.8, 1.2)
    
    # Combined factor
    performance_factor = dow_factor * season_factor * daily_variance
    
    return platform_rates.get(platform, platform_rates['google_ads']), performance_factor

def update_google_ads_performance():
    """Update Google Ads campaigns with performance data."""
    print("\nUpdating Google Ads campaign performance...")
    
    with db_helper.config.get_cursor() as cursor:
        # Get all campaigns
        cursor.execute("SELECT * FROM raw.google_ads_campaigns")
        campaigns = cursor.fetchall()
        
        updates = []
        for campaign in campaigns:
            # Skip if campaign hasn't started yet
            start_date = campaign[5]  # start_date column
            end_date = campaign[6]    # end_date column
            if start_date > datetime.now().date():
                continue
            
            # Calculate days running
            current_date = min(datetime.now().date(), end_date)
            days_running = (current_date - start_date).days + 1
            
            # Get campaign budget
            budget_amount = float(campaign[7]) if campaign[7] else 0
            daily_budget = budget_amount / ((end_date - start_date).days + 1)
            
            # Simulate daily performance
            total_impressions = 0
            total_clicks = 0
            total_cost = 0
            total_conversions = 0
            
            rates, _ = calculate_daily_performance(campaign, 'google_ads', 0, 1.0)
            
            for day in range(days_running):
                current_day = start_date + timedelta(days=day)
                dow = current_day.weekday()
                
                # Seasonal factor (Q4 is higher for retail)
                month = current_day.month
                season_factor = 1.2 if month in [10, 11, 12] else 1.0
                
                _, perf_factor = calculate_daily_performance(campaign, 'google_ads', dow, season_factor)
                
                # Daily impressions based on budget and competition
                daily_impressions = int(random.randint(1000, 10000) * perf_factor)
                daily_clicks = int(daily_impressions * rates['ctr'] * perf_factor)
                daily_cost = min(daily_clicks * rates['cpc'], daily_budget * 0.9)  # Don't exceed budget
                daily_conversions = int(daily_clicks * rates['conversion_rate'])
                
                total_impressions += daily_impressions
                total_clicks += daily_clicks
                total_cost += daily_cost
                total_conversions += daily_conversions
            
            # Update campaign
            updates.append({
                'id': campaign[0],
                'impressions': total_impressions,
                'clicks': total_clicks,
                'cost': round(total_cost, 2),
                'conversions': total_conversions
            })
        
        # Batch update
        for update in updates:
            cursor.execute("""
                UPDATE raw.google_ads_campaigns 
                SET impressions = %s, clicks = %s, cost = %s, conversions = %s
                WHERE id = %s
            """, (update['impressions'], update['clicks'], update['cost'], 
                  update['conversions'], update['id']))
        
        print(f"✓ Updated {len(updates)} Google Ads campaigns with performance data")

def update_facebook_ads_performance():
    """Update Facebook Ads campaigns with performance data."""
    print("\nUpdating Facebook Ads campaign performance...")
    
    with db_helper.config.get_cursor() as cursor:
        # Get all campaigns
        cursor.execute("SELECT * FROM raw.facebook_ads_campaigns")
        campaigns = cursor.fetchall()
        
        updates = []
        for campaign in campaigns:
            start_time = campaign[5]  # start_time column
            stop_time = campaign[6]   # stop_time column
            
            if not start_time or start_time > datetime.now():
                continue
            
            # Calculate days running
            end_time = stop_time if stop_time else datetime.now()
            days_running = (end_time - start_time).days + 1
            
            # Get budget
            daily_budget = float(campaign[7]) if campaign[7] else 100
            
            # Simulate performance
            total_impressions = 0
            total_clicks = 0
            total_spend = 0
            
            rates, _ = calculate_daily_performance(campaign, 'facebook_ads', 0, 1.0)
            
            for day in range(days_running):
                current_day = start_time + timedelta(days=day)
                dow = current_day.weekday()
                season_factor = 1.1 if current_day.month in [11, 12] else 1.0
                
                _, perf_factor = calculate_daily_performance(campaign, 'facebook_ads', dow, season_factor)
                
                # Facebook uses CPM model
                daily_spend = daily_budget * random.uniform(0.8, 1.0) * perf_factor
                daily_impressions = int((daily_spend / rates['cpm']) * 1000)
                daily_clicks = int(daily_impressions * rates['ctr'] * perf_factor)
                
                total_impressions += daily_impressions
                total_clicks += daily_clicks
                total_spend += daily_spend
            
            # Generate actions based on objective
            actions = []
            objective = campaign[3]  # objective column
            if objective == 'CONVERSIONS':
                actions.append({
                    'action_type': 'purchase',
                    'value': int(total_clicks * rates['conversion_rate'])
                })
            elif objective == 'LEAD_GENERATION':
                actions.append({
                    'action_type': 'leadgen.other',
                    'value': int(total_clicks * rates['conversion_rate'] * 2)
                })
            elif objective == 'TRAFFIC':
                actions.append({
                    'action_type': 'link_click',
                    'value': total_clicks
                })
            
            updates.append({
                'id': campaign[0],
                'impressions': total_impressions,
                'clicks': total_clicks,
                'spend': round(total_spend, 2),
                'actions': json.dumps(actions) if actions else None
            })
        
        # Batch update
        for update in updates:
            cursor.execute("""
                UPDATE raw.facebook_ads_campaigns 
                SET impressions = %s, clicks = %s, spend = %s, actions = %s
                WHERE id = %s
            """, (update['impressions'], update['clicks'], update['spend'], 
                  update['actions'], update['id']))
        
        print(f"✓ Updated {len(updates)} Facebook Ads campaigns with performance data")

def update_linkedin_ads_performance():
    """Update LinkedIn Ads campaigns with performance data."""
    print("\nUpdating LinkedIn Ads campaign performance...")
    
    with db_helper.config.get_cursor() as cursor:
        # Get all campaigns
        cursor.execute("SELECT * FROM raw.linkedin_ads_campaigns")
        campaigns = cursor.fetchall()
        
        updates = []
        for campaign in campaigns:
            start_date = campaign[6]  # start_date column
            end_date = campaign[7]    # end_date column
            
            if start_date > datetime.now().date():
                continue
            
            # Calculate days running
            current_date = min(datetime.now().date(), end_date)
            days_running = (current_date - start_date).days + 1
            
            # Get budget
            daily_budget = float(campaign[8]) if campaign[8] else 200
            
            # Simulate performance (LinkedIn has lower volume but higher quality)
            total_impressions = 0
            total_clicks = 0
            total_cost = 0
            total_conversions = 0
            
            rates, _ = calculate_daily_performance(campaign, 'linkedin_ads', 0, 1.0)
            
            for day in range(days_running):
                current_day = start_date + timedelta(days=day)
                dow = current_day.weekday()
                
                # B2B seasonality (lower in summer)
                month = current_day.month
                season_factor = 0.8 if month in [6, 7, 8] else 1.0
                
                _, perf_factor = calculate_daily_performance(campaign, 'linkedin_ads', dow, season_factor)
                
                # LinkedIn has lower volume
                daily_impressions = int(random.randint(500, 5000) * perf_factor)
                daily_clicks = int(daily_impressions * rates['ctr'] * perf_factor)
                daily_cost = min(daily_clicks * rates['cpc'], daily_budget * 0.95)
                daily_conversions = int(daily_clicks * rates['conversion_rate'])
                
                total_impressions += daily_impressions
                total_clicks += daily_clicks
                total_cost += daily_cost
                total_conversions += daily_conversions
            
            updates.append({
                'id': campaign[0],
                'impressions': total_impressions,
                'clicks': total_clicks,
                'cost': round(total_cost, 2),
                'conversions': total_conversions
            })
        
        # Batch update
        for update in updates:
            cursor.execute("""
                UPDATE raw.linkedin_ads_campaigns 
                SET impressions = %s, clicks = %s, cost = %s, conversions = %s
                WHERE id = %s
            """, (update['impressions'], update['clicks'], update['cost'], 
                  update['conversions'], update['id']))
        
        print(f"✓ Updated {len(updates)} LinkedIn Ads campaigns with performance data")

def generate_performance_summary():
    """Generate a summary of all campaign performance."""
    print("\nGenerating performance summary...")
    
    summary = {
        'total_impressions': 0,
        'total_clicks': 0,
        'total_spend': 0,
        'total_conversions': 0,
        'platform_breakdown': {}
    }
    
    with db_helper.config.get_cursor() as cursor:
        # Google Ads
        cursor.execute("""
            SELECT SUM(impressions), SUM(clicks), SUM(cost), SUM(conversions)
            FROM raw.google_ads_campaigns
        """)
        google_stats = cursor.fetchone()
        summary['platform_breakdown']['google_ads'] = {
            'impressions': int(google_stats[0] or 0),
            'clicks': int(google_stats[1] or 0),
            'spend': float(google_stats[2] or 0),
            'conversions': int(google_stats[3] or 0)
        }
        
        # Facebook Ads
        cursor.execute("""
            SELECT SUM(impressions), SUM(clicks), SUM(spend)
            FROM raw.facebook_ads_campaigns
        """)
        fb_stats = cursor.fetchone()
        summary['platform_breakdown']['facebook_ads'] = {
            'impressions': int(fb_stats[0] or 0),
            'clicks': int(fb_stats[1] or 0),
            'spend': float(fb_stats[2] or 0)
        }
        
        # LinkedIn Ads
        cursor.execute("""
            SELECT SUM(impressions), SUM(clicks), SUM(cost), SUM(conversions)
            FROM raw.linkedin_ads_campaigns
        """)
        li_stats = cursor.fetchone()
        summary['platform_breakdown']['linkedin_ads'] = {
            'impressions': int(li_stats[0] or 0),
            'clicks': int(li_stats[1] or 0),
            'spend': float(li_stats[2] or 0),
            'conversions': int(li_stats[3] or 0)
        }
    
    # Calculate totals
    for platform in summary['platform_breakdown'].values():
        summary['total_impressions'] += platform.get('impressions', 0)
        summary['total_clicks'] += platform.get('clicks', 0)
        summary['total_spend'] += platform.get('spend', 0)
        summary['total_conversions'] += platform.get('conversions', 0)
    
    # Save summary
    with open('data/campaign_performance_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def main():
    print("=== Generating Campaign Performance Data ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Update performance for each platform
    update_google_ads_performance()
    update_facebook_ads_performance()
    update_linkedin_ads_performance()
    
    # Generate summary
    summary = generate_performance_summary()
    
    print("\n=== Performance Summary ===")
    print(f"Total Impressions: {summary['total_impressions']:,}")
    print(f"Total Clicks: {summary['total_clicks']:,}")
    print(f"Total Spend: ${summary['total_spend']:,.2f}")
    print(f"Total Conversions: {summary['total_conversions']:,}")
    
    if summary['total_impressions'] > 0:
        overall_ctr = (summary['total_clicks'] / summary['total_impressions']) * 100
        print(f"Overall CTR: {overall_ctr:.2f}%")
    
    if summary['total_clicks'] > 0:
        overall_cpc = summary['total_spend'] / summary['total_clicks']
        print(f"Overall CPC: ${overall_cpc:.2f}")
    
    if summary['total_conversions'] > 0:
        overall_cpa = summary['total_spend'] / summary['total_conversions']
        print(f"Overall CPA: ${overall_cpa:.2f}")
    
    print("\n✓ Campaign performance data generation complete")
    print("✓ Performance summary saved to data/campaign_performance_summary.json")

if __name__ == "__main__":
    main()