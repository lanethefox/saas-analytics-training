#!/usr/bin/env python3
"""
Generate synthetic Stripe prices data for the bar management SaaS platform.

This module creates pricing tiers for all plans:
- Basic, Pro, Enterprise tiers
- Monthly and annual variants
- Proper unit amounts in cents
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Pricing configuration (in cents)
PRICING_TIERS = [
    {
        'tier': 'basic',
        'monthly_price': 29900,  # $299.00
        'annual_price': 323892,  # $269.91/month when paid annually (10% discount)
        'features': ['basic_analytics', 'device_monitoring', 'email_support']
    },
    {
        'tier': 'pro',
        'monthly_price': 99900,  # $999.00
        'annual_price': 1078920,  # $899.10/month when paid annually (10% discount)
        'features': ['advanced_analytics', 'device_monitoring', 'api_access', 'priority_support']
    },
    {
        'tier': 'enterprise',
        'monthly_price': 299900,  # $2999.00
        'annual_price': 3238920,  # $2699.10/month when paid annually (10% discount)
        'features': ['full_analytics', 'device_monitoring', 'api_access', 'white_label', 'dedicated_support']
    }
]

def generate_stripe_prices():
    """Generate Stripe price records for all tiers"""
    stripe_prices = []
    price_id = 1
    
    print(f"Generating {len(PRICING_TIERS) * 2} Stripe prices...")
    
    for tier_config in PRICING_TIERS:
        tier = tier_config['tier']
        
        # Monthly price
        monthly_price_id = f"price_{tier}_monthly_{price_id}"
        monthly_price = {
            'id': monthly_price_id,
            'product_id': f"prod_{tier}",
            'currency': 'usd',
            'unit_amount': tier_config['monthly_price'],
            'interval': 'month',
            'interval_count': 1,
            'nickname': f"{tier.capitalize()} Monthly",
            'active': True,
            'billing_scheme': 'per_unit',
            'metadata': json.dumps({
                'tier': tier,
                'billing_cycle': 'monthly',
                'features': tier_config['features']
            }),
            'created_at': datetime.now() - timedelta(days=365)  # Created a year ago
        }
        stripe_prices.append(monthly_price)
        price_id += 1
        
        # Annual price
        annual_price_id = f"price_{tier}_annual_{price_id}"
        annual_price = {
            'id': annual_price_id,
            'product_id': f"prod_{tier}",
            'currency': 'usd',
            'unit_amount': tier_config['annual_price'],
            'interval': 'year',
            'interval_count': 1,
            'nickname': f"{tier.capitalize()} Annual",
            'active': True,
            'billing_scheme': 'per_unit',
            'metadata': json.dumps({
                'tier': tier,
                'billing_cycle': 'annual',
                'features': tier_config['features'],
                'discount_percentage': 10
            }),
            'created_at': datetime.now() - timedelta(days=365)
        }
        stripe_prices.append(annual_price)
        price_id += 1
    
    return stripe_prices
def insert_stripe_prices(prices):
    """Insert Stripe prices into the database"""
    print(f"\nInserting {len(prices):,} Stripe prices into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'stripe_prices'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.stripe_prices:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_prices = []
    for price in prices:
        mapped = {
            'id': price['id'],
            'object': 'price',
            'active': price['active'],
            'currency': price['currency'],
            'unit_amount': price['unit_amount'],
            'type': 'recurring',
            'recurring_interval': price['interval'],
            'recurring_interval_count': price['interval_count'],
            'nickname': price['nickname'],
            'created': price['created_at'],
            'created_at': price['created_at']
        }
        mapped_prices.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('stripe_prices', mapped_prices)
    
    return inserted

def verify_stripe_prices():
    """Verify the inserted Stripe prices"""
    count = db_helper.get_row_count('stripe_prices')
    print(f"\n✓ Verification: {count:,} Stripe prices in database")
    
    # Show all prices
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT * FROM raw.stripe_prices
            ORDER BY nickname, unit_amount
        """)
        prices = cursor.fetchall()
        
        print("\nStripe pricing tiers:")
        for price in prices:
            amount_display = f"${price['unit_amount'] / 100:,.2f}"
            interval = price['recurring_interval']
            print(f"  {price['nickname']}: {amount_display}/{interval} - {price['id']}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Price Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if Stripe prices already exist
    existing_count = db_helper.get_row_count('stripe_prices')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} Stripe prices already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_prices')
        else:
            print("Aborting...")
            return
    
    # Generate Stripe prices
    stripe_prices = generate_stripe_prices()
    
    # Insert into database
    inserted = insert_stripe_prices(stripe_prices)
    
    # Verify
    verify_stripe_prices()
    
    print(f"\n✅ Successfully generated {inserted:,} Stripe prices!")

if __name__ == "__main__":
    main()
