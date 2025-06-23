#!/usr/bin/env python3
"""
Generate synthetic Stripe invoices data for the bar management SaaS platform.

This module creates Stripe invoice records with:
- Monthly invoices for active subscriptions
- Historical invoices for canceled subscriptions
- Payment success rate of 95%
- Late payment patterns
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

def load_stripe_subscriptions():
    """Load Stripe subscriptions with their details"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                s.id as subscription_id,
                s.customer,
                s.status,
                s.created as subscription_created,
                s.current_period_start,
                s.current_period_end,
                s.canceled_at,
                s.ended_at,
                s.trial_start,
                s.trial_end,
                s.metadata
            FROM raw.stripe_subscriptions s
            ORDER BY s.created
        """)
        subscriptions = cursor.fetchall()
    
    return subscriptions

def load_subscription_items():
    """Load subscription items to calculate invoice amounts"""
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                subscription,
                id as item_id,
                quantity,
                price,
                metadata
            FROM raw.stripe_subscription_items
            ORDER BY subscription, created
        """)
        items = cursor.fetchall()
    
    # Group by subscription
    items_by_subscription = {}
    for item in items:
        sub_id = item['subscription']
        if sub_id not in items_by_subscription:
            items_by_subscription[sub_id] = []
        items_by_subscription[sub_id].append(item)
    
    return items_by_subscription

def calculate_invoice_amount(subscription_items):
    """Calculate total amount for invoice based on subscription items"""
    total = 0
    
    for item in subscription_items:
        price_data = item['price'] if isinstance(item['price'], dict) else json.loads(item['price'])
        unit_amount = price_data.get('unit_amount', 0)
        quantity = item.get('quantity', 1)
        
        # For annual prices, we need to divide by 12 for monthly invoicing
        if price_data.get('recurring', {}).get('interval') == 'year':
            unit_amount = unit_amount // 12
        
        total += unit_amount * quantity
    
    return total

def generate_invoices_for_subscription(subscription, subscription_items):
    """Generate all invoices for a subscription based on its lifecycle"""
    invoices = []
    
    # Parse dates
    start_date = subscription['subscription_created']
    current_period_start = subscription['current_period_start']
    current_period_end = subscription['current_period_end']
    
    # Skip trial periods (no invoices during trial)
    if subscription['trial_end'] and start_date < subscription['trial_end']:
        start_date = subscription['trial_end']
    
    # Limit historical invoice generation to last 12 months to control total count
    # This gives us approximately the expected 1.5M invoices for 125K subscriptions
    invoice_history_limit = datetime.now() - relativedelta(months=12)
    if start_date < invoice_history_limit:
        start_date = invoice_history_limit
    
    # Determine the end date for invoice generation
    if subscription['status'] == 'active':
        end_date = datetime.now()
    else:
        end_date = subscription['ended_at'] or subscription['canceled_at'] or current_period_end
    
    # Generate monthly invoices
    invoice_date = start_date
    invoice_counter = 0
    
    while invoice_date <= end_date:
        invoice_counter += 1
        
        # Calculate period for this invoice
        period_start = invoice_date
        period_end = invoice_date + relativedelta(months=1)
        
        # Don't generate future invoices
        if period_start > datetime.now():
            break
        
        # Calculate invoice amount
        amount = calculate_invoice_amount(subscription_items)
        
        # Determine if invoice is paid (95% success rate)
        is_paid = random.random() < 0.95
        
        # Generate invoice ID
        invoice_id = f"in_{subscription['subscription_id'][4:]}_{invoice_counter:04d}"
        
        # Determine payment date (immediate for most, some delayed)
        if is_paid:
            if random.random() < 0.9:  # 90% pay immediately
                paid_at = invoice_date + timedelta(hours=random.randint(1, 4))
            else:  # 10% pay late (1-7 days)
                paid_at = invoice_date + timedelta(days=random.randint(1, 7))
        else:
            paid_at = None
        
        # Create status transitions
        status_transitions = {
            "finalized_at": int(invoice_date.timestamp()),
            "marked_uncollectible_at": None,
            "paid_at": int(paid_at.timestamp()) if paid_at else None,
            "voided_at": None
        }
        
        # Get customer metadata
        metadata = subscription['metadata'] if isinstance(subscription['metadata'], dict) else json.loads(subscription['metadata'])
        
        invoice = {
            'id': invoice_id,
            'object': 'invoice',
            'account_country': 'US',
            'account_name': f"Account {metadata.get('account_id', 'Unknown')}",
            'account_tax_ids': json.dumps([]),
            'amount_due': amount,
            'amount_paid': amount if is_paid else 0,
            'amount_remaining': 0 if is_paid else amount,
            'application_fee_amount': None,
            'attempt_count': 1 if is_paid else random.randint(1, 3),
            'attempted': True,
            'auto_advance': True,
            'billing_reason': 'subscription_cycle' if invoice_counter > 1 else 'subscription_create',
            'charge': f"ch_{invoice_id[3:]}" if is_paid else None,
            'collection_method': 'charge_automatically',
            'created': invoice_date,
            'currency': 'usd',
            'custom_fields': None,
            'customer': subscription['customer'],
            'customer_address': None,
            'customer_email': None,
            'customer_name': None,
            'customer_phone': None,
            'customer_shipping': None,
            'customer_tax_exempt': 'none',
            'customer_tax_ids': json.dumps([]),
            'default_payment_method': None,
            'default_source': None,
            'default_tax_rates': json.dumps([]),
            'description': None,
            'discount': None,
            'discounts': json.dumps([]),
            'due_date': None,
            'ending_balance': 0 if is_paid else amount,
            'footer': None,
            'hosted_invoice_url': f"https://invoice.stripe.com/{invoice_id}",
            'invoice_pdf': f"https://invoice.stripe.com/{invoice_id}/pdf",
            'last_finalization_error': None,
            'lines': json.dumps({
                "object": "list",
                "data": [
                    {
                        "id": f"il_{invoice_id[3:]}",
                        "object": "line_item",
                        "amount": item_amount,
                        "currency": "usd",
                        "description": f"Subscription item",
                        "period": {
                            "start": int(period_start.timestamp()),
                            "end": int(period_end.timestamp())
                        },
                        "price": item['price'],
                        "quantity": item['quantity']
                    }
                    for item, item_amount in [(i, calculate_invoice_amount([i])) for i in subscription_items]
                ],
                "has_more": False,
                "total_count": len(subscription_items)
            }),
            'livemode': True,
            'metadata': json.dumps({
                "subscription_id": subscription['subscription_id'],
                "account_id": metadata.get('account_id'),
                "invoice_number": invoice_counter
            }),
            'next_payment_attempt': None,
            'number': f"INV-{metadata.get('account_id', '0').zfill(4)}-{invoice_counter:04d}",
            'on_behalf_of': None,
            'paid': is_paid,
            'payment_intent': f"pi_{invoice_id[3:]}" if is_paid else None,
            'payment_settings': None,
            'period_end': period_end,
            'period_start': period_start,
            'post_payment_credit_notes_amount': 0,
            'pre_payment_credit_notes_amount': 0,
            'receipt_number': f"RCPT-{invoice_id[3:]}" if is_paid else None,
            'starting_balance': 0,
            'statement_descriptor': None,
            'status': 'paid' if is_paid else 'open',
            'status_transitions': json.dumps(status_transitions),
            'subscription': subscription['subscription_id'],
            'subtotal': amount,
            'tax': 0,
            'total': amount,
            'total_tax_amounts': json.dumps([]),
            'transfer_data': None,
            'webhooks_delivered_at': invoice_date + timedelta(seconds=random.randint(1, 10)),
            'created_at': invoice_date
        }
        
        invoices.append(invoice)
        
        # Move to next month
        invoice_date = period_end
        
        # Stop if subscription was canceled before next invoice
        if subscription['status'] == 'canceled' and invoice_date > end_date:
            break
    
    return invoices

