#!/usr/bin/env python3
"""
Generate synthetic Stripe payment intents data for the bar management SaaS platform.

This module creates Stripe payment intent records with:
- Payment intents for successful charges
- Failed payment attempts
- Various payment methods (card, bank transfer)
- Proper status transitions
"""

import sys
import os
import json
import random
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Payment intent configuration
PAYMENT_METHODS = [
    ('card', 0.85),      # 85% card payments
    ('us_bank_account', 0.10),  # 10% bank transfers
    ('link', 0.05)       # 5% Link payments
]

FAILURE_REASONS = [
    'card_declined',
    'insufficient_funds', 
    'processing_error',
    'expired_card',
    'incorrect_cvc'
]

def generate_minimal_payment_intents():
    """Generate a minimal set of payment intents when no charges exist"""
    payment_intents = []
    
    # Generate 50 minimal payment intents
    for i in range(50):
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        
        # Random status distribution
        status_rand = random.random()
        if status_rand < 0.75:
            status = 'succeeded'
        elif status_rand < 0.90:
            status = 'processing'
        elif status_rand < 0.95:
            status = 'requires_payment_method'
        else:
            status = 'canceled'
        
        # Random amount (in cents)
        amount = random.choice([2900, 4900, 9900, 14900, 24900]) * 100  # Common subscription amounts
        
        payment_intent = {
            'id': f'pi_minimal_{uuid.uuid4().hex[:16]}',
            'amount': amount,
            'amount_capturable': 0,
            'amount_received': amount if status == 'succeeded' else 0,
            'capture_method': 'automatic',
            'charges': json.dumps({'data': []}),  # Empty charges array
            'confirmation_method': 'automatic',
            'created': created_at,
            'currency': 'usd',
            'customer': f'cus_{uuid.uuid4().hex[:14]}',
            'description': f'Minimal payment intent for testing',
            'invoice': None,
            'metadata': json.dumps({'source': 'minimal_generator'}),
            'payment_method': f'pm_{uuid.uuid4().hex[:16]}' if status != 'requires_payment_method' else None,
            'payment_method_types': json.dumps(['card']),
            'setup_future_usage': None,
            'shipping': None,
            'statement_descriptor': 'BARMANAGER PRO',
            'status': status,
            'created_at': created_at
        }
        
        payment_intents.append(payment_intent)
    
    return payment_intents

def load_stripe_charges():
    """Load Stripe charges to create corresponding payment intents"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                id as charge_id,
                amount,
                currency,
                customer,
                description,
                invoice,
                paid,
                payment_method,
                status,
                created,
                metadata
            FROM raw.stripe_charges
            ORDER BY created
            LIMIT %s
        """, (current_env.stripe_charges,))  # Limit to expected charge count
        charges = cursor.fetchall()
    
    return charges

def generate_payment_intent_for_charge(charge):
    """Generate a payment intent for a charge"""
    # Extract charge details
    charge_id = charge['charge_id']
    amount = charge['amount']
    is_successful = charge['paid']
    
    # Generate payment intent ID
    pi_id = f"pi_{charge_id[3:]}"  # Replace ch_ with pi_
    
    # Determine payment method type
    payment_method_type = random.choices(
        [method[0] for method in PAYMENT_METHODS],
        [method[1] for method in PAYMENT_METHODS]
    )[0]
    
    # Generate payment method ID
    pm_id = f"pm_{charge_id[3:]}"
    
    # Create timestamps
    created_at = charge['created']
    confirmed_at = created_at + timedelta(seconds=random.randint(1, 30))
    
    # Handle status and cancellation
    if is_successful:
        status = 'succeeded'
        canceled_at = None
        cancellation_reason = None
        failure_code = None
        failure_message = None
    else:
        # Some failed intents are canceled, others just fail
        if random.random() < 0.3:
            status = 'canceled'
            canceled_at = confirmed_at + timedelta(seconds=random.randint(30, 300))
            cancellation_reason = 'requested_by_customer'
            failure_code = None
            failure_message = None
        else:
            status = 'requires_payment_method'
            canceled_at = None
            cancellation_reason = None
            failure_code = random.choice(FAILURE_REASONS)
            failure_message = f"Your {payment_method_type} was declined"
    
    # Build charges array
    charges_data = [{
        "id": charge_id,
        "object": "charge",
        "amount": amount,
        "amount_captured": amount if is_successful else 0,
        "amount_refunded": 0,
        "paid": is_successful,
        "status": charge['status']
    }]
    
    # Get metadata
    if charge['metadata'] is None:
        metadata = {}
    elif isinstance(charge['metadata'], dict):
        metadata = charge['metadata']
    else:
        metadata = json.loads(charge['metadata'])
    
    payment_intent = {
        'id': pi_id,
        'object': 'payment_intent',
        'amount': amount,
        'amount_capturable': 0,
        'amount_received': amount if is_successful else 0,
        'application': None,
        'application_fee_amount': None,
        'canceled_at': canceled_at,
        'cancellation_reason': cancellation_reason,
        'capture_method': 'automatic',
        'charges': json.dumps({
            "object": "list",
            "data": charges_data,
            "has_more": False,
            "total_count": 1,
            "url": f"/v1/charges?payment_intent={pi_id}"
        }),
        'client_secret': f"{pi_id}_secret_{charge_id[3:]}",
        'confirmation_method': 'automatic',
        'created': created_at,
        'currency': charge['currency'],
        'customer': charge['customer'],
        'description': charge['description'],
        'invoice': charge['invoice'],
        'last_payment_error': json.dumps({
            "code": failure_code,
            "message": failure_message,
            "type": "card_error" if failure_code else None
        }) if failure_code else None,
        'livemode': True,
        'metadata': json.dumps(metadata),
        'next_action': None,
        'on_behalf_of': None,
        'payment_method': pm_id if is_successful else None,
        'payment_method_options': json.dumps({
            payment_method_type: {
                "request_three_d_secure": "automatic" if payment_method_type == "card" else None
            }
        }),
        'payment_method_types': json.dumps([payment_method_type]),
        'receipt_email': None,
        'review': None,
        'setup_future_usage': None,
        'shipping': None,
        'statement_descriptor': None,
        'statement_descriptor_suffix': None,
        'status': status,
        'transfer_data': None,
        'transfer_group': None
    }
    
    return payment_intent

