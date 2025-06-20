#!/usr/bin/env python3
"""
Generate synthetic user sessions data for the bar management SaaS platform.

This script creates:
- 50,000 user sessions with login patterns by role
- Session duration distributions
- Device type patterns
- Geographic IP distribution
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import math
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_users():
    """Load existing users data."""
    with open('data/generated_users.json', 'r') as f:
        return json.load(f)

def generate_user_sessions(env_config):
    """Generate user sessions data."""
    sessions = []
    users = load_users()
    
    # Session patterns by role
    role_patterns = {
        'admin': {
            'sessions_per_week': 20,
            'avg_duration': 1800,  # 30 minutes
            'page_views_per_session': 15,
            'actions_per_session': 25,
            'peak_hours': range(9, 18),  # 9 AM - 6 PM
            'work_days': [0, 1, 2, 3, 4]  # Mon-Fri
        },
        'manager': {
            'sessions_per_week': 15,
            'avg_duration': 1200,  # 20 minutes
            'page_views_per_session': 10,
            'actions_per_session': 18,
            'peak_hours': range(10, 20),  # 10 AM - 8 PM
            'work_days': [0, 1, 2, 3, 4, 5]  # Mon-Sat
        },
        'staff': {
            'sessions_per_week': 8,
            'avg_duration': 600,  # 10 minutes
            'page_views_per_session': 6,
            'actions_per_session': 10,
            'peak_hours': range(14, 23),  # 2 PM - 11 PM
            'work_days': [0, 1, 2, 3, 4, 5, 6]  # All week
        }
    }
    
    # Device type distribution
    device_types = {
        'desktop': 0.45,
        'mobile': 0.35,
        'tablet': 0.20
    }
    
    # Browser distribution
    browsers_by_device = {
        'desktop': ['Chrome', 'Firefox', 'Safari', 'Edge'],
        'mobile': ['Mobile Safari', 'Chrome Mobile', 'Samsung Browser', 'Firefox Mobile'],
        'tablet': ['Safari', 'Chrome', 'Firefox']
    }
    
    # Calculate sessions per user based on activity level
    total_sessions_needed = 50000
    active_users = [u for u in users if u['is_active']]
    
    # First allocate 45,000 sessions to logged-in users
    logged_in_sessions = 45000
    
    # Distribute sessions across users (power law distribution)
    user_session_counts = []
    
    # Sort users by account_id to ensure consistent distribution
    active_users.sort(key=lambda x: x['id'])
    
    # Calculate sessions per user group
    top_20_percent = int(len(active_users) * 0.2)
    next_30_percent = int(len(active_users) * 0.5) - top_20_percent
    remaining_users = len(active_users) - top_20_percent - next_30_percent
    
    # Allocate sessions proportionally
    sessions_for_top = int(logged_in_sessions * 0.6)  # 60% of sessions from top 20%
    sessions_for_middle = int(logged_in_sessions * 0.3)  # 30% from middle 30%
    sessions_for_bottom = logged_in_sessions - sessions_for_top - sessions_for_middle  # 10% from bottom
    
    # Distribute within each group
    for i, user in enumerate(active_users):
        if i < top_20_percent:
            # Top users get more sessions
            sessions_for_user = max(100, sessions_for_top // top_20_percent + random.randint(-20, 20))
        elif i < top_20_percent + next_30_percent:
            # Middle users
            sessions_for_user = max(30, sessions_for_middle // next_30_percent + random.randint(-10, 10))
        else:
            # Bottom users
            sessions_for_user = max(5, sessions_for_bottom // remaining_users + random.randint(-2, 2))
        
        user_session_counts.append((user, sessions_for_user))
    
    # Generate sessions for each user
    for user, num_sessions in user_session_counts:
        user_role = user['role'].lower()
        pattern = role_patterns.get(user_role, role_patterns['staff'])
        
        # Spread sessions over last 90 days
        for _ in range(num_sessions):
            session_id = str(uuid.uuid4())
            
            # Random date in last 90 days
            days_ago = random.randint(0, 90)
            session_date = datetime.now() - timedelta(days=days_ago)
            
            # Time of day based on role pattern
            if session_date.weekday() in pattern['work_days']:
                hour = random.choice(list(pattern['peak_hours']))
            else:
                # Off hours - less likely
                hour = random.randint(0, 23)
            
            minute = random.randint(0, 59)
            start_time = session_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Session duration (log-normal distribution)
            avg_duration = pattern['avg_duration']
            duration_seconds = int(random.lognormvariate(
                math.log(avg_duration), 
                0.5
            ))
            duration_seconds = max(30, min(duration_seconds, 7200))  # 30s to 2 hours
            
            end_time = start_time + timedelta(seconds=duration_seconds)
            
            # Page views and actions (correlated with duration)
            duration_factor = duration_seconds / avg_duration
            page_views = max(1, int(pattern['page_views_per_session'] * duration_factor * random.uniform(0.7, 1.3)))
            actions_taken = max(1, int(pattern['actions_per_session'] * duration_factor * random.uniform(0.8, 1.2)))
            
            # Device type
            device_type = random.choices(
                list(device_types.keys()),
                weights=list(device_types.values())
            )[0]
            
            # Browser based on device
            browser = random.choice(browsers_by_device[device_type])
            
            session = {
                'session_id': session_id,
                'user_id': user['id'],
                'customer_id': user['account_id'],
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration_seconds,
                'page_views': page_views,
                'actions_taken': actions_taken,
                'device_type': device_type,
                'browser': browser,
                'created_at': start_time.isoformat()
            }
            
            sessions.append(session)
    
    # Add anonymous/logged-out sessions to reach exactly 50,000
    logged_in_count = len(sessions)
    anonymous_sessions_needed = total_sessions_needed - logged_in_count
    
    if anonymous_sessions_needed > 0:
        for _ in range(anonymous_sessions_needed):
            session_id = str(uuid.uuid4())
            
            days_ago = random.randint(0, 90)
            session_date = datetime.now() - timedelta(days=days_ago)
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            start_time = session_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Anonymous sessions are typically shorter
            duration_seconds = random.randint(30, 300)
            end_time = start_time + timedelta(seconds=duration_seconds)
            
            # Fewer page views for anonymous
            page_views = random.randint(1, 5)
            actions_taken = random.randint(0, 3)
            
            device_type = random.choices(
                list(device_types.keys()),
                weights=list(device_types.values())
            )[0]
            browser = random.choice(browsers_by_device[device_type])
            
            session = {
                'session_id': session_id,
                'user_id': 0,  # Anonymous user
                'customer_id': 0,  # No customer
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration_seconds,
                'page_views': page_views,
                'actions_taken': actions_taken,
                'device_type': device_type,
                'browser': browser,
                'created_at': start_time.isoformat()
            }
            
            sessions.append(session)
    
    return sessions[:50000]  # Ensure exactly 50,000

def save_sessions_summary(sessions):
    """Save sessions summary for future reference."""
    summary = {
        'total_sessions': len(sessions),
        'unique_users': len(set(s['user_id'] for s in sessions if s['user_id'] > 0)),
        'anonymous_sessions': len([s for s in sessions if s['user_id'] == 0]),
        'avg_duration': sum(s['duration_seconds'] for s in sessions) / len(sessions),
        'avg_page_views': sum(s['page_views'] for s in sessions) / len(sessions),
        'device_breakdown': {},
        'browser_breakdown': {},
        'sessions_by_hour': {}
    }
    
    # Device and browser breakdown
    for session in sessions:
        device = session['device_type']
        browser = session['browser']
        hour = datetime.fromisoformat(session['start_time']).hour
        
        summary['device_breakdown'][device] = summary['device_breakdown'].get(device, 0) + 1
        summary['browser_breakdown'][browser] = summary['browser_breakdown'].get(browser, 0) + 1
        summary['sessions_by_hour'][hour] = summary['sessions_by_hour'].get(hour, 0) + 1
    
    with open('data/user_sessions_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved user sessions summary to data/user_sessions_summary.json")

def main():
    print("=== Generating User Sessions ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate sessions
    print("\nGenerating user sessions...")
    sessions = generate_user_sessions(env_config)
    print(f"✓ Generated {len(sessions)} user sessions")
    
    # Statistics
    unique_users = len(set(s['user_id'] for s in sessions if s['user_id'] > 0))
    anonymous = len([s for s in sessions if s['user_id'] == 0])
    avg_duration = sum(s['duration_seconds'] for s in sessions) / len(sessions)
    avg_pages = sum(s['page_views'] for s in sessions) / len(sessions)
    
    print(f"\nSession Statistics:")
    print(f"  - Unique Users: {unique_users}")
    print(f"  - Anonymous Sessions: {anonymous} ({anonymous/len(sessions)*100:.1f}%)")
    print(f"  - Average Duration: {avg_duration/60:.1f} minutes")
    print(f"  - Average Page Views: {avg_pages:.1f}")
    
    # Device breakdown
    devices = {}
    for session in sessions:
        device = session['device_type']
        devices[device] = devices.get(device, 0) + 1
    
    print("\nDevice Type Distribution:")
    for device, count in sorted(devices.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(sessions)) * 100
        print(f"  - {device}: {count:,} ({percentage:.1f}%)")
    
    # Peak hours analysis
    hours = {}
    for session in sessions:
        hour = datetime.fromisoformat(session['start_time']).hour
        hours[hour] = hours.get(hour, 0) + 1
    
    print("\nPeak Usage Hours (Top 5):")
    for hour, count in sorted(hours.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {hour:02d}:00: {count:,} sessions")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('app_database_user_sessions', sessions)
    
    # Save summary
    save_sessions_summary(sessions)
    
    # Verify
    count = db_helper.get_row_count('app_database_user_sessions')
    print(f"\n✓ Total user sessions in database: {count:,}")

if __name__ == "__main__":
    main()