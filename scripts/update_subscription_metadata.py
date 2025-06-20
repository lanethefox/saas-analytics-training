#!/usr/bin/env python3
"""
Update subscription metadata with additional business context.

This script:
- Adds metadata JSON to subscriptions
- Includes contract details, feature flags, usage limits
- Updates the subscriptions table with enriched data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from datetime import datetime, timedelta
import random

# Subscription tier features and limits
TIER_METADATA = {
    1: {  # Basic
        'name': 'Basic',
        'features': {
            'locations_included': 1,
            'devices_per_location': 3,
            'users_included': 5,
            'api_calls_per_month': 10000,
            'data_retention_days': 90,
            'support_level': 'standard',
            'reporting': {
                'basic_reports': True,
                'custom_reports': False,
                'export_formats': ['csv', 'pdf'],
                'scheduled_reports': False
            },
            'integrations': {
                'stripe': True,
                'quickbooks': False,
                'salesforce': False,
                'custom_api': False
            }
        },
        'usage_limits': {
            'monthly_transactions': 5000,
            'monthly_pour_volume_oz': 50000,
            'concurrent_devices': 5,
            'api_rate_limit_per_minute': 60
        }
    },
    2: {  # Pro
        'name': 'Pro',
        'features': {
            'locations_included': 3,
            'devices_per_location': 10,
            'users_included': 20,
            'api_calls_per_month': 100000,
            'data_retention_days': 365,
            'support_level': 'priority',
            'reporting': {
                'basic_reports': True,
                'custom_reports': True,
                'export_formats': ['csv', 'pdf', 'excel', 'json'],
                'scheduled_reports': True
            },
            'integrations': {
                'stripe': True,
                'quickbooks': True,
                'salesforce': True,
                'custom_api': False
            }
        },
        'usage_limits': {
            'monthly_transactions': 50000,
            'monthly_pour_volume_oz': 500000,
            'concurrent_devices': 30,
            'api_rate_limit_per_minute': 300
        }
    },
    3: {  # Enterprise
        'name': 'Enterprise',
        'features': {
            'locations_included': 999,  # Unlimited
            'devices_per_location': 999,  # Unlimited
            'users_included': 999,  # Unlimited
            'api_calls_per_month': 999999999,  # Unlimited
            'data_retention_days': 999999,  # Unlimited
            'support_level': 'dedicated',
            'reporting': {
                'basic_reports': True,
                'custom_reports': True,
                'export_formats': ['csv', 'pdf', 'excel', 'json', 'xml', 'api'],
                'scheduled_reports': True,
                'white_label': True
            },
            'integrations': {
                'stripe': True,
                'quickbooks': True,
                'salesforce': True,
                'custom_api': True,
                'sso': True,
                'custom_webhooks': True
            }
        },
        'usage_limits': {
            'monthly_transactions': 999999999,  # Unlimited
            'monthly_pour_volume_oz': 999999999,  # Unlimited
            'concurrent_devices': 999999,  # Unlimited
            'api_rate_limit_per_minute': 1000
        }
    }
}

def add_metadata_column():
    """Add metadata column if it doesn't exist."""
    with db_helper.config.get_cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_subscriptions'
            AND column_name = 'metadata'
        """)
        
        if cursor.rowcount == 0:
            print("Adding metadata column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_subscriptions 
                ADD COLUMN metadata JSONB
            """)
            cursor.connection.commit()
            return True
        return False

