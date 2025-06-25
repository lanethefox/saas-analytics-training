#!/usr/bin/env python3
"""
Generate synthetic Stripe charges data for the bar management SaaS platform.

This module creates Stripe charge records with:
- Successful payments for paid invoices
- Payment method distributions (70% card, 30% bank)
- Geographic patterns based on account locations
- Realistic payment processing details
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random
import string

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

def load_paid_invoices():
    """Load paid invoices that need charges"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                i.id as invoice_id,
                i.charge as charge_id,
                i.customer,
                i.amount_paid,
                i.currency,
                i.created,
                i.metadata,
                i.subscription,
                i.payment_intent,
                i.number
            FROM raw.stripe_invoices i
            WHERE i.paid = true
            ORDER BY i.created
        """)
        invoices = cursor.fetchall()
    
    return invoices

def load_customer_details():
    """Load customer details for billing information"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                c.id as customer_id,
                c.email,
                c.name,
                c.metadata
            FROM raw.stripe_customers c
        """)
        customers = cursor.fetchall()
    
    # Create lookup map
    customer_map = {c['customer_id']: c for c in customers}
    return customer_map

def generate_payment_method_details(payment_type='card'):
    """Generate realistic payment method details"""
    if payment_type == 'card':
        # Card brands distribution
        brands = ['visa', 'mastercard', 'amex', 'discover']
        brand_weights = [0.45, 0.35, 0.15, 0.05]
        brand = random.choices(brands, weights=brand_weights)[0]
        
        # Generate card details
        return {
            "card": {
                "brand": brand,
                "exp_month": random.randint(1, 12),
                "exp_year": random.randint(2025, 2030),
                "last4": ''.join(random.choices(string.digits, k=4)),
                "network": brand,
                "three_d_secure": None,
                "wallet": None,
                "country": "US",
                "funding": random.choice(["credit", "debit"]),
                "fingerprint": ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            },
            "type": "card"
        }
    else:  # bank_account
        return {
            "bank_account": {
                "bank_name": random.choice(["JPMORGAN CHASE", "BANK OF AMERICA", "WELLS FARGO", "CITIBANK"]),
                "country": "US",
                "currency": "usd",
                "last4": ''.join(random.choices(string.digits, k=4)),
                "routing_number": ''.join(random.choices(string.digits, k=9)),
                "status": "verified"
            },
            "type": "bank_account"
        }

def generate_outcome():
    """Generate payment outcome details"""
    return {
        "network_status": "approved_by_network",
        "reason": None,
        "risk_level": "normal",
        "risk_score": random.randint(10, 40),
        "seller_message": "Payment complete.",
        "type": "authorized"
    }

def generate_billing_details(customer_info):
    """Generate billing details from customer info"""
    # Sample US addresses
    addresses = [
        {"city": "New York", "state": "NY", "postal_code": "10001"},
        {"city": "Los Angeles", "state": "CA", "postal_code": "90001"},
        {"city": "Chicago", "state": "IL", "postal_code": "60601"},
        {"city": "Houston", "state": "TX", "postal_code": "77001"},
        {"city": "Phoenix", "state": "AZ", "postal_code": "85001"},
        {"city": "Philadelphia", "state": "PA", "postal_code": "19101"},
        {"city": "San Antonio", "state": "TX", "postal_code": "78201"},
        {"city": "San Diego", "state": "CA", "postal_code": "92101"},
        {"city": "Dallas", "state": "TX", "postal_code": "75201"},
        {"city": "San Jose", "state": "CA", "postal_code": "95101"}
    ]
    
    address = random.choice(addresses)
    
    return {
        "address": {
            "city": address["city"],
            "country": "US",
            "line1": f"{random.randint(100, 9999)} Main Street",
            "line2": None,
            "postal_code": address["postal_code"],
            "state": address["state"]
        },
        "email": customer_info.get('email'),
        "name": customer_info.get('name'),
        "phone": None
    }

def generate_stripe_charges(invoices, customer_map):
    """Generate charge records for all paid invoices"""
    charges = []
    
    print(f"Generating charges for {len(invoices):,} paid invoices...")
    
    for invoice in invoices:
        # Get customer info
        customer_info = customer_map.get(invoice['customer'], {})
        
        # Use the charge ID from the invoice
        charge_id = invoice['charge_id'] if invoice['charge_id'] else f"ch_{invoice['invoice_id'][3:]}"
        
        # Payment method type (70% card, 30% bank)
        payment_type = 'card' if random.random() < 0.7 else 'bank_account'
        
        # Generate receipt URL
        receipt_url = f"https://pay.stripe.com/receipts/{charge_id[3:]}"
        
        # Transaction ID for balance
        balance_transaction_id = f"txn_{charge_id[3:]}"
        
        # Payment method ID
        payment_method_id = f"pm_{charge_id[3:]}"
        
        # Create charge metadata
        charge_metadata = {
            "invoice_id": invoice['invoice_id'],
            "invoice_number": invoice['number'],
            "subscription_id": invoice['subscription']
        }
        
        # Parse invoice metadata if needed
        if invoice['metadata']:
            invoice_meta = invoice['metadata'] if isinstance(invoice['metadata'], dict) else json.loads(invoice['metadata'])
            charge_metadata['account_id'] = invoice_meta.get('account_id')
        
        charge = {
            'id': charge_id,
            'object': 'charge',
            'amount': invoice['amount_paid'],
            'amount_captured': invoice['amount_paid'],
            'amount_refunded': 0,
            'application': None,
            'application_fee': None,
            'application_fee_amount': None,
            'balance_transaction': balance_transaction_id,
            'billing_details': json.dumps(generate_billing_details(customer_info)),
            'calculated_statement_descriptor': "BAR MGMT PLATFORM",
            'captured': True,
            'created': invoice['created'] + timedelta(seconds=random.randint(10, 300)),
            'currency': invoice['currency'],
            'customer': invoice['customer'],
            'description': f"Payment for invoice {invoice['number']}",
            'destination': None,
            'dispute': None,
            'disputed': False,
            'failure_code': None,
            'failure_message': None,
            'fraud_details': json.dumps({}),
            'invoice': invoice['invoice_id'],
            'livemode': True,
            'metadata': json.dumps(charge_metadata),
            'on_behalf_of': None,
            'order_id': None,
            'outcome': json.dumps(generate_outcome()),
            'paid': True,
            'payment_intent': invoice['payment_intent'],
            'payment_method': payment_method_id,
            'payment_method_details': json.dumps(generate_payment_method_details(payment_type)),
            'receipt_email': customer_info.get('email'),
            'receipt_number': invoice['number'].replace('INV', 'RCPT'),
            'receipt_url': receipt_url,
            'refunded': False,
            'refunds': json.dumps({
                "object": "list",
                "data": [],
                "has_more": False,
                "total_count": 0
            }),
            'review': None,
            'shipping': None,
            'source': json.dumps({
                "id": payment_method_id,
                "object": payment_type,
                "type": payment_type
            }),
            'source_transfer': None,
            'statement_descriptor': None,
            'statement_descriptor_suffix': None,
            'status': 'succeeded',
            'transfer_data': None,
            'transfer_group': None,
            'created_at': invoice['created'] + timedelta(seconds=random.randint(10, 300))
        }
        
        charges.append(charge)
    
    return charges

def insert_stripe_charges(charges):
    """Insert Stripe charges into the database"""
    print(f"\nInserting {len(charges):,} charges into database...")
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(charges), batch_size):
        batch = charges[i:i + batch_size]
        inserted = db_helper.bulk_insert('stripe_charges', batch)
        total_inserted += inserted
        print(f"  Inserted batch {i//batch_size + 1}: {inserted:,} records")
    
    return total_inserted

def verify_stripe_charges():
    """Verify the inserted charges"""
    count = db_helper.get_row_count('stripe_charges')
    print(f"\n✓ Verification: {count:,} charges in database")
    
    # Show payment statistics
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Payment method distribution
        cursor.execute("""
            SELECT 
                payment_method_details->>'type' as payment_type,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM raw.stripe_charges
            GROUP BY payment_type
            ORDER BY count DESC
        """)
        payment_stats = cursor.fetchall()
        
        print("\nPayment method distribution:")
        for row in payment_stats:
            print(f"  {row['payment_type']}: {row['count']:,} charges, ${row['total_amount']/100:,.2f} total")
        
        # Monthly charge totals
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', created) as month,
                COUNT(*) as charge_count,
                SUM(amount) as total_amount
            FROM raw.stripe_charges
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly_stats = cursor.fetchall()
        
        print("\nRecent monthly charges:")
        for row in monthly_stats:
            print(f"  {row['month'].strftime('%Y-%m')}: {row['charge_count']:,} charges, ${row['total_amount']/100:,.2f}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Charge Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check for force flag
    force_mode = '--force' in sys.argv
    
    # Check if charges already exist
    existing_count = db_helper.get_row_count('stripe_charges')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} charges already exist")
        if force_mode:
            print("Force mode enabled - truncating existing data...")
            db_helper.truncate_table('stripe_charges')
        else:
            response = input("Do you want to truncate and regenerate? (y/N): ")
            if response.lower() == 'y':
                db_helper.truncate_table('stripe_charges')
            else:
                print("Aborting...")
                return
    
    # Load paid invoices
    invoices = load_paid_invoices()
    print(f"\n✓ Loaded {len(invoices):,} paid invoices")
    
    # Load customer details
    customer_map = load_customer_details()
    print(f"✓ Loaded {len(customer_map):,} customer details")
    
    # Generate charges
    charges = generate_stripe_charges(invoices, customer_map)
    
    # Insert into database
    inserted = insert_stripe_charges(charges)
    
    # Verify
    verify_stripe_charges()
    
    print(f"\n✅ Successfully generated {inserted:,} charges!")

if __name__ == "__main__":
    main()