#!/usr/bin/env python3
"""
Generate deterministic subscriptions data for the TapFlow Analytics platform.

This module creates subscriptions with:
- One active subscription per account
- Pricing tiers based on device count from configuration
- Historical subscriptions for growth patterns
- Sequential IDs within reserved range (1-200)
- Realistic churn and upgrade patterns
"""

import sys
import os
import random
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

import os

def should_truncate():
    """Check if we should auto-truncate in Docker environment"""
    if os.environ.get('DOCKER_ENV', 'false').lower() == 'true':
        return True
    if os.environ.get('PYTHONUNBUFFERED', '0') == '1':
        # Running in automated mode, always truncate
        return True
    response = input("Do you want to truncate and regenerate? (y/N): ")
    return response.lower() == 'y'

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

# Initialize Faker with seed from config
fake = Faker()

def get_subscription_tier_for_account(account, device_count):
    """Determine subscription tier based on device count"""
    tiers = config.get_subscription_tiers()
    
    # Determine tier based on device count
    if device_count <= tiers['starter']['device_limit']:
        return 'starter'
    elif device_count <= tiers['professional']['device_limit']:
        return 'professional'
    elif device_count <= tiers['business']['device_limit']:
        return 'business'
    else:
        return 'enterprise'

def get_trial_duration(account_size):
    """Get trial duration based on account size"""
    if account_size == 'enterprise':
        return 30  # Enterprise gets 30-day trials
    elif account_size == 'large':
        return 21  # Large gets 21-day trials
    else:
        return 14  # Standard 14-day trial

def calculate_account_device_count(account_id):
    """Calculate total device count for an account"""
    # Query the database directly for device count
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT d.id) as device_count
            FROM raw.app_database_locations l
            JOIN raw.app_database_devices d ON d.location_id = l.id
            WHERE l.customer_id = %s
        """, (account_id,))
        result = cursor.fetchone()
        
        if result and result['device_count'] > 0:
            return result['device_count']
        
        # If no devices found, estimate based on account type
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN employee_count > 1000 OR annual_revenue > 100000000 THEN 'enterprise'
                    WHEN employee_count > 100 OR annual_revenue > 10000000 THEN 'large'
                    WHEN employee_count > 10 OR annual_revenue > 1000000 THEN 'medium'
                    ELSE 'small'
                END as account_size
            FROM raw.app_database_accounts
            WHERE id = %s
        """, (account_id,))
        account = cursor.fetchone()
        
        if not account:
            return 10  # Default for missing accounts
            
        size = account['account_size']
        distribution = config.get_account_distribution()[size]
        
        # Estimate device count
        locations = (distribution['locations_min'] + distribution['locations_max']) // 2
        devices_per_loc = (distribution['devices_per_location_min'] + distribution['devices_per_location_max']) // 2
        return locations * devices_per_loc

def generate_subscription_history(account, current_tier, account_created):
    """Generate subscription history showing growth"""
    history = []
    growth_patterns = config.get_growth_patterns()
    
    # Determine if this account has grown
    account_age_months = (datetime.now() - account_created).days / 30
    
    if account_age_months > 12 and random.random() < 0.3:  # 30% of old accounts have upgraded
        # Create previous subscription
        if current_tier == 'enterprise':
            previous_tier = 'business'
        elif current_tier == 'business':
            previous_tier = 'professional'
        elif current_tier == 'professional':
            previous_tier = 'starter'
        else:
            previous_tier = None
        
        if previous_tier:
            # Previous subscription lasted 6-24 months
            duration_months = random.randint(6, 24)
            upgrade_date = datetime.now() - relativedelta(months=random.randint(3, 12))
            start_date = upgrade_date - relativedelta(months=duration_months)
            
            # Ensure start date is after account creation
            if start_date < account_created:
                start_date = account_created + timedelta(days=14)  # After trial
            
            history.append({
                'tier': previous_tier,
                'start_date': start_date,
                'end_date': upgrade_date,
                'status': 'upgraded',
                'reason': 'growth'
            })
    
    return history

