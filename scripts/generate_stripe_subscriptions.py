#!/usr/bin/env python3
"""
Generate synthetic Stripe subscriptions data for the bar management SaaS platform.

This module creates Stripe subscription records with:
- Matching app subscriptions from raw.app_database_subscriptions
- Proper billing periods and status transitions
- Trial period handling
- Correct price mapping based on plan tier
"""

import sys
import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

def load_app_subscriptions():
    """Load generated app subscriptions from JSON file"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_subscriptions.json'
    )
    
    with open(mapping_file, 'r') as f:
        subscriptions = json.load(f)
    
    # Convert ISO strings back to datetime
    for sub in subscriptions:
        sub['start_date'] = datetime.fromisoformat(sub['start_date'])
        if sub['end_date']:
            sub['end_date'] = datetime.fromisoformat(sub['end_date'])
        if sub['canceled_at']:
            sub['canceled_at'] = datetime.fromisoformat(sub['canceled_at'])
        sub['created_at'] = datetime.fromisoformat(sub['created_at'])
        sub['updated_at'] = datetime.fromisoformat(sub['updated_at'])
    
    return subscriptions

def load_stripe_customers():
    """Load Stripe customers from database to get customer IDs"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT id as stripe_customer_id, metadata
            FROM raw.stripe_customers
        """)
        customers = cursor.fetchall()
    
    # Create mapping from account_id to stripe_customer_id
    customer_map = {}
    for customer in customers:
        # metadata might already be a dict if JSONB is auto-parsed
        if isinstance(customer['metadata'], str):
            metadata = json.loads(customer['metadata'])
        else:
            metadata = customer['metadata']
        account_id = int(metadata['account_id'])
        customer_map[account_id] = customer['stripe_customer_id']
    
    return customer_map

def get_price_map():
    """Get mapping of plan types to Stripe price IDs"""
    # Based on the prices we loaded:
    # Basic: $299/month, $3,238.92/year
    # Pro: $999/month, $10,789.20/year  
    # Enterprise: $2,999/month, $32,389.20/year
    
    return {
        'basic_monthly': 'price_basic_monthly_1',
        'basic_annual': 'price_basic_annual_2',
        'pro_monthly': 'price_pro_monthly_3',
        'pro_annual': 'price_pro_annual_4',
        'enterprise_monthly': 'price_enterprise_monthly_5',
        'enterprise_annual': 'price_enterprise_annual_6'
    }

def generate_stripe_subscriptions(app_subscriptions, customer_map, price_map):
    """Generate Stripe subscription records for all app subscriptions"""
    stripe_subscriptions = []
    subscription_map = {}  # Map app subscription ID to Stripe subscription ID
    
    print(f"Generating {len(app_subscriptions):,} Stripe subscriptions...")
    
    for app_sub in app_subscriptions:
        # Skip if we don't have a customer mapping
        if app_sub['account_id'] not in customer_map:
            print(f"Warning: No Stripe customer found for account {app_sub['account_id']}")
            continue
        
        # Generate Stripe subscription ID
        stripe_sub_id = f"sub_{app_sub['id']:08d}{random.randint(100000, 999999)}"
        
        # Determine billing interval (80% monthly, 20% annual)
        is_annual = random.random() < 0.2
        interval = 'year' if is_annual else 'month'
        
        # Get the correct price ID
        plan_key = f"{app_sub['plan']}_{interval}ly"
        if plan_key not in price_map:
            plan_key = f"{app_sub['plan']}_monthly"  # Fallback to monthly
        price_id = price_map[plan_key]
        
        # Calculate billing periods
        start_date = app_sub['start_date']
        
        # For active subscriptions, calculate current period
        if app_sub['status'] == 'active':
            # Calculate how many periods have passed
            now = datetime.now()
            if is_annual:
                periods_passed = (now.year - start_date.year)
                current_period_start = start_date + relativedelta(years=periods_passed)
                if current_period_start > now:
                    current_period_start = start_date + relativedelta(years=periods_passed - 1)
                current_period_end = current_period_start + relativedelta(years=1)
            else:
                months_passed = (now.year - start_date.year) * 12 + (now.month - start_date.month)
                current_period_start = start_date + relativedelta(months=months_passed)
                if current_period_start > now:
                    current_period_start = start_date + relativedelta(months=months_passed - 1)
                current_period_end = current_period_start + relativedelta(months=1)
        else:
            # For canceled subscriptions, use the end date
            if app_sub['end_date']:
                current_period_start = app_sub['end_date'] - relativedelta(months=1)
                current_period_end = app_sub['end_date']
            else:
                # Fallback for bad data
                current_period_start = start_date
                current_period_end = start_date + relativedelta(months=1)
        
        # Handle trial periods
        trial_start = None
        trial_end = None
        if app_sub['is_trial']:
            trial_start = start_date
            trial_end = start_date + timedelta(days=14)  # 14-day trial
        
        # Create items JSON
        items_data = {
            "object": "list",
            "data": [{
                "id": f"si_{stripe_sub_id[4:]}",
                "object": "subscription_item",
                "created": int(start_date.timestamp()),
                "price": {
                    "id": price_id,
                    "object": "price",
                    "recurring": {
                        "interval": interval,
                        "interval_count": 1
                    }
                },
                "quantity": 1
            }],
            "has_more": False,
            "total_count": 1
        }
        
        # Create metadata
        metadata = {
            "app_subscription_id": str(app_sub['id']),
            "account_id": str(app_sub['account_id']),
            "plan": app_sub['plan']
        }
        
        # Determine payment method (for active subscriptions)
        default_payment_method = None
        if app_sub['status'] == 'active':
            default_payment_method = f"pm_{customer_map[app_sub['account_id']][4:16]}"
        
        subscription = {
            'id': stripe_sub_id,
            'object': 'subscription',
            'application_fee_percent': None,
            'billing_cycle_anchor': start_date,
            'cancel_at': None,
            'cancel_at_period_end': False,
            'canceled_at': app_sub['canceled_at'] if app_sub['status'] == 'canceled' else None,
            'created': start_date,
            'current_period_end': current_period_end,
            'current_period_start': current_period_start,
            'customer': customer_map[app_sub['account_id']],
            'days_until_due': None,  # Charges immediately
            'default_payment_method': default_payment_method,
            'default_source': None,
            'discount': None,
            'ended_at': app_sub['end_date'] if app_sub['status'] == 'canceled' else None,
            'items': json.dumps(items_data),
            'latest_invoice': f"in_{stripe_sub_id[4:]}",  # Will be created later
            'livemode': True,
            'metadata': json.dumps(metadata),
            'next_pending_invoice_item_invoice': None,
            'pending_invoice_item_interval': None,
            'pending_setup_intent': None,
            'pending_update': None,
            'schedule': None,
            'start_date': start_date,
            'status': app_sub['status'],
            'trial_end': trial_end,
            'trial_start': trial_start,
            'created_at': app_sub['created_at']
        }
        
        stripe_subscriptions.append(subscription)
        subscription_map[app_sub['id']] = stripe_sub_id
    
    return stripe_subscriptions, subscription_map

def insert_stripe_subscriptions(subscriptions):
    """Insert Stripe subscriptions into the database"""
    print(f"\nInserting {len(subscriptions):,} Stripe subscriptions into database...")
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('stripe_subscriptions', subscriptions)
    
    return inserted

def save_subscription_mapping(subscription_map):
    """Save the mapping of app subscription IDs to Stripe subscription IDs"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'stripe_subscription_mapping.json'
    )
    
    with open(mapping_file, 'w') as f:
        json.dump(subscription_map, f, indent=2)
    
    print(f"✓ Saved subscription mapping to {mapping_file}")

