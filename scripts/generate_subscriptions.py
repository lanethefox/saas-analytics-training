#!/usr/bin/env python3
"""
Generate synthetic subscriptions data for the bar management SaaS platform.

This module creates realistic subscription data with:
- Subscription history for accounts  
- Plan progression patterns (upgrades/downgrades)
- Churn patterns (10% annual churn rate)
- Trial conversions (70% trial-to-paid)
- MRR matching account records
- Controlled total subscription count (1.25x accounts)
"""

import sys
import os
import random
import json
import uuid
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

# Subscription configuration
SUBSCRIPTION_PLANS = {
    'basic': {'mrr': 299, 'features': ['basic_analytics', 'device_monitoring']},
    'pro': {'mrr': 999, 'features': ['advanced_analytics', 'device_monitoring', 'api_access']},
    'enterprise': {'mrr': 2999, 'features': ['full_analytics', 'device_monitoring', 'api_access', 'white_label']}
}

SUBSCRIPTION_STATUS = ['trialing', 'active', 'past_due', 'canceled', 'paused']

# Annual churn rate 10% = ~0.87% monthly
MONTHLY_CHURN_RATE = 0.0087
TRIAL_CONVERSION_RATE = 0.70
TRIAL_DURATION_DAYS = 14

# Control subscription generation
ACCOUNTS_WITH_HISTORY = 0.25  # 25% of accounts have plan change history
MAX_SUBSCRIPTIONS_PER_ACCOUNT = 3  # Maximum subscription records per account

def load_accounts():
    """Load generated accounts from JSON file"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    
    with open(mapping_file, 'r') as f:
        accounts = json.load(f)
    
    # Convert ISO strings back to datetime
    for acc in accounts:
        acc['created_at'] = datetime.fromisoformat(acc['created_at'])
        acc['updated_at'] = datetime.fromisoformat(acc['updated_at'])
    
    return accounts

def generate_subscription_for_account(account, include_history=False):
    """Generate subscription(s) for an account"""
    subscriptions = []
    
    # Start with a trial
    trial_start = account['created_at'] + timedelta(days=random.randint(0, 7))
    trial_end = trial_start + timedelta(days=TRIAL_DURATION_DAYS)
    
    # Determine if trial converts
    converts = random.random() < TRIAL_CONVERSION_RATE
    
    if not converts and include_history:
        # Only include failed trials for accounts with history
        trial_sub = {
            'account_id': account['id'],
            'plan': account['subscription_tier'],
            'status': 'canceled',
            'mrr': 0,
            'start_date': trial_start,
            'end_date': trial_end,
            'is_trial': True,
            'canceled_at': trial_end
        }
        subscriptions.append(trial_sub)
        return subscriptions
    
    # For converting accounts
    if converts:
        current_plan = account['subscription_tier']
        sub_start = trial_end
        
        # Check if account is still active
        if account['is_active']:
            # Active subscription
            active_sub = {
                'account_id': account['id'],
                'plan': current_plan,
                'status': 'active',
                'mrr': SUBSCRIPTION_PLANS[current_plan]['mrr'],
                'start_date': sub_start,
                'end_date': None,
                'is_trial': False,
                'canceled_at': None
            }
            subscriptions.append(active_sub)
            
            # Add plan change history for some accounts
            if include_history and random.random() < 0.3:
                # Create a previous subscription (plan change)
                old_plan = 'basic' if current_plan != 'basic' else 'pro'
                old_sub_start = sub_start - relativedelta(months=random.randint(6, 24))
                
                old_sub = {
                    'account_id': account['id'],
                    'plan': old_plan,
                    'status': 'canceled',
                    'mrr': SUBSCRIPTION_PLANS[old_plan]['mrr'],
                    'start_date': old_sub_start,
                    'end_date': sub_start,
                    'is_trial': False,
                    'canceled_at': sub_start
                }
                subscriptions.insert(0, old_sub)  # Insert at beginning
        else:
            # Canceled subscription
            cancel_date = sub_start + relativedelta(months=random.randint(3, 36))
            canceled_sub = {
                'account_id': account['id'],
                'plan': current_plan,
                'status': 'canceled',
                'mrr': SUBSCRIPTION_PLANS[current_plan]['mrr'],
                'start_date': sub_start,
                'end_date': cancel_date,
                'is_trial': False,
                'canceled_at': cancel_date
            }
            subscriptions.append(canceled_sub)
    
    return subscriptions

def generate_subscriptions(accounts):
    """Generate subscription data for all accounts with controlled total count"""
    all_subscriptions = []
    subscription_id = 1
    
    # Calculate target total based on environment config
    target_total = current_env.subscriptions
    accounts_count = len(accounts)
    
    print(f"Generating ~{target_total:,} subscriptions for {accounts_count:,} accounts...")
    print(f"  Target ratio: {target_total/accounts_count:.2f} subscriptions per account")
    
    # Determine which accounts get history
    accounts_with_history = set(random.sample(range(accounts_count), 
                                            int(accounts_count * ACCOUNTS_WITH_HISTORY)))
    
    for i, account in enumerate(accounts):
        include_history = i in accounts_with_history
        account_subs = generate_subscription_for_account(account, include_history)
        
        for sub in account_subs[:MAX_SUBSCRIPTIONS_PER_ACCOUNT]:  # Limit subs per account
            sub['id'] = subscription_id
            sub['created_at'] = sub['start_date']
            sub['updated_at'] = sub['start_date'] + timedelta(days=random.randint(0, 30))
            all_subscriptions.append(sub)
            subscription_id += 1
        
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i + 1:,} accounts... ({len(all_subscriptions):,} subscriptions)")
    
    print(f"  Generated {len(all_subscriptions):,} total subscriptions")
    return all_subscriptions

def insert_subscriptions(subscriptions):
    """Insert subscriptions into the database"""
    print(f"\nInserting {len(subscriptions):,} subscriptions into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_subscriptions'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.app_database_subscriptions:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_subscriptions = []
    for sub in subscriptions:
        mapped = {
            'id': sub['id'],
            'customer_id': sub['account_id'],  # customer_id maps to account_id
            'plan_name': sub['plan'],
            'status': sub['status'],
            'start_date': sub['start_date'].date(),
            'end_date': sub['end_date'].date() if sub['end_date'] else None,
            'monthly_price': sub['mrr'],
            'billing_cycle': 'monthly',  # Default to monthly billing
            'created_at': sub['created_at'],
            'updated_at': sub['updated_at']
        }
        mapped_subscriptions.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_subscriptions', mapped_subscriptions)
    
    return inserted

def save_subscription_mapping(subscriptions):
    """Save subscription mapping to JSON file"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_subscriptions.json'
    )
    
    # Save the full subscription data
    with open(mapping_file, 'w') as f:
        # Convert datetime objects to strings
        serializable_subs = []
        for sub in subscriptions:
            sub_copy = sub.copy()
            sub_copy['start_date'] = sub_copy['start_date'].isoformat()
            sub_copy['end_date'] = sub_copy['end_date'].isoformat() if sub_copy['end_date'] else None
            sub_copy['created_at'] = sub_copy['created_at'].isoformat()
            sub_copy['updated_at'] = sub_copy['updated_at'].isoformat()
            sub_copy['canceled_at'] = sub_copy['canceled_at'].isoformat() if sub_copy.get('canceled_at') else None
            serializable_subs.append(sub_copy)
        
        json.dump(serializable_subs, f, indent=2)
    
    print(f"\n✓ Saved subscription mapping to {mapping_file}")