def generate_subscriptions():
    """Generate deterministic subscription data"""
    # Load accounts directly from the database
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                id,
                name,
                created_at,
                updated_at,
                -- Determine account size based on employee count and revenue
                CASE 
                    WHEN employee_count > 1000 OR annual_revenue > 100000000 THEN 'enterprise'
                    WHEN employee_count > 100 OR annual_revenue > 10000000 THEN 'large'
                    WHEN employee_count > 10 OR annual_revenue > 1000000 THEN 'medium'
                    ELSE 'small'
                END as account_size,
                -- Determine if account is active based on status
                CASE 
                    WHEN status = 'active' THEN true
                    WHEN status = 'churned' THEN false
                    WHEN created_at > (CURRENT_DATE - INTERVAL '90 days') THEN true
                    ELSE (RANDOM() < 0.85)  -- 85% of older accounts are active
                END as is_active
            FROM raw.app_database_accounts
            ORDER BY id
        """)
        accounts = cursor.fetchall()
    
    subscriptions = []
    subscription_tiers = config.get_subscription_tiers()
    
    print(f"Generating subscriptions for {len(accounts)} accounts...")
    
    # Reset ID allocator for subscriptions
    id_allocator.current_ids['subscriptions'] = 1
    
    for account in accounts:
        # Calculate device count for this account
        device_count = calculate_account_device_count(account['id'])
        
        # Determine appropriate tier
        tier = get_subscription_tier_for_account(account, device_count)
        tier_config = subscription_tiers[tier]
        
        # Trial period
        trial_duration = get_trial_duration(account['account_size'])
        trial_start = account['created_at'] + timedelta(days=random.randint(0, 3))
        trial_end = trial_start + timedelta(days=trial_duration)
        
        # Determine subscription status
        if account.get('is_active', True):  # Default to active if not specified
            status = 'active'
            start_date = trial_end
            end_date = None
            canceled_at = None
        else:
            # Inactive accounts have canceled subscriptions
            status = 'canceled'
            start_date = trial_end
            # Subscription lasted 3-36 months
            duration_months = random.randint(3, 36)
            end_date = start_date + relativedelta(months=duration_months)
            # Ensure end date is in the past
            if end_date > datetime.now():
                end_date = datetime.now() - timedelta(days=random.randint(30, 180))
            canceled_at = end_date
        
        # Generate subscription history
        history = generate_subscription_history(account, tier, account['created_at'])
        
        # Add historical subscriptions
        for hist in history:
            hist_id = id_allocator.get_next_id('subscriptions')
            hist_tier_config = subscription_tiers[hist['tier']]
            
            subscription = {
                'id': hist_id,
                'customer_id': account['id'],
                'plan_name': hist['tier'],
                'status': 'canceled',
                'start_date': hist['start_date'],
                'end_date': hist['end_date'],
                'monthly_price': hist_tier_config['monthly_price'],
                'billing_cycle': 'monthly',
                'features': json.dumps(hist_tier_config['features']),
                'device_limit': hist_tier_config['device_limit'],
                'created_at': hist['start_date'],
                'updated_at': hist['end_date'],
                'canceled_at': hist['end_date'],
                'cancellation_reason': hist['reason']
            }
            subscriptions.append(subscription)
        
        # Add current/final subscription
        sub_id = id_allocator.get_next_id('subscriptions')
        
        subscription = {
            'id': sub_id,
            'customer_id': account['id'],
            'plan_name': tier,
            'status': status,
            'start_date': start_date,
            'end_date': end_date,
            'monthly_price': tier_config['monthly_price'],
            'billing_cycle': 'monthly',
            'features': json.dumps(tier_config['features']),
            'device_limit': tier_config['device_limit'] if tier_config['device_limit'] else 999999,  # Unlimited
            'created_at': start_date,
            'updated_at': start_date + timedelta(days=random.randint(0, 30)),
            'canceled_at': canceled_at,
            'cancellation_reason': 'customer_request' if canceled_at else None,
            'trial_start': trial_start,
            'trial_end': trial_end,
            'device_count': device_count  # Store for reference
        }
        
        subscriptions.append(subscription)
    
    print(f"  Generated {len(subscriptions)} total subscriptions")
    print(f"  Active subscriptions: {len([s for s in subscriptions if s['status'] == 'active'])}")
    
    return subscriptions

def insert_subscriptions(subscriptions):
    """Insert subscriptions into the database"""
    print(f"\nInserting {len(subscriptions)} subscriptions into database...")
    
    # Map our generated data to actual table columns
    mapped_subscriptions = []
    for sub in subscriptions:
        mapped = {
            'id': sub['id'],
            'customer_id': sub['customer_id'],
            'plan_name': sub['plan_name'],
            'status': sub['status'],
            'start_date': sub['start_date'].date(),
            'end_date': sub['end_date'].date() if sub['end_date'] else None,
            'monthly_price': sub['monthly_price'],
            'billing_cycle': sub['billing_cycle'],
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
    serializable_subs = []
    for sub in subscriptions:
        sub_copy = sub.copy()
        sub_copy['start_date'] = sub_copy['start_date'].isoformat()
        sub_copy['end_date'] = sub_copy['end_date'].isoformat() if sub_copy['end_date'] else None
        sub_copy['created_at'] = sub_copy['created_at'].isoformat()
        sub_copy['updated_at'] = sub_copy['updated_at'].isoformat()
        sub_copy['canceled_at'] = sub_copy['canceled_at'].isoformat() if sub_copy.get('canceled_at') else None
        sub_copy['trial_start'] = sub_copy['trial_start'].isoformat() if sub_copy.get('trial_start') else None
        sub_copy['trial_end'] = sub_copy['trial_end'].isoformat() if sub_copy.get('trial_end') else None
        # Features already JSON string
        serializable_subs.append(sub_copy)
    
    with open(mapping_file, 'w') as f:
        json.dump(serializable_subs, f, indent=2)
    
    print(f"\n✓ Saved subscription mapping to {mapping_file}")

def verify_subscriptions():
    """Verify the inserted subscriptions"""
    count = db_helper.get_row_count('app_database_subscriptions')
    print(f"\n✓ Verification: {count} subscriptions in database")
    
    # Show distribution statistics
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_subscriptions
            GROUP BY status
            ORDER BY count DESC
        """)
        status_dist = cursor.fetchall()
        
        print("\nStatus distribution:")
        for row in status_dist:
            print(f"  {row['status']}: {row['count']} ({row['percentage']}%)")
        
        # Plan distribution
        cursor.execute("""
            SELECT plan_name, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_subscriptions
            GROUP BY plan_name
            ORDER BY count DESC
        """)
        plan_dist = cursor.fetchall()
        
        print("\nPlan distribution:")
        for row in plan_dist:
            print(f"  {row['plan_name']}: {row['count']} ({row['percentage']}%)")
        
        # MRR calculation
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'active' THEN monthly_price ELSE 0 END) as active_mrr,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                AVG(CASE WHEN status = 'active' THEN monthly_price END) as avg_price
            FROM raw.app_database_subscriptions
        """)
        mrr_data = cursor.fetchone()
        
        print(f"\nMRR Summary:")
        print(f"  Active subscriptions: {mrr_data['active_count']}")
        print(f"  Total MRR: ${mrr_data['active_mrr']:,.2f}")
        print(f"  Average price: ${mrr_data['avg_price']:,.2f}")
        
        # Compare with account MRR
        cursor.execute("""
            SELECT COUNT(*) as active_accounts
            FROM raw.app_database_accounts
            WHERE id IN (
                SELECT DISTINCT customer_id 
                FROM raw.app_database_subscriptions 
                WHERE status = 'active'
            )
        """)
        active_accounts = cursor.fetchone()['active_accounts']
        
        print(f"\n✓ Active accounts with subscriptions: {active_accounts}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Subscription Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if subscriptions already exist
    existing_count = db_helper.get_row_count('app_database_subscriptions')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} subscriptions already exist")
        if should_truncate():
            db_helper.truncate_table('app_database_subscriptions')
        else:
            print("Aborting...")
            return
    
    # Generate subscriptions
    subscriptions = generate_subscriptions()
    
    # Save mapping
    save_subscription_mapping(subscriptions)
    
    # Insert into database
    inserted = insert_subscriptions(subscriptions)
    
    # Verify
    verify_subscriptions()
    
    print(f"\n✅ Successfully generated {inserted} subscriptions!")

if __name__ == "__main__":
    main()