#!/usr/bin/env python3
"""
Generate synthetic Iterable email campaigns data for the bar management SaaS platform.

This module creates Iterable email marketing campaign records with:
- Newsletter campaigns
- Promotional campaigns
- Transactional campaigns
- Automated workflows
- Realistic email metrics
"""

import sys
import os
import json
import random
import uuid
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# Campaign configuration
CAMPAIGN_TYPES = [
    ('NEWSLETTER', 0.25),
    ('PROMOTIONAL', 0.30),
    ('ONBOARDING', 0.15),
    ('REENGAGEMENT', 0.10),
    ('TRANSACTIONAL', 0.10),
    ('PRODUCT_UPDATE', 0.10)
]

CAMPAIGN_STATUS = [
    ('SENT', 0.70),
    ('SCHEDULED', 0.10),
    ('DRAFT', 0.10),
    ('ARCHIVED', 0.10)
]

# Email subject lines by type
SUBJECT_TEMPLATES = {
    'NEWSLETTER': [
        "📊 {month} Bar Industry Insights & Trends",
        "Your Monthly Bar Management Digest",
        "What's New: Features, Tips & Success Stories",
        "Bar Tech Bulletin: {month} Edition"
    ],
    'PROMOTIONAL': [
        "🎉 {discount}% Off Annual Plans - This Week Only!",
        "Last Chance: Upgrade & Save ${amount}",
        "Flash Sale: Premium Features Unlocked",
        "Special Offer for {company} Inside"
    ],
    'ONBOARDING': [
        "Welcome to {platform}! Here's How to Get Started",
        "Day {day}: Unlock Your Bar's Full Potential",
        "Quick Tip: Set Up Your Inventory in 5 Minutes",
        "You're Almost There! Complete Your Setup"
    ],
    'REENGAGEMENT': [
        "We Miss You at {platform}!",
        "{name}, Your Bar Analytics Are Waiting",
        "See What's New Since You've Been Away",
        "Special Comeback Offer Just for You"
    ],
    'TRANSACTIONAL': [
        "Your {month} Invoice is Ready",
        "Payment Received - Thank You!",
        "Account Update Confirmation",
        "Password Reset Instructions"
    ],
    'PRODUCT_UPDATE': [
        "New Feature Alert: {feature} is Here!",
        "Product Update: Improvements You'll Love",
        "Enhancement: Faster Analytics Dashboard",
        "What's New in {platform} {version}"
    ]
}

# Email performance benchmarks by type
PERFORMANCE_BENCHMARKS = {
    'NEWSLETTER': {
        'open_rate': (0.18, 0.28),      # 18-28%
        'click_rate': (0.02, 0.04),     # 2-4%
        'unsubscribe_rate': (0.001, 0.003)  # 0.1-0.3%
    },
    'PROMOTIONAL': {
        'open_rate': (0.15, 0.25),      # 15-25%
        'click_rate': (0.03, 0.06),     # 3-6%
        'unsubscribe_rate': (0.002, 0.005)  # 0.2-0.5%
    },
    'ONBOARDING': {
        'open_rate': (0.40, 0.60),      # 40-60%
        'click_rate': (0.10, 0.20),     # 10-20%
        'unsubscribe_rate': (0.001, 0.002)  # 0.1-0.2%
    },
    'REENGAGEMENT': {
        'open_rate': (0.12, 0.20),      # 12-20%
        'click_rate': (0.02, 0.05),     # 2-5%
        'unsubscribe_rate': (0.005, 0.010)  # 0.5-1%
    },
    'TRANSACTIONAL': {
        'open_rate': (0.60, 0.80),      # 60-80%
        'click_rate': (0.15, 0.25),     # 15-25%
        'unsubscribe_rate': (0.0001, 0.001)  # 0.01-0.1%
    },
    'PRODUCT_UPDATE': {
        'open_rate': (0.25, 0.35),      # 25-35%
        'click_rate': (0.05, 0.10),     # 5-10%
        'unsubscribe_rate': (0.001, 0.003)  # 0.1-0.3%
    }
}

