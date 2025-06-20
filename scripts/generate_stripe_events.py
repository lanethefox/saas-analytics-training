#!/usr/bin/env python3
"""
Generate synthetic Stripe events data for the bar management SaaS platform.

This module creates Stripe event records with:
- Complete audit trail for all entity changes
- Event types for customers, subscriptions, invoices, charges
- Proper chronological ordering
- Realistic event patterns
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

def generate_event_id():
    """Generate a unique Stripe event ID"""
    return f"evt_{''.join(random.choices(string.ascii_letters + string.digits, k=24))}"

def load_entity_timeline():
    """Load all entities with their creation timestamps to build event timeline"""
    timeline = []
    
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        # Load customers
        cursor.execute("""
            SELECT 'customer' as entity_type, id, created, metadata
            FROM raw.stripe_customers
        """)
        for row in cursor.fetchall():
            timeline.append({
                'type': 'customer.created',
                'timestamp': row['created'],
                'object_id': row['id'],
                'object_type': 'customer',
                'data': {'id': row['id'], 'object': 'customer'}
            })
        
        # Load subscriptions with status changes
        cursor.execute("""
            SELECT id, created, status, canceled_at, ended_at, trial_end
            FROM raw.stripe_subscriptions
        """)
        for row in cursor.fetchall():
            # Subscription created
            timeline.append({
                'type': 'customer.subscription.created',
                'timestamp': row['created'],
                'object_id': row['id'],
                'object_type': 'subscription',
                'data': {'id': row['id'], 'object': 'subscription', 'status': 'active'}
            })
            
            # Trial ended (if applicable)
            if row['trial_end'] and row['trial_end'] > row['created']:
                timeline.append({
                    'type': 'customer.subscription.trial_will_end',
                    'timestamp': row['trial_end'] - timedelta(days=3),
                    'object_id': row['id'],
                    'object_type': 'subscription',
                    'data': {'id': row['id'], 'object': 'subscription'}
                })
            
            # Subscription canceled (if applicable)
            if row['canceled_at']:
                timeline.append({
                    'type': 'customer.subscription.deleted',
                    'timestamp': row['canceled_at'],
                    'object_id': row['id'],
                    'object_type': 'subscription',
                    'data': {'id': row['id'], 'object': 'subscription', 'status': 'canceled'}
                })
        
        # Load invoices
        cursor.execute("""
            SELECT id, created, status, paid, customer, subscription
            FROM raw.stripe_invoices
        """)
        for row in cursor.fetchall():
            # Invoice created
            timeline.append({
                'type': 'invoice.created',
                'timestamp': row['created'],
                'object_id': row['id'],
                'object_type': 'invoice',
                'data': {'id': row['id'], 'object': 'invoice', 'customer': row['customer']}
            })
            
            # Invoice finalized (1 hour after creation)
            timeline.append({
                'type': 'invoice.finalized',
                'timestamp': row['created'] + timedelta(hours=1),
                'object_id': row['id'],
                'object_type': 'invoice',
                'data': {'id': row['id'], 'object': 'invoice'}
            })
            
            # Invoice paid (if applicable)
            if row['paid']:
                timeline.append({
                    'type': 'invoice.paid',
                    'timestamp': row['created'] + timedelta(hours=2),
                    'object_id': row['id'],
                    'object_type': 'invoice',
                    'data': {'id': row['id'], 'object': 'invoice', 'paid': True}
                })
                
                # Payment succeeded event
                timeline.append({
                    'type': 'invoice.payment_succeeded',
                    'timestamp': row['created'] + timedelta(hours=2, minutes=1),
                    'object_id': row['id'],
                    'object_type': 'invoice',
                    'data': {'id': row['id'], 'object': 'invoice'}
                })
        
        # Load charges
        cursor.execute("""
            SELECT id, created, status, amount, customer, invoice
            FROM raw.stripe_charges
            WHERE status = 'succeeded'
            LIMIT 1000  -- Limit to avoid too many events
        """)
        for row in cursor.fetchall():
            # Charge created
            timeline.append({
                'type': 'charge.succeeded',
                'timestamp': row['created'],
                'object_id': row['id'],
                'object_type': 'charge',
                'data': {
                    'id': row['id'], 
                    'object': 'charge',
                    'amount': row['amount'],
                    'customer': row['customer'],
                    'invoice': row['invoice']
                }
            })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    return timeline

def generate_stripe_events(timeline):
    """Generate Stripe event records from timeline"""
    events = []
    
    print(f"Generating {len(timeline):,} events from timeline...")
    
    for idx, item in enumerate(timeline):
        event_id = generate_event_id()
        
        # Add some randomness to timestamps to avoid exact duplicates
        timestamp = item['timestamp'] + timedelta(seconds=random.randint(0, 59))
        
        # Create request object (simulating API calls)
        request_data = {
            "id": f"req_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}",
            "idempotency_key": None
        }
        
        event = {
            'id': event_id,
            'object': 'event',
            'api_version': '2020-08-27',
            'created': timestamp,
            'data': json.dumps({
                'object': item['data'],
                'previous_attributes': {}
            }),
            'livemode': True,
            'pending_webhooks': 0,
            'request': json.dumps(request_data),
            'type': item['type'],
            'created_at': timestamp
        }
        
        events.append(event)
    
    # Add some webhook events
    webhook_events = generate_webhook_events(timeline)
    events.extend(webhook_events)
    
    # Sort all events by timestamp
    events.sort(key=lambda x: x['created'])
    
    return events

def generate_webhook_events(timeline):
    """Generate additional webhook-related events"""
    webhook_events = []
    
    # Sample some events for webhook delivery
    sampled_events = random.sample(timeline, min(100, len(timeline) // 10))
    
    for item in sampled_events:
        # Webhook endpoint added
        if random.random() < 0.1:  # 10% chance
            event_id = generate_event_id()
            timestamp = item['timestamp'] - timedelta(days=random.randint(1, 30))
            
            webhook_events.append({
                'id': event_id,
                'object': 'event',
                'api_version': '2020-08-27',
                'created': timestamp,
                'data': json.dumps({
                    'object': {
                        'id': f"we_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}",
                        'object': 'webhook_endpoint',
                        'url': 'https://api.example.com/webhooks/stripe'
                    }
                }),
                'livemode': True,
                'pending_webhooks': 0,
                'request': json.dumps({"id": None, "idempotency_key": None}),
                'type': 'webhook_endpoint.created',
                'created_at': timestamp
            })
    
    return webhook_events

def insert_stripe_events(events):
    """Insert Stripe events into the database"""
    print(f"\nInserting {len(events):,} events into database...")
    
    # Insert in batches
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        inserted = db_helper.bulk_insert('stripe_events', batch)
        total_inserted += inserted
        print(f"  Inserted batch {i//batch_size + 1}: {inserted:,} records")
    
    return total_inserted

def verify_stripe_events():
    """Verify the inserted events"""
    count = db_helper.get_row_count('stripe_events')
    print(f"\n✓ Verification: {count:,} events in database")
    
    # Show event type distribution
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as count
            FROM raw.stripe_events
            GROUP BY type
            ORDER BY count DESC
            LIMIT 10
        """)
        event_types = cursor.fetchall()
        
        print("\nTop event types:")
        for row in event_types:
            print(f"  {row['type']}: {row['count']:,}")
        
        # Show events per month
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', created) as month,
                COUNT(*) as event_count
            FROM raw.stripe_events
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly_stats = cursor.fetchall()
        
        print("\nRecent monthly event counts:")
        for row in monthly_stats:
            print(f"  {row['month'].strftime('%Y-%m')}: {row['event_count']:,} events")

def main():
    """Main execution function"""
    print("=" * 60)
    print("Stripe Event Generation")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if events already exist
    existing_count = db_helper.get_row_count('stripe_events')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} events already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('stripe_events')
        else:
            print("Aborting...")
            return
    
    # Load entity timeline
    timeline = load_entity_timeline()
    print(f"\n✓ Built timeline with {len(timeline):,} entity changes")
    
    # Generate events
    events = generate_stripe_events(timeline)
    
    # Insert into database
    inserted = insert_stripe_events(events)
    
    # Verify
    verify_stripe_events()
    
    print(f"\n✅ Successfully generated {inserted:,} events!")

if __name__ == "__main__":
    main()