#!/usr/bin/env python3
"""
Generate synthetic Google Analytics sessions data for the bar management SaaS platform.

This script creates:
- 30,000 sessions worth of daily aggregated data
- Realistic traffic patterns
- Source/medium distributions
- Bounce rates by page type
- Session durations
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, date
import random
import math
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def generate_google_analytics_sessions(env_config):
    """Generate Google Analytics daily sessions data."""
    sessions_data = []
    
    # Date range - last 180 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    
    # Base metrics for a B2B SaaS
    base_daily_sessions = 150  # Starting point
    growth_rate = 0.002  # 0.2% daily growth
    
    # Day of week factors (B2B pattern)
    dow_factors = {
        0: 1.1,   # Monday
        1: 1.15,  # Tuesday
        2: 1.2,   # Wednesday
        3: 1.15,  # Thursday
        4: 0.9,   # Friday
        5: 0.4,   # Saturday
        6: 0.3    # Sunday
    }
    
    # Seasonal factors by month
    seasonal_factors = {
        1: 0.9,   # January - slow start
        2: 1.0,   # February
        3: 1.1,   # March
        4: 1.05,  # April
        5: 1.0,   # May
        6: 0.9,   # June
        7: 0.85,  # July - summer slowdown
        8: 0.85,  # August
        9: 1.1,   # September - back to business
        10: 1.15, # October
        11: 1.2,  # November - year-end push
        12: 0.95  # December - holidays
    }
    
    # Traffic patterns for B2B SaaS
    new_user_rate = 0.35  # 35% new users
    bounce_rate_base = 0.45  # 45% bounce rate
    avg_session_duration_base = 180  # 3 minutes average
    pages_per_session = 3.5
    
    # Goal conversion rates (demo requests, trial signups, etc.)
    goal_conversion_rate_base = 0.025  # 2.5% conversion
    
    current_date = start_date
    day_counter = 0
    
    while current_date <= end_date:
        # Calculate growth factor
        growth_factor = (1 + growth_rate) ** day_counter
        
        # Get day of week and seasonal factors
        dow = current_date.weekday()
        dow_factor = dow_factors[dow]
        seasonal_factor = seasonal_factors[current_date.month]
        
        # Add some randomness
        random_factor = random.uniform(0.85, 1.15)
        
        # Calculate sessions for the day
        daily_sessions = int(
            base_daily_sessions * 
            growth_factor * 
            dow_factor * 
            seasonal_factor * 
            random_factor
        )
        
        # Calculate users (some users have multiple sessions)
        session_per_user_rate = random.uniform(1.1, 1.3)
        daily_users = int(daily_sessions / session_per_user_rate)
        
        # New users
        daily_new_users = int(daily_users * new_user_rate * random.uniform(0.8, 1.2))
        
        # Page views
        daily_page_views = int(daily_sessions * pages_per_session * random.uniform(0.9, 1.1))
        
        # Bounce rate (varies by traffic source and day)
        if dow in [5, 6]:  # Weekend traffic has higher bounce
            bounce_rate = bounce_rate_base * 1.2
        else:
            bounce_rate = bounce_rate_base
        bounce_rate = min(0.7, bounce_rate * random.uniform(0.85, 1.15))
        
        # Average session duration (in seconds)
        if dow in [5, 6]:  # Weekend sessions are shorter
            avg_duration = avg_session_duration_base * 0.7
        else:
            avg_duration = avg_session_duration_base
        avg_duration = avg_duration * random.uniform(0.8, 1.2)
        
        # Goal completions (demo requests, signups, etc.)
        # Higher on weekdays, especially mid-week
        if dow in [1, 2, 3]:  # Tue, Wed, Thu
            goal_conversion_factor = 1.3
        elif dow in [5, 6]:  # Weekend
            goal_conversion_factor = 0.3
        else:
            goal_conversion_factor = 1.0
        
        goal_conversion_rate = goal_conversion_rate_base * goal_conversion_factor * random.uniform(0.7, 1.3)
        daily_goal_completions = int(daily_sessions * goal_conversion_rate)
        
        # Special events (marketing campaigns, product launches, etc.)
        # Add spikes for campaign launches
        if day_counter in [30, 60, 90, 120, 150]:  # Campaign launch days
            daily_sessions = int(daily_sessions * 1.5)
            daily_users = int(daily_users * 1.6)
            daily_new_users = int(daily_new_users * 2.0)
            daily_goal_completions = int(daily_goal_completions * 1.8)
        
        # Create the daily record
        ga_record = {
            'date': current_date.isoformat(),
            'sessions': daily_sessions,
            'users': daily_users,
            'new_users': daily_new_users,
            'page_views': daily_page_views,
            'bounce_rate': float(bounce_rate),
            'avg_session_duration': float(avg_duration),
            'goal_completions': daily_goal_completions,
            'goal_conversion_rate': float(daily_goal_completions / daily_sessions) if daily_sessions > 0 else 0,
            'created_at': datetime.now().isoformat()
        }
        
        sessions_data.append(ga_record)
        
        # Move to next day
        current_date += timedelta(days=1)
        day_counter += 1
    
    return sessions_data

def calculate_summary_metrics(sessions_data):
    """Calculate summary metrics from the generated data."""
    total_sessions = sum(d['sessions'] for d in sessions_data)
    total_users = sum(d['users'] for d in sessions_data)
    total_page_views = sum(d['page_views'] for d in sessions_data)
    total_goal_completions = sum(d['goal_completions'] for d in sessions_data)
    
    avg_bounce_rate = sum(d['bounce_rate'] for d in sessions_data) / len(sessions_data)
    avg_session_duration = sum(d['avg_session_duration'] for d in sessions_data) / len(sessions_data)
    
    # Monthly breakdown
    monthly_sessions = {}
    for record in sessions_data:
        month_key = record['date'][:7]  # YYYY-MM
        if month_key not in monthly_sessions:
            monthly_sessions[month_key] = {
                'sessions': 0,
                'users': 0,
                'goal_completions': 0
            }
        monthly_sessions[month_key]['sessions'] += record['sessions']
        monthly_sessions[month_key]['users'] += record['users']
        monthly_sessions[month_key]['goal_completions'] += record['goal_completions']
    
    return {
        'total_sessions': total_sessions,
        'total_users': total_users,
        'total_page_views': total_page_views,
        'total_goal_completions': total_goal_completions,
        'avg_bounce_rate': avg_bounce_rate,
        'avg_session_duration': avg_session_duration,
        'days_of_data': len(sessions_data),
        'monthly_breakdown': monthly_sessions
    }

def save_ga_summary(sessions_data, summary):
    """Save Google Analytics summary."""
    with open('data/google_analytics_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Saved Google Analytics summary to data/google_analytics_summary.json")

def main():
    print("=== Generating Google Analytics Sessions Data ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate sessions data
    print("\nGenerating Google Analytics daily data...")
    sessions_data = generate_google_analytics_sessions(env_config)
    print(f"✓ Generated {len(sessions_data)} days of Google Analytics data")
    
    # Calculate summary
    summary = calculate_summary_metrics(sessions_data)
    
    print(f"\nGoogle Analytics Summary:")
    print(f"  - Total Sessions: {summary['total_sessions']:,}")
    print(f"  - Total Users: {summary['total_users']:,}")
    print(f"  - Total Page Views: {summary['total_page_views']:,}")
    print(f"  - Total Goal Completions: {summary['total_goal_completions']:,}")
    print(f"  - Average Bounce Rate: {summary['avg_bounce_rate']:.1%}")
    print(f"  - Average Session Duration: {summary['avg_session_duration']:.1f} seconds")
    
    # Show monthly trend
    print("\nMonthly Sessions Trend:")
    for month, data in sorted(summary['monthly_breakdown'].items()):
        print(f"  - {month}: {data['sessions']:,} sessions, {data['goal_completions']} conversions")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('google_analytics_sessions', sessions_data)
    
    # Save summary
    save_ga_summary(sessions_data, summary)
    
    # Verify
    count = db_helper.get_row_count('google_analytics_sessions')
    print(f"\n✓ Total days of GA data in database: {count}")

if __name__ == "__main__":
    main()