def generate_subscription_metadata(subscription):
    """Generate metadata for a subscription."""
    sub_id, account_id, plan_name, status, start_date, end_date = subscription
    
    # Extract tier from plan name (Basic=1, Pro=2, Enterprise=3)
    if 'Enterprise' in plan_name:
        tier = 3
    elif 'Pro' in plan_name:
        tier = 2
    else:
        tier = 1
    
    # Get tier metadata
    tier_meta = TIER_METADATA.get(tier, TIER_METADATA[1])
    
    # Calculate contract details
    contract_length = 12 if tier == 3 else (6 if tier == 2 else 0)  # Enterprise: 12mo, Pro: 6mo, Basic: month-to-month
    
    metadata = {
        'tier_details': tier_meta,
        'contract': {
            'type': 'annual' if tier == 3 else ('semi-annual' if tier == 2 else 'monthly'),
            'minimum_term_months': contract_length,
            'auto_renew': True,
            'negotiated_discount': 0.1 if tier == 3 else 0,  # 10% enterprise discount
            'payment_terms': 'net_30' if tier == 3 else 'due_on_receipt'
        },
        'usage_tracking': {
            'current_locations': random.randint(1, tier_meta['features']['locations_included']),
            'current_devices': random.randint(
                tier_meta['features']['devices_per_location'], 
                tier_meta['features']['devices_per_location'] * 3
            ),
            'current_users': random.randint(3, tier_meta['features']['users_included']),
            'last_month_transactions': random.randint(100, tier_meta['usage_limits']['monthly_transactions'] // 2),
            'last_month_api_calls': random.randint(100, tier_meta['features']['api_calls_per_month'] // 2),
            'last_month_pour_volume_oz': random.randint(1000, tier_meta['usage_limits']['monthly_pour_volume_oz'] // 2)
        },
        'billing_preferences': {
            'invoice_delivery': 'email',
            'payment_method': 'credit_card' if tier < 3 else 'bank_transfer',
            'billing_contact_different': random.choice([True, False]),
            'tax_exempt': tier == 3 and random.random() < 0.3,  # Some enterprises are tax exempt
            'currency': 'USD'
        },
        'account_health': {
            'payment_history': 'excellent' if random.random() < 0.8 else 'good',
            'support_tickets_last_30_days': random.randint(0, 5),
            'feature_adoption_score': random.uniform(0.4, 0.95),
            'nps_score': random.choice([9, 10]) if tier == 3 else random.choice([7, 8, 9]),
            'expansion_potential': 'high' if tier < 3 else 'low',
            'churn_risk': 'low' if status == 'active' else 'high'
        },
        'custom_configuration': {},
        'notes': []
    }
    
    # Add some custom configurations for certain accounts
    if random.random() < 0.2:
        metadata['custom_configuration']['custom_branding'] = True
        metadata['notes'].append("Custom branding enabled")
    
    if tier == 3 and random.random() < 0.5:
        metadata['custom_configuration']['dedicated_server'] = True
        metadata['custom_configuration']['sla_uptime'] = 99.9
        metadata['notes'].append("Enterprise SLA in effect")
    
    # Add upgrade/downgrade history
    metadata['subscription_changes'] = []
    if random.random() < 0.3 and tier > 1:
        change_date = start_date + timedelta(days=random.randint(30, 180))
        metadata['subscription_changes'].append({
            'date': change_date.isoformat(),
            'type': 'upgrade',
            'from_tier': tier - 1,
            'to_tier': tier,
            'reason': random.choice(['growth', 'features_needed', 'sales_negotiation'])
        })
    
    return metadata

def update_subscription_metadata():
    """Update all subscriptions with metadata."""
    with db_helper.config.get_cursor() as cursor:
        # Get all subscriptions
        cursor.execute("""
            SELECT id, customer_id, plan_name, status, start_date, end_date
            FROM raw.app_database_subscriptions
            ORDER BY id
        """)
        subscriptions = cursor.fetchall()
        
        print(f"Updating metadata for {len(subscriptions)} subscriptions...")
        
        # Track statistics
        tier_counts = {}
        status_counts = {}
        updates = []
        
        for subscription in subscriptions:
            sub_id = subscription[0]
            plan_name = subscription[2]
            status = subscription[3]
            
            # Extract tier from plan name
            if 'Enterprise' in plan_name:
                tier = 3
            elif 'Pro' in plan_name:
                tier = 2
            else:
                tier = 1
            
            metadata = generate_subscription_metadata(subscription)
            updates.append((json.dumps(metadata), sub_id))
            
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Batch update
        cursor.executemany("""
            UPDATE raw.app_database_subscriptions
            SET metadata = %s::jsonb
            WHERE id = %s
        """, updates)
        
        cursor.connection.commit()
        
        return tier_counts, status_counts

def save_metadata_summary():
    """Save summary of subscription metadata."""
    with db_helper.config.get_cursor() as cursor:
        # Get tier distribution with usage
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN plan_name LIKE '%Enterprise%' THEN 3
                    WHEN plan_name LIKE '%Pro%' THEN 2
                    ELSE 1
                END as tier,
                COUNT(*) as count,
                AVG((metadata->'usage_tracking'->>'current_locations')::int) as avg_locations,
                AVG((metadata->'usage_tracking'->>'current_devices')::int) as avg_devices,
                AVG((metadata->'account_health'->>'feature_adoption_score')::float) as avg_adoption
            FROM raw.app_database_subscriptions
            WHERE metadata IS NOT NULL AND status = 'active'
            GROUP BY tier
            ORDER BY tier
        """)
        
        tier_data = []
        for row in cursor.fetchall():
            tier_data.append({
                'tier': row[0],
                'tier_name': TIER_METADATA[row[0]]['name'],
                'active_subscriptions': row[1],
                'avg_locations_used': float(row[2]) if row[2] else 0,
                'avg_devices_used': float(row[3]) if row[3] else 0,
                'avg_feature_adoption': float(row[4]) if row[4] else 0
            })
        
        # Get payment method distribution
        cursor.execute("""
            SELECT 
                metadata->'billing_preferences'->>'payment_method' as payment_method,
                COUNT(*) as count
            FROM raw.app_database_subscriptions
            WHERE metadata IS NOT NULL
            GROUP BY payment_method
        """)
        
        payment_methods = {row[0]: row[1] for row in cursor.fetchall()}
        
        summary = {
            'tier_distribution': tier_data,
            'payment_methods': payment_methods,
            'metadata_structure': {
                'tier_features': list(TIER_METADATA[1]['features'].keys()),
                'usage_metrics': list(TIER_METADATA[1]['usage_limits'].keys()),
                'health_indicators': ['payment_history', 'support_tickets', 'feature_adoption', 'nps_score', 'churn_risk']
            }
        }
        
        with open('data/subscription_metadata_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✓ Saved metadata summary to data/subscription_metadata_summary.json")

def main():
    print("=== Updating Subscription Metadata ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Add metadata column if needed
    column_added = add_metadata_column()
    if column_added:
        print("✓ Added metadata column to subscriptions table")
    
    # Update metadata
    print("\nGenerating subscription metadata...")
    tier_counts, status_counts = update_subscription_metadata()
    
    print("\nSubscription distribution:")
    print("By Tier:")
    for tier, count in sorted(tier_counts.items()):
        tier_name = TIER_METADATA[tier]['name']
        print(f"  - {tier_name} (Tier {tier}): {count} subscriptions")
    
    print("\nBy Status:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {status}: {count} subscriptions")
    
    # Save summary
    save_metadata_summary()
    
    # Show sample metadata
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.id,
                a.name as company_name,
                s.plan_name,
                s.metadata->'tier_details'->>'name' as tier_name,
                s.metadata->'usage_tracking'->>'current_locations' as locations,
                s.metadata->'account_health'->>'feature_adoption_score' as adoption
            FROM raw.app_database_subscriptions s
            JOIN raw.app_database_accounts a ON s.customer_id = a.id
            WHERE s.metadata IS NOT NULL AND s.status = 'active'
            LIMIT 3
        """)
        
        print("\nSample subscription metadata:")
        for sub_id, company, tier, tier_name, locations, adoption in cursor.fetchall():
            print(f"\n  {company} ({tier_name}):")
            print(f"    • Subscription ID: {sub_id}")
            print(f"    • Locations in use: {locations}")
            print(f"    • Feature adoption: {float(adoption):.1%}")
    
    # Verify all updated
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(metadata) as with_metadata
            FROM raw.app_database_subscriptions
        """)
        total, with_meta = cursor.fetchone()
        
        if total == with_meta:
            print(f"\n✓ Successfully updated all {total} subscriptions with metadata")
        else:
            print(f"\n⚠ Updated {with_meta} out of {total} subscriptions with metadata")
    
    print("\n✓ Task 36 complete!")

if __name__ == "__main__":
    main()