def verify_stripe_subscriptions():
    """Verify the inserted Stripe subscriptions"""
    count = db_helper.get_row_count('stripe_subscriptions')
    print(f"\n✓ Verification: {count:,} Stripe subscriptions in database")
    
    # Show status distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM raw.stripe_subscriptions
            GROUP BY status
            ORDER BY count DESC
        """)
        status_dist = cursor.fetchall()
        
        print("\nSubscription status distribution:")
        for row in status_dist:
            print(f"  {row['status']}: {row['count']:,}")
        
        # Show sample subscriptions
        cursor.execute("""
            SELECT id, customer, status, 
                   current_period_start, current_period_end,
                   (metadata->>'plan') as plan
            FROM raw.stripe_subscriptions
            ORDER BY created DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample Stripe subscriptions:")
        for sub in samples:
            print(f"  {sub['id']} - {sub['plan']} - {sub['status']} - Period: {sub['current_period_start'].date()} to {sub['current_period_end'].date()}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Subscription Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if Stripe subscriptions already exist
    existing_count = db_helper.get_row_count('stripe_subscriptions')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} Stripe subscriptions already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_subscriptions')
        else:
            print("Aborting...")
            return
    
    # Load app subscriptions
    app_subscriptions = load_app_subscriptions()
    print(f"\n✓ Loaded {len(app_subscriptions):,} app subscriptions")
    
    # Load Stripe customers
    customer_map = load_stripe_customers()
    print(f"✓ Loaded {len(customer_map):,} Stripe customer mappings")
    
    # Get price mapping
    price_map = get_price_map()
    
    # Generate Stripe subscriptions
    stripe_subscriptions, subscription_map = generate_stripe_subscriptions(
        app_subscriptions, customer_map, price_map
    )
    
    # Insert into database
    inserted = insert_stripe_subscriptions(stripe_subscriptions)
    
    # Save mapping for future use
    save_subscription_mapping(subscription_map)
    
    # Verify
    verify_stripe_subscriptions()
    
    print(f"\n✅ Successfully generated {inserted:,} Stripe subscriptions!")

if __name__ == "__main__":
    main()