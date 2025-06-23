#!/usr/bin/env python3
"""
Generate synthetic page views data for the bar management SaaS platform.

This script creates:
- 250,000 page views linked to user sessions
- Page path patterns based on user roles
- Page load performance metrics
- Conversion funnel tracking
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

def load_user_sessions():
    """Load user sessions from database."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT session_id, user_id, customer_id, 
                   start_time, end_time, page_views, device_type
            FROM raw.app_database_user_sessions
            ORDER BY start_time
        """)
        return [dict(zip(['session_id', 'user_id', 'customer_id', 
                         'start_time', 'end_time', 'page_views', 'device_type'], row)) 
                for row in cursor.fetchall()]

def load_users():
    """Load users with roles."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, role
            FROM raw.app_database_users
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}

def generate_page_views(env_config):
    """Generate page views data."""
    sessions = load_user_sessions()
    users = load_users()
    page_views = []
    
    # Page paths by role
    page_paths = {
        'admin': {
            'common': [
                '/dashboard', '/analytics', '/reports/revenue', '/reports/usage',
                '/accounts', '/accounts/{id}', '/users', '/users/{id}',
                '/settings', '/settings/billing', '/settings/integrations'
            ],
            'frequent': [
                '/dashboard', '/analytics', '/reports/revenue', '/accounts'
            ],
            'conversion': [
                '/accounts', '/accounts/{id}', '/accounts/{id}/edit',
                '/accounts/{id}/subscription', '/accounts/{id}/subscription/upgrade'
            ]
        },
        'manager': {
            'common': [
                '/dashboard', '/locations', '/locations/{id}', '/devices',
                '/devices/{id}', '/inventory', '/inventory/products',
                '/reports/sales', '/reports/inventory', '/staff'
            ],
            'frequent': [
                '/dashboard', '/locations', '/inventory', '/reports/sales'
            ],
            'conversion': [
                '/inventory', '/inventory/products', '/inventory/products/{id}',
                '/inventory/products/{id}/order', '/inventory/orders/confirm'
            ]
        },
        'staff': {
            'common': [
                '/dashboard', '/pos', '/pos/orders', '/pos/products',
                '/inventory/check', '/schedule', '/profile', '/help'
            ],
            'frequent': [
                '/pos', '/pos/orders', '/dashboard'
            ],
            'conversion': [
                '/pos', '/pos/products', '/pos/cart', '/pos/checkout', '/pos/receipt'
            ]
        }
    }
    
    # Default paths for anonymous users
    default_paths = {
        'common': [
            '/', '/features', '/pricing', '/about', '/contact',
            '/login', '/signup', '/demo', '/blog', '/blog/{slug}'
        ],
        'frequent': [
            '/', '/features', '/pricing', '/login'
        ],
        'conversion': [
            '/', '/features', '/pricing', '/signup', '/signup/complete'
        ]
    }
    
    # Performance metrics by device type
    load_time_ranges = {
        'desktop': (500, 2000),    # ms
        'mobile': (800, 3500),
        'tablet': (600, 2500)
    }
    
    page_view_id = 1
    
    for session in sessions:
        session_start = session['start_time']
        session_end = session['end_time']
        num_pages = session['page_views']
        
        if num_pages == 0:
            continue
            
        # Get user role
        user_id = session['user_id']
        role = users.get(user_id, '').lower() if user_id and user_id != '0' else None
        
        # Select page patterns based on role
        if role and role in page_paths:
            paths = page_paths[role]
        else:
            paths = default_paths
        
        # Calculate time between pages
        session_duration = (session_end - session_start).total_seconds()
        if num_pages > 1:
            avg_time_per_page = session_duration / num_pages
        else:
            avg_time_per_page = session_duration
        
        # Determine if this is a conversion session
        is_conversion = random.random() < 0.05  # 5% conversion rate
        
        # Generate page views for this session
        current_time = session_start
        
        for page_num in range(num_pages):
            # Select page path
            if is_conversion and page_num < len(paths.get('conversion', [])):
                # Follow conversion funnel
                page_path = paths['conversion'][page_num]
            elif page_num == 0:
                # First page - often a common entry point
                page_path = random.choice(paths['frequent'])
            else:
                # Subsequent pages
                if random.random() < 0.7:  # 70% chance of common page
                    page_path = random.choice(paths['common'])
                else:
                    page_path = random.choice(paths['frequent'])
            
            # Replace placeholders in path
            if '{id}' in page_path:
                page_path = page_path.replace('{id}', str(random.randint(1, 1000)))
            elif '{slug}' in page_path:
                page_path = page_path.replace('{slug}', fake.slug())
            
            # Page title based on path
            page_title = page_path.strip('/').replace('/', ' - ').title()
            if page_title == '':
                page_title = 'Home'
            
            # Load time based on device
            device_type = session['device_type']
            min_load, max_load = load_time_ranges.get(device_type, (500, 2000))
            load_time_ms = random.randint(min_load, max_load)
            
            # Time on page
            if page_num < num_pages - 1:
                # Not the last page
                time_on_page = random.uniform(
                    avg_time_per_page * 0.3,
                    avg_time_per_page * 2.0
                )
            else:
                # Last page - might be shorter
                time_on_page = random.uniform(
                    avg_time_per_page * 0.1,
                    avg_time_per_page * 1.5
                )
            
            # Bounce (only for first page)
            bounced = page_num == 0 and num_pages == 1
            
            # Exit page (only for last page)
            is_exit = page_num == num_pages - 1
            
            page_view = {
                'page_view_id': str(uuid.uuid4()),
                'session_id': session['session_id'],
                'user_id': user_id if user_id and user_id != '0' else '0',
                'customer_id': session['customer_id'] if session['customer_id'] and session['customer_id'] != '0' else '0',
                'page_url': 'https://app.barsaas.com' + page_path,
                'page_title': page_title,
                'time_on_page_seconds': int(time_on_page),
                'referrer_url': 'https://app.barsaas.com' + paths['frequent'][0] if page_num > 0 else None,
                'timestamp': current_time.isoformat(),
                'created_at': current_time.isoformat()
            }
            
            page_views.append(page_view)
            page_view_id += 1
            
            # Move to next page time
            current_time += timedelta(seconds=time_on_page)
            
            # Stop if we've exceeded session end time
            if current_time > session_end:
                break
    
    return page_views[:250000]  # Ensure exactly 250,000