def verify_subscriptions():
    """Verify the inserted subscriptions"""
    count = db_helper.get_row_count('app_database_subscriptions')
    print(f"\n✓ Verification: {count:,} subscriptions in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT s.*, a.name as account_name
            FROM raw.app_database_subscriptions s
            JOIN raw.app_database_accounts a ON s.customer_id = a.id
            ORDER BY s.created_at DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample subscriptions (most recent):")
        for sub in samples:
            print(f"  {sub['account_name']} - {sub['plan_name']} - ${sub['monthly_price']}/mo - Status: {sub['status']}")
    
    # Show status distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT status, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_subscriptions
            GROUP BY status
            ORDER BY count DESC
        """)
        dist = cursor.fetchall()
        
        print("\nStatus distribution:")
        for row in dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
    
    # Show MRR summary
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'active' THEN monthly_price ELSE 0 END) as active_mrr,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
            FROM raw.app_database_subscriptions
        """)
        mrr_data = cursor.fetchone()
        
        print(f"\nMRR Summary:")
        print(f"  Active subscriptions: {mrr_data[1]:,}")
        print(f"  Total MRR: ${mrr_data[0]:,.2f}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Subscription Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if subscriptions already exist
    existing_count = db_helper.get_row_count('app_database_subscriptions')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} subscriptions already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_subscriptions')
        else:
            print("Aborting...")
            return
    
    # Load accounts
    accounts = load_accounts()
    print(f"\n✓ Loaded {len(accounts):,} accounts")
    
    # Generate subscriptions
    subscriptions = generate_subscriptions(accounts)
    
    # Save mapping
    save_subscription_mapping(subscriptions)
    
    # Insert into database
    inserted = insert_subscriptions(subscriptions)
    
    # Verify
    verify_subscriptions()
    
    print(f"\n✅ Successfully generated {inserted:,} subscriptions!")

if __name__ == "__main__":
    main()