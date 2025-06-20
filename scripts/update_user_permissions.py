#!/usr/bin/env python3
"""
Update user permissions with detailed role-based access controls.

This script:
- Adds detailed permissions JSON for each user role
- Ensures permissions align with role responsibilities
- Updates the users table with structured permission data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

# Role-based permission templates
ROLE_PERMISSIONS = {
    'admin': {
        'dashboard': {
            'view': True,
            'edit': True,
            'export': True
        },
        'users': {
            'view': True,
            'create': True,
            'edit': True,
            'delete': True,
            'manage_roles': True
        },
        'billing': {
            'view': True,
            'manage_subscriptions': True,
            'manage_payment_methods': True,
            'view_invoices': True,
            'manage_billing_contacts': True
        },
        'locations': {
            'view': True,
            'create': True,
            'edit': True,
            'delete': True,
            'manage_all': True
        },
        'devices': {
            'view': True,
            'create': True,
            'edit': True,
            'delete': True,
            'manage_firmware': True,
            'view_telemetry': True
        },
        'inventory': {
            'view': True,
            'edit': True,
            'manage_suppliers': True,
            'approve_orders': True
        },
        'reports': {
            'view_all': True,
            'create_custom': True,
            'export': True,
            'schedule': True,
            'share': True
        },
        'integrations': {
            'view': True,
            'manage': True,
            'configure_api': True
        },
        'settings': {
            'view': True,
            'edit': True,
            'manage_company': True,
            'manage_security': True
        }
    },
    'manager': {
        'dashboard': {
            'view': True,
            'edit': False,
            'export': True
        },
        'users': {
            'view': True,
            'create': False,
            'edit': True,
            'delete': False,
            'manage_roles': False
        },
        'billing': {
            'view': True,
            'manage_subscriptions': False,
            'manage_payment_methods': False,
            'view_invoices': True,
            'manage_billing_contacts': False
        },
        'locations': {
            'view': True,
            'create': False,
            'edit': True,
            'delete': False,
            'manage_all': False
        },
        'devices': {
            'view': True,
            'create': True,
            'edit': True,
            'delete': False,
            'manage_firmware': False,
            'view_telemetry': True
        },
        'inventory': {
            'view': True,
            'edit': True,
            'manage_suppliers': True,
            'approve_orders': False
        },
        'reports': {
            'view_all': True,
            'create_custom': False,
            'export': True,
            'schedule': False,
            'share': True
        },
        'integrations': {
            'view': True,
            'manage': False,
            'configure_api': False
        },
        'settings': {
            'view': True,
            'edit': False,
            'manage_company': False,
            'manage_security': False
        }
    },
    'staff': {
        'dashboard': {
            'view': True,
            'edit': False,
            'export': False
        },
        'users': {
            'view': False,
            'create': False,
            'edit': False,
            'delete': False,
            'manage_roles': False
        },
        'billing': {
            'view': False,
            'manage_subscriptions': False,
            'manage_payment_methods': False,
            'view_invoices': False,
            'manage_billing_contacts': False
        },
        'locations': {
            'view': True,
            'create': False,
            'edit': False,
            'delete': False,
            'manage_all': False
        },
        'devices': {
            'view': True,
            'create': False,
            'edit': False,
            'delete': False,
            'manage_firmware': False,
            'view_telemetry': False
        },
        'inventory': {
            'view': True,
            'edit': True,
            'manage_suppliers': False,
            'approve_orders': False
        },
        'reports': {
            'view_all': False,
            'create_custom': False,
            'export': False,
            'schedule': False,
            'share': False
        },
        'integrations': {
            'view': False,
            'manage': False,
            'configure_api': False
        },
        'settings': {
            'view': False,
            'edit': False,
            'manage_company': False,
            'manage_security': False
        },
        'pos': {
            'use': True,
            'void_transactions': False,
            'apply_discounts': True,
            'manage_cash_drawer': True
        }
    }
}

def add_permissions_column():
    """Add permissions column if it doesn't exist."""
    with db_helper.config.get_cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_users'
            AND column_name = 'permissions'
        """)
        
        if cursor.rowcount == 0:
            print("Adding permissions column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_users 
                ADD COLUMN permissions JSONB
            """)
            cursor.connection.commit()
            return True
        return False

def update_user_permissions():
    """Update all users with detailed permissions based on their role."""
    with db_helper.config.get_cursor() as cursor:
        # Get all users
        cursor.execute("""
            SELECT id, role, email
            FROM raw.app_database_users
            ORDER BY id
        """)
        users = cursor.fetchall()
        
        print(f"Updating permissions for {len(users)} users...")
        
        # Track role distribution
        role_counts = {}
        updates = []
        
        for user_id, role, email in users:
            # Get base permissions for role
            permissions = ROLE_PERMISSIONS.get(role.lower(), ROLE_PERMISSIONS['staff'])
            
            # Add some user-specific metadata
            permissions['_metadata'] = {
                'role': role,
                'permissions_version': '2.0',
                'last_updated': '2025-06-20',
                'custom_permissions': []
            }
            
            # For some admin users, add extra permissions
            if role.lower() == 'admin' and user_id % 5 == 0:
                permissions['_metadata']['custom_permissions'].append('super_admin')
                permissions['system'] = {
                    'view_logs': True,
                    'manage_api_keys': True,
                    'impersonate_users': True
                }
            
            updates.append((json.dumps(permissions), user_id))
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Batch update
        cursor.executemany("""
            UPDATE raw.app_database_users
            SET permissions = %s::jsonb
            WHERE id = %s
        """, updates)
        
        cursor.connection.commit()
        
        return role_counts

def save_permissions_summary():
    """Save summary of permissions distribution."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT role, COUNT(*) as user_count
            FROM raw.app_database_users
            GROUP BY role
            ORDER BY user_count DESC
        """)
        
        role_data = []
        for row in cursor.fetchall():
            role = row[0]
            count = row[1]
            
            # Get sample permissions
            sample_perms = ROLE_PERMISSIONS.get(role.lower(), {})
            
            role_data.append({
                'role': role,
                'user_count': count,
                'key_permissions': {
                    'can_manage_users': sample_perms.get('users', {}).get('manage_roles', False),
                    'can_manage_billing': sample_perms.get('billing', {}).get('manage_subscriptions', False),
                    'can_export_reports': sample_perms.get('reports', {}).get('export', False),
                    'can_manage_devices': sample_perms.get('devices', {}).get('manage_firmware', False)
                }
            })
        
        # Count special permissions
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw.app_database_users
            WHERE permissions->>'_metadata' IS NOT NULL
            AND permissions->'_metadata'->>'custom_permissions' LIKE '%super_admin%'
        """)
        super_admin_count = cursor.fetchone()[0]
        
        summary = {
            'total_users': sum(r['user_count'] for r in role_data),
            'role_distribution': role_data,
            'super_admin_users': super_admin_count,
            'permission_structure': {
                'modules': list(ROLE_PERMISSIONS['admin'].keys()),
                'roles': list(ROLE_PERMISSIONS.keys())
            }
        }
        
        with open('data/user_permissions_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✓ Saved permissions summary to data/user_permissions_summary.json")

def main():
    print("=== Updating User Permissions ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Add permissions column if needed
    column_added = add_permissions_column()
    if column_added:
        print("✓ Added permissions column to users table")
    
    # Update permissions
    print("\nUpdating user permissions...")
    role_counts = update_user_permissions()
    
    print("\nRole distribution:")
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {role}: {count} users")
    
    # Save summary
    save_permissions_summary()
    
    # Show sample permissions
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT email, role, 
                   permissions->'dashboard'->>'view' as can_view_dashboard,
                   permissions->'billing'->>'manage_subscriptions' as can_manage_billing,
                   permissions->'users'->>'manage_roles' as can_manage_roles
            FROM raw.app_database_users
            WHERE permissions IS NOT NULL
            LIMIT 5
        """)
        
        print("\nSample user permissions:")
        for email, role, dash, bill, roles in cursor.fetchall():
            print(f"  - {email} ({role}):")
            print(f"    • View Dashboard: {dash}")
            print(f"    • Manage Billing: {bill}")
            print(f"    • Manage Roles: {roles}")
    
    # Verify all updated
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(permissions) as with_permissions
            FROM raw.app_database_users
        """)
        total, with_perms = cursor.fetchone()
        
        if total == with_perms:
            print(f"\n✓ Successfully updated all {total} users with permissions")
        else:
            print(f"\n⚠ Updated {with_perms} out of {total} users with permissions")
    
    print("\n✓ Task 34 complete!")

if __name__ == "__main__":
    main()