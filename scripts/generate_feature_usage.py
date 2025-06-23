#!/usr/bin/env python3
"""
Generate synthetic feature usage data for the bar management SaaS platform.

This script creates:
- 150,000 feature usage events
- Tracking of different feature types by role
- Feature adoption metrics
- Usage intensity patterns
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_users():
    """Load users with roles and accounts."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, customer_id, role, last_login_date
            FROM raw.app_database_users
        """)
        users = []
        for row in cursor.fetchall():
            user = dict(zip(['id', 'customer_id', 'role', 'last_login_date'], row))
            # Consider users active if they logged in within last 30 days
            if user['last_login_date']:
                days_since_login = (datetime.now().date() - user['last_login_date']).days
                user['is_active'] = days_since_login <= 30
            else:
                user['is_active'] = False
            users.append(user)
        return users

def generate_feature_usage(env_config):
    """Generate feature usage data."""
    users = load_users()
    active_users = [u for u in users if u['is_active']]
    feature_events = []
    
    # Features by role with usage intensity
    features_by_role = {
        'admin': {
            'dashboard_analytics': {'frequency': 'daily', 'avg_events_per_use': 10},
            'revenue_reports': {'frequency': 'daily', 'avg_events_per_use': 5},
            'user_management': {'frequency': 'weekly', 'avg_events_per_use': 8},
            'billing_management': {'frequency': 'monthly', 'avg_events_per_use': 6},
            'export_data': {'frequency': 'weekly', 'avg_events_per_use': 3},
            'integrations_config': {'frequency': 'monthly', 'avg_events_per_use': 4},
            'account_settings': {'frequency': 'weekly', 'avg_events_per_use': 5},
            'audit_logs': {'frequency': 'weekly', 'avg_events_per_use': 7}
        },
        'manager': {
            'dashboard_overview': {'frequency': 'daily', 'avg_events_per_use': 8},
            'inventory_management': {'frequency': 'daily', 'avg_events_per_use': 15},
            'sales_reports': {'frequency': 'daily', 'avg_events_per_use': 6},
            'device_monitoring': {'frequency': 'daily', 'avg_events_per_use': 5},
            'staff_scheduling': {'frequency': 'weekly', 'avg_events_per_use': 10},
            'location_analytics': {'frequency': 'weekly', 'avg_events_per_use': 7},
            'product_management': {'frequency': 'weekly', 'avg_events_per_use': 12},
            'supplier_orders': {'frequency': 'weekly', 'avg_events_per_use': 8}
        },
        'staff': {
            'pos_system': {'frequency': 'daily', 'avg_events_per_use': 25},
            'inventory_check': {'frequency': 'daily', 'avg_events_per_use': 10},
            'order_management': {'frequency': 'daily', 'avg_events_per_use': 20},
            'customer_lookup': {'frequency': 'daily', 'avg_events_per_use': 8},
            'schedule_view': {'frequency': 'weekly', 'avg_events_per_use': 3},
            'product_search': {'frequency': 'daily', 'avg_events_per_use': 15},
            'quick_sale': {'frequency': 'daily', 'avg_events_per_use': 12},
            'shift_report': {'frequency': 'daily', 'avg_events_per_use': 4}
        }
    }
    
    # Event types per feature
    event_types = [
        'view', 'click', 'create', 'update', 'delete', 
        'export', 'search', 'filter', 'save', 'submit'
    ]
    
    # Calculate events needed per user
    total_events_needed = 150000
    events_per_user = total_events_needed // len(active_users)
    
    # Generate events for each active user
    for user in active_users:
        role = user['role'].lower()
        if role not in features_by_role:
            role = 'staff'  # Default to staff features
        
        user_features = features_by_role[role]
        
        # Determine which features this user has adopted
        adopted_features = []
        for feature, config in user_features.items():
            # Adoption probability based on frequency
            if config['frequency'] == 'daily':
                adoption_prob = 0.8
            elif config['frequency'] == 'weekly':
                adoption_prob = 0.6
            else:  # monthly
                adoption_prob = 0.4
            
            if random.random() < adoption_prob:
                adopted_features.append((feature, config))
        
        if not adopted_features:
            continue
        
        # Generate events for adopted features over last 90 days
        user_events = []
        for _ in range(events_per_user):
            # Select a feature weighted by usage frequency
            feature, config = random.choice(adopted_features)
            
            # Random timestamp in last 90 days
            days_ago = random.randint(0, 90)
            event_date = datetime.now() - timedelta(days=days_ago)
            
            # Time of day based on role
            if role == 'admin':
                hour = random.choice(list(range(9, 18)))  # Business hours
            elif role == 'manager':
                hour = random.choice(list(range(10, 20)))  # Extended hours
            else:  # staff
                hour = random.choice(list(range(14, 23)))  # Afternoon/evening
            
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = event_date.replace(hour=hour, minute=minute, second=second)
            
            # For aggregated usage, simulate multiple events in one record
            usage_count = random.randint(1, config['avg_events_per_use'])
            
            event = {
                'usage_id': str(uuid.uuid4()),
                'user_id': user['id'],
                'customer_id': user['customer_id'],
                'feature_name': feature,
                'usage_count': usage_count,
                'timestamp': timestamp.isoformat(),
                'created_at': timestamp.isoformat()
            }
            
            user_events.append(event)
        
        feature_events.extend(user_events)
    
    # Trim to exact count needed
    return feature_events[:150000]

def save_feature_usage_summary(events):
    """Save feature usage summary for future reference."""
    summary = {
        'total_events': len(events),
        'unique_users': len(set(e['user_id'] for e in events)),
        'unique_features': len(set(e['feature_name'] for e in events)),
        'events_by_feature': {},
        'total_usage_count': sum(e['usage_count'] for e in events),
        'daily_average': 0
    }
    
    # Count by feature
    for event in events:
        feature = event['feature_name']
        summary['events_by_feature'][feature] = summary['events_by_feature'].get(feature, 0) + 1
    
    # Calculate daily average
    if events:
        dates = set(datetime.fromisoformat(e['timestamp']).date() for e in events)
        summary['daily_average'] = len(events) / len(dates)
    
    with open('data/feature_usage_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved feature usage summary to data/feature_usage_summary.json")

def main():
    print("=== Generating Feature Usage ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate feature usage
    print("\nGenerating feature usage events...")
    events = generate_feature_usage(env_config)
    print(f"✓ Generated {len(events)} feature usage events")
    
    # Statistics
    unique_users = len(set(e['user_id'] for e in events))
    unique_features = len(set(e['feature_name'] for e in events))
    
    print(f"\nFeature Usage Statistics:")
    print(f"  - Unique Users: {unique_users:,}")
    print(f"  - Unique Features: {unique_features}")
    if unique_users > 0:
        print(f"  - Events per User: {len(events) / unique_users:.1f}")
    else:
        print(f"  - Events per User: 0")
    
    # Top features
    feature_counts = {}
    for event in events:
        feature = event['feature_name']
        feature_counts[feature] = feature_counts.get(feature, 0) + 1
    
    print("\nTop 10 Features by Usage:")
    for feature, count in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / len(events)) * 100
        print(f"  - {feature}: {count:,} events ({percentage:.1f}%)")
    
    # Usage intensity
    total_usage = sum(e['usage_count'] for e in events)
    print(f"\nUsage Intensity:")
    print(f"  - Total Usage Count: {total_usage:,}")
    if len(events) > 0:
        print(f"  - Average Usage per Event: {total_usage / len(events):.1f}")
    else:
        print(f"  - Average Usage per Event: 0")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('app_database_feature_usage', events)
    
    # Save summary
    save_feature_usage_summary(events)
    
    # Verify
    count = db_helper.get_row_count('app_database_feature_usage')
    print(f"\n✓ Total feature usage events in database: {count:,}")

if __name__ == "__main__":
    main()