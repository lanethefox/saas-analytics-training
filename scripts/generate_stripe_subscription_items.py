#!/usr/bin/env python3
"""
Generate synthetic Stripe subscription items data for the bar management SaaS platform.

This module creates Stripe subscription item records with:
- Line items for each subscription
- Multiple items for add-ons (10% of subscriptions have add-ons)
- Quantity variations based on account size
"""

import sys
import os
import json
from datetime import datetime
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

def load_stripe_subscriptions():
    """Load Stripe subscriptions from database"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT id, created, metadata, items
            FROM raw.stripe_subscriptions
            ORDER BY created
        """)
        subscriptions = cursor.fetchall()
    
    return subscriptions

def load_stripe_prices():
    """Load Stripe prices to understand our pricing structure"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT id, nickname, unit_amount, recurring_interval
            FROM raw.stripe_prices
            ORDER BY unit_amount
        """)
        prices = cursor.fetchall()
    
    return prices

def create_addon_items():
    """Create add-on items that can be added to subscriptions"""
    # Define some common add-ons for a bar management system
    addons = [
        {
            'id': 'price_addon_extra_locations',
            'name': 'Extra Locations',
            'unit_amount': 4900,  # $49 per location
            'description': 'Additional location support'
        },
        {
            'id': 'price_addon_advanced_analytics',
            'name': 'Advanced Analytics',
            'unit_amount': 9900,  # $99 flat
            'description': 'Advanced reporting and analytics'
        },
        {
            'id': 'price_addon_priority_support',
            'name': 'Priority Support',
            'unit_amount': 19900,  # $199 flat
            'description': '24/7 priority support'
        },
        {
            'id': 'price_addon_extra_devices',
            'name': 'Extra Devices',
            'unit_amount': 2900,  # $29 per device
            'description': 'Additional IoT device support'
        }
    ]
    return addons

def generate_subscription_items(subscriptions, prices, addons):
    """Generate subscription item records for all subscriptions"""
    subscription_items = []
    item_counter = 0
    
    print(f"Generating subscription items for {len(subscriptions):,} subscriptions...")
    
    # Create a price lookup map
    price_map = {price['id']: price for price in prices}
    
    for sub in subscriptions:
        # Parse the subscription's existing items to get the price
        items_data = sub['items'] if isinstance(sub['items'], dict) else json.loads(sub['items'])
        
        # Get metadata
        metadata = sub['metadata'] if isinstance(sub['metadata'], dict) else json.loads(sub['metadata'])
        plan_type = metadata.get('plan', 'basic')
        
        # Main subscription item (already referenced in the subscription)
        for item in items_data.get('data', []):
            item_counter += 1
            subscription_item = {
                'id': item['id'],  # Use the ID already in the subscription
                'object': 'subscription_item',
                'billing_thresholds': None,
                'created': sub['created'],
                'metadata': json.dumps({
                    'type': 'base_plan',
                    'plan': plan_type
                }),
                'price': json.dumps(item['price']),
                'quantity': item.get('quantity', 1),
                'subscription': sub['id'],
                'tax_rates': json.dumps([]),
                'created_at': sub['created']
            }
            subscription_items.append(subscription_item)
        
        # Add add-ons for some subscriptions (more likely for higher tiers)
        addon_probability = {
            'basic': 0.05,      # 5% of basic plans have add-ons
            'pro': 0.15,        # 15% of pro plans have add-ons
            'enterprise': 0.30  # 30% of enterprise plans have add-ons
        }
        
        if random.random() < addon_probability.get(plan_type, 0.05):
            # Add 1-2 add-ons
            num_addons = random.randint(1, 2)
            selected_addons = random.sample(addons, num_addons)
            
            for addon in selected_addons:
                item_counter += 1
                item_id = f"si_{sub['id'][4:]}_{item_counter:04d}"
                
                # Determine quantity (for location/device based add-ons)
                if 'location' in addon['name'].lower():
                    quantity = random.randint(1, 5)  # 1-5 extra locations
                elif 'device' in addon['name'].lower():
                    quantity = random.randint(2, 10)  # 2-10 extra devices
                else:
                    quantity = 1  # Flat rate add-ons
                
                addon_price_data = {
                    'id': addon['id'],
                    'object': 'price',
                    'unit_amount': addon['unit_amount'],
                    'recurring': {
                        'interval': 'month',
                        'interval_count': 1
                    }
                }
                
                subscription_item = {
                    'id': item_id,
                    'object': 'subscription_item',
                    'billing_thresholds': None,
                    'created': sub['created'],
                    'metadata': json.dumps({
                        'type': 'addon',
                        'addon_name': addon['name'],
                        'description': addon['description']
                    }),
                    'price': json.dumps(addon_price_data),
                    'quantity': quantity,
                    'subscription': sub['id'],
                    'tax_rates': json.dumps([]),
                    'created_at': sub['created']
                }
                subscription_items.append(subscription_item)
    
    return subscription_items

def insert_subscription_items(items):
    """Insert subscription items into the database"""
    print(f"\nInserting {len(items):,} subscription items into database...")
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('stripe_subscription_items', items)
    
    return inserted

def verify_subscription_items():
    """Verify the inserted subscription items"""
    count = db_helper.get_row_count('stripe_subscription_items')
    print(f"\n✓ Verification: {count:,} subscription items in database")
    
    # Show distribution by type
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Count items per subscription
        cursor.execute("""
            SELECT subscription, COUNT(*) as item_count
            FROM raw.stripe_subscription_items
            GROUP BY subscription
            ORDER BY item_count DESC
            LIMIT 10
        """)
        items_per_sub = cursor.fetchall()
        
        print("\nTop subscriptions by item count:")
        for row in items_per_sub:
            print(f"  {row['subscription']}: {row['item_count']} items")
        
        # Show subscriptions with add-ons
        cursor.execute("""
            SELECT COUNT(DISTINCT subscription) as subs_with_addons
            FROM raw.stripe_subscription_items
            WHERE metadata->>'type' = 'addon'
        """)
        addons_count = cursor.fetchone()
        
        print(f"\nSubscriptions with add-ons: {addons_count['subs_with_addons']:,}")
        
        # Show sample items
        cursor.execute("""
            SELECT id, subscription, quantity,
                   metadata->>'type' as item_type,
                   metadata->>'addon_name' as addon_name
            FROM raw.stripe_subscription_items
            WHERE metadata->>'type' = 'addon'
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        if samples:
            print("\nSample add-on items:")
            for item in samples:
                print(f"  {item['id']} - {item['addon_name']} (qty: {item['quantity']})")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Subscription Items Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if subscription items already exist
    existing_count = db_helper.get_row_count('stripe_subscription_items')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} subscription items already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_subscription_items')
        else:
            print("Aborting...")
            return
    
    # Load stripe subscriptions
    subscriptions = load_stripe_subscriptions()
    print(f"\n✓ Loaded {len(subscriptions):,} Stripe subscriptions")
    
    # Load stripe prices
    prices = load_stripe_prices()
    print(f"✓ Loaded {len(prices):,} Stripe prices")
    
    # Create add-on definitions
    addons = create_addon_items()
    print(f"✓ Created {len(addons):,} add-on definitions")
    
    # Generate subscription items
    subscription_items = generate_subscription_items(subscriptions, prices, addons)
    
    # Insert into database
    inserted = insert_subscription_items(subscription_items)
    
    # Verify
    verify_subscription_items()
    
    print(f"\n✅ Successfully generated {inserted:,} subscription items!")

if __name__ == "__main__":
    main()