def generate_stripe_invoices(subscriptions, items_by_subscription):
    """Generate all Stripe invoices"""
    all_invoices = []
    
    print(f"Generating invoices for {len(subscriptions):,} subscriptions...")
    
    for subscription in subscriptions:
        sub_id = subscription['subscription_id']
        subscription_items = items_by_subscription.get(sub_id, [])
        
        if not subscription_items:
            print(f"Warning: No items found for subscription {sub_id}")
            continue
        
        # Generate invoices for this subscription
        invoices = generate_invoices_for_subscription(subscription, subscription_items)
        all_invoices.extend(invoices)
    
    return all_invoices

def insert_stripe_invoices(invoices):
    """Insert Stripe invoices into the database"""
    print(f"\nInserting {len(invoices):,} invoices into database...")
    
    # Insert in batches due to large size
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(invoices), batch_size):
        batch = invoices[i:i + batch_size]
        inserted = db_helper.bulk_insert('stripe_invoices', batch)
        total_inserted += inserted
        print(f"  Inserted batch {i//batch_size + 1}: {inserted:,} records")
    
    return total_inserted

def verify_stripe_invoices():
    """Verify the inserted invoices"""
    count = db_helper.get_row_count('stripe_invoices')
    print(f"\n✓ Verification: {count:,} invoices in database")
    
    # Show payment statistics
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(amount_due) as total_amount,
                AVG(amount_due) as avg_amount
            FROM raw.stripe_invoices
            GROUP BY status
            ORDER BY count DESC
        """)
        status_stats = cursor.fetchall()
        
        print("\nInvoice status distribution:")
        for row in status_stats:
            print(f"  {row['status']}: {row['count']:,} invoices, ${row['total_amount']/100:,.2f} total")
        
        # Show monthly invoice counts
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', period_start) as month,
                COUNT(*) as invoice_count,
                SUM(amount_paid) as revenue
            FROM raw.stripe_invoices
            WHERE status = 'paid'
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly_stats = cursor.fetchall()
        
        print("\nRecent monthly revenue:")
        for row in monthly_stats:
            print(f"  {row['month'].strftime('%Y-%m')}: {row['invoice_count']:,} invoices, ${row['revenue']/100:,.2f}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Invoice Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if invoices already exist
    existing_count = db_helper.get_row_count('stripe_invoices')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} invoices already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_invoices')
        else:
            print("Aborting...")
            return
    
    # Load subscriptions
    subscriptions = load_stripe_subscriptions()
    print(f"\n✓ Loaded {len(subscriptions):,} Stripe subscriptions")
    
    # Load subscription items
    items_by_subscription = load_subscription_items()
    print(f"✓ Loaded subscription items for {len(items_by_subscription):,} subscriptions")
    
    # Generate invoices
    invoices = generate_stripe_invoices(subscriptions, items_by_subscription)
    
    # Insert into database
    inserted = insert_stripe_invoices(invoices)
    
    # Verify
    verify_stripe_invoices()
    
    print(f"\n✅ Successfully generated {inserted:,} invoices!")

if __name__ == "__main__":
    main()