def generate_iterable_campaigns():
    """Generate Iterable email campaigns"""
    campaigns = []
    
    # Calculate number of campaigns based on environment
    # Roughly 3 campaigns per 100 accounts for realistic email marketing ratio
    num_campaigns = max(300, (current_env.accounts // 100) * 3)
    
    print(f"Generating {num_campaigns:,} Iterable email campaigns...")
    
    # Time range for campaigns (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    for i in range(num_campaigns):
        campaign_id = f"iter_camp_{uuid.uuid4().hex[:12]}"
        
        # Campaign send date
        send_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        
        # Determine campaign type and status
        campaign_type = random.choices(
            [t[0] for t in CAMPAIGN_TYPES],
            [t[1] for t in CAMPAIGN_TYPES]
        )[0]
        
        # Status based on send date
        if send_date < datetime.now() - timedelta(days=30):
            status = random.choices(['SENT', 'ARCHIVED'], [0.7, 0.3])[0]
        elif send_date > datetime.now():
            status = random.choices(['SCHEDULED', 'DRAFT'], [0.6, 0.4])[0]
        else:
            status = 'SENT'
        
        # List size and targeting
        if campaign_type == 'NEWSLETTER':
            list_size = random.randint(5000, 50000)  # Broad audience
            segment = 'All Active Users'
        elif campaign_type == 'PROMOTIONAL':
            list_size = random.randint(2000, 20000)  # Targeted segments
            segment = random.choice(['Pro Plan Users', 'Trial Users', 'Inactive 30+ Days', 'High Engagement'])
        elif campaign_type == 'ONBOARDING':
            list_size = random.randint(100, 1000)    # New users only
            segment = 'New Users (Last 7 Days)'
        elif campaign_type == 'REENGAGEMENT':
            list_size = random.randint(500, 5000)    # Inactive users
            segment = 'Inactive 60+ Days'
        elif campaign_type == 'TRANSACTIONAL':
            list_size = random.randint(1, 100)      # Individual sends
            segment = 'Triggered'
        else:  # PRODUCT_UPDATE
            list_size = random.randint(3000, 30000)
            segment = 'All Users'
        
        # Generate subject line
        month = send_date.strftime('%B')
        subject_template = random.choice(SUBJECT_TEMPLATES[campaign_type])
        subject_line = subject_template.format(
            month=month,
            discount=random.choice([10, 15, 20, 25]),
            amount=random.choice([50, 100, 200]),
            company='Bar Solutions Inc',
            platform='BarManager Pro',
            day=random.randint(1, 7),
            name=fake.first_name(),
            feature=random.choice(['Smart Inventory', 'Analytics 2.0', 'Mobile App']),
            version=f"{random.randint(2, 4)}.{random.randint(0, 9)}"
        )
        
        # Calculate metrics based on campaign type
        benchmarks = PERFORMANCE_BENCHMARKS[campaign_type]
        
        if status == 'SENT' or (status == 'ARCHIVED' and send_date < datetime.now()):
            # Calculate sends (some bounces)
            bounce_rate = random.uniform(0.01, 0.03)  # 1-3% bounce
            sends_successful = int(list_size * (1 - bounce_rate))
            
            # Opens
            open_rate = random.uniform(*benchmarks['open_rate'])
            unique_opens = int(sends_successful * open_rate)
            total_opens = int(unique_opens * random.uniform(1.2, 1.8))  # Multiple opens
            
            # Clicks
            click_rate = random.uniform(*benchmarks['click_rate'])
            unique_clicks = int(unique_opens * click_rate / open_rate)  # Click rate is of sends, not opens
            total_clicks = int(unique_clicks * random.uniform(1.1, 1.5))
            
            # Unsubscribes
            unsubscribe_rate = random.uniform(*benchmarks['unsubscribe_rate'])
            unsubscribes = int(sends_successful * unsubscribe_rate)
            
            # Complaints (spam reports)
            complaints = int(sends_successful * random.uniform(0.0001, 0.0005))
            
            # Conversions (for promotional/onboarding)
            if campaign_type in ['PROMOTIONAL', 'ONBOARDING']:
                conversion_rate = random.uniform(0.01, 0.05)  # 1-5% of clicks
                conversions = int(unique_clicks * conversion_rate)
                revenue = conversions * random.randint(50, 500) * 100  # $50-500 per conversion
            else:
                conversions = 0
                revenue = 0
        else:
            # Not sent yet
            sends_successful = 0
            unique_opens = 0
            total_opens = 0
            unique_clicks = 0
            total_clicks = 0
            unsubscribes = 0
            complaints = 0
            conversions = 0
            revenue = 0
        
        # A/B testing flag
        is_ab_test = random.random() < 0.3  # 30% of campaigns have A/B tests
        
        # Generate labels
        labels = [campaign_type.lower(), segment.lower().replace(' ', '_')]
        if is_ab_test:
            labels.append('ab_test')
        
        campaign = {
            'id': campaign_id,
            'name': f"{campaign_type} - {segment} - {send_date.strftime('%Y-%m-%d')}",
            'campaign_type': campaign_type,
            'status': status,
            'created_at_source': send_date - timedelta(days=random.randint(1, 7)),
            'updated_at_source': send_date - timedelta(days=random.randint(0, 1)),
            'start_at': send_date if status in ['SCHEDULED', 'SENT'] else None,
            'ended_at': send_date + timedelta(hours=random.randint(1, 24)) if status == 'SENT' else None,
            'send_size': sends_successful if status == 'SENT' else list_size,
            'message_medium': 'EMAIL',
            'labels': ', '.join(labels)
        }
        
        campaigns.append(campaign)
    
    return campaigns

def insert_iterable_campaigns(campaigns):
    """Insert Iterable campaigns into the database"""
    print(f"\nInserting {len(campaigns):,} campaigns into database...")
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        inserted = db_helper.bulk_insert('iterable_campaigns', batch)
        total_inserted += inserted
        
        if (i + batch_size) % 2000 == 0:
            print(f"  Inserted {i + batch_size:,} records...")
    
    return total_inserted

def verify_iterable_campaigns():
    """Verify the inserted campaigns"""
    count = db_helper.get_row_count('iterable_campaigns')
    print(f"\n✓ Verification: {count:,} campaigns in database")
    
    # Show type distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                campaign_type as type,
                COUNT(*) as count,
                SUM(send_size) as total_sent,
                AVG(send_size) as avg_send_size
            FROM raw.iterable_campaigns
            WHERE status = 'SENT'
            GROUP BY campaign_type
            ORDER BY count DESC
        """)
        type_dist = cursor.fetchall()
        
        print("\nCampaign type distribution:")
        for row in type_dist:
            print(f"  {row['type']}: {row['count']:,} campaigns, {row['total_sent']:,} emails sent, {row['avg_send_size']:,.0f} avg send size")
        
        # Show status distribution
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as campaigns,
                SUM(send_size) as total_send_size
            FROM raw.iterable_campaigns
            GROUP BY status
            ORDER BY campaigns DESC
        """)
        status_stats = cursor.fetchall()
        
        print("\nCampaign status distribution:")
        for row in status_stats:
            print(f"  {row['status']}: {row['campaigns']:,} campaigns, {row['total_send_size']:,} total send size")

def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Iterable campaigns data')
    parser.add_argument('--force', action='store_true', 
                        help='Force regeneration without prompting')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Iterable Email Campaign Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if campaigns already exist
    existing_count = db_helper.get_row_count('iterable_campaigns')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} campaigns already exist")
        if args.force:
            print("Force flag set - truncating existing data...")
            db_helper.truncate_table('iterable_campaigns')
        else:
            response = input("Do you want to truncate and regenerate? (y/N): ")
            if response.lower() == 'y':
                db_helper.truncate_table('iterable_campaigns')
            else:
                print("Aborting...")
                return
    
    # Generate campaigns
    campaigns = generate_iterable_campaigns()
    
    # Insert into database
    inserted = insert_iterable_campaigns(campaigns)
    
    # Verify
    verify_iterable_campaigns()
    
    print(f"\n✅ Successfully generated {inserted:,} Iterable email campaigns!")

if __name__ == "__main__":
    main()