def save_page_views_summary(page_views):
    """Save page views summary for future reference."""
    summary = {
        'total_page_views': len(page_views),
        'unique_sessions': len(set(pv['session_id'] for pv in page_views)),
        'avg_load_time_ms': 0,  # Not tracked in this table
        'avg_time_on_page': sum(pv['time_on_page_seconds'] for pv in page_views) / len(page_views),
        'bounce_rate': 0.0,  # Not tracked in this table
        'top_pages': {},
        'pages_by_role': {}
    }
    
    # Top pages
    page_counts = {}
    for pv in page_views:
        path = pv['page_url'].replace('https://app.barsaas.com', '')
        page_counts[path] = page_counts.get(path, 0) + 1
    
    # Get top 20 pages
    top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    summary['top_pages'] = dict(top_pages)
    
    with open('data/page_views_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved page views summary to data/page_views_summary.json")

def main():
    print("=== Generating Page Views ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate page views
    print("\nGenerating page views...")
    page_views = generate_page_views(env_config)
    print(f"✓ Generated {len(page_views)} page views")
    
    # Statistics
    unique_sessions = len(set(pv['session_id'] for pv in page_views))
    # avg_load_time = sum(pv['page_load_time_ms'] for pv in page_views) / len(page_views)
    avg_time_on_page = sum(pv['time_on_page_seconds'] for pv in page_views) / len(page_views)
    # bounce_rate = len([pv for pv in page_views if pv['bounce']]) / len(page_views)
    
    print(f"\nPage View Statistics:")
    print(f"  - Unique Sessions: {unique_sessions:,}")
    print(f"  - Average Time on Page: {avg_time_on_page:.1f} seconds")
    
    # Top pages
    page_counts = {}
    for pv in page_views:
        path = pv['page_url'].replace('https://app.barsaas.com', '')
        page_counts[path] = page_counts.get(path, 0) + 1
    
    print("\nTop 10 Pages:")
    for path, count in sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / len(page_views)) * 100
        print(f"  - {path}: {count:,} ({percentage:.1f}%)")
    
    # Insert into database
    print("\nInserting into database...")
    db_helper.bulk_insert('app_database_page_views', page_views)
    
    # Save summary
    save_page_views_summary(page_views)
    
    # Verify
    count = db_helper.get_row_count('app_database_page_views')
    print(f"\n✓ Total page views in database: {count:,}")

if __name__ == "__main__":
    main()