def generate_stripe_payment_intents(charges):
    """Generate all Stripe payment intents"""
    payment_intents = []
    
    print(f"Generating payment intents for {len(charges):,} charges...")
    
    for i, charge in enumerate(charges):
        payment_intent = generate_payment_intent_for_charge(charge)
        payment_intents.append(payment_intent)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} payment intents...")
    
    return payment_intents

def insert_stripe_payment_intents(payment_intents):
    """Insert Stripe payment intents into the database"""
    print(f"\nInserting {len(payment_intents):,} payment intents into database...")
    
    # Insert in batches
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(payment_intents), batch_size):
        batch = payment_intents[i:i + batch_size]
        inserted = db_helper.bulk_insert('stripe_payment_intents', batch)
        total_inserted += inserted
        
        if (i + batch_size) % 10000 == 0:
            print(f"  Inserted {i + batch_size:,} records...")
    
    return total_inserted

def verify_stripe_payment_intents():
    """Verify the inserted payment intents"""
    count = db_helper.get_row_count('stripe_payment_intents')
    print(f"\n✓ Verification: {count:,} payment intents in database")
    
    # Show status distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.stripe_payment_intents
            GROUP BY status
            ORDER BY count DESC
        """)
        status_dist = cursor.fetchall()
        
        print("\nPayment intent status distribution:")
        for row in status_dist:
            print(f"  {row['status']}: {row['count']:,} ({row['percentage']}%)")
        
        # Show payment method distribution
        cursor.execute("""
            SELECT 
                payment_method_types,
                COUNT(*) as count
            FROM raw.stripe_payment_intents
            WHERE payment_method_types IS NOT NULL
            GROUP BY payment_method_types
            ORDER BY count DESC
            LIMIT 10
        """)
        method_dist = cursor.fetchall()
        
        print("\nPayment method types:")
        for row in method_dist:
            methods = row['payment_method_types']
            if isinstance(methods, str):
                methods = json.loads(methods)
            print(f"  {', '.join(methods)}: {row['count']:,}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Payment Intent Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check for force flag
    force_mode = '--force' in sys.argv
    
    # Check if payment intents already exist
    existing_count = db_helper.get_row_count('stripe_payment_intents')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} payment intents already exist")
        if force_mode:
            print("Force mode enabled - truncating existing data...")
            db_helper.truncate_table('stripe_payment_intents')
        else:
            response = input("Do you want to truncate and regenerate? (y/N): ")
            if response.lower() == 'y':
                db_helper.truncate_table('stripe_payment_intents')
            else:
                print("Aborting...")
                return
    
    # Load charges
    charges = load_stripe_charges()
    print(f"\n✓ Loaded {len(charges):,} Stripe charges")
    
    if not charges:
        print("⚠️  No charges found. Generating minimal payment intents for testing...")
        # Generate a minimal set of payment intents for testing
        payment_intents = generate_minimal_payment_intents()
    else:
        # Generate payment intents based on charges
        payment_intents = generate_stripe_payment_intents(charges)
    
    # Insert into database
    inserted = insert_stripe_payment_intents(payment_intents)
    
    # Verify
    verify_stripe_payment_intents()
    
    print(f"\n✅ Successfully generated {inserted:,} payment intents!")

if __name__ == "__main__":
    main()