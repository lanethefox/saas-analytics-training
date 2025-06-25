#!/usr/bin/env python3
"""
Generate deterministic users data for the TapFlow Analytics platform.

This module creates users with:
- Proper distribution per account size (small: 2-5, medium: 5-20, large: 20-100, enterprise: 100-500)
- Role distribution from configuration (admin: 10%, manager: 30%, staff: 60%)
- Sequential IDs within reserved range (1-6000)
- Realistic login patterns and permissions
"""

import sys
import os
import random
import json
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig, IDAllocator

import os

def should_truncate():
    """Check if we should auto-truncate in Docker environment"""
    if os.environ.get('DOCKER_ENV', 'false').lower() == 'true':
        return True
    response = input("Do you want to truncate and regenerate? (y/N): ")
    return response.lower() == 'y'

# Initialize configuration
config = DataGenerationConfig()
id_allocator = IDAllocator(config)

# Initialize Faker with seed from config
fake = Faker()

# Permissions by role
ROLE_PERMISSIONS = {
    'admin': {
        'can_manage_users': True,
        'can_manage_billing': True,
        'can_view_reports': True,
        'can_manage_devices': True,
        'can_manage_products': True,
        'can_export_data': True,
        'can_access_api': True,
        'can_manage_locations': True
    },
    'manager': {
        'can_manage_users': False,
        'can_manage_billing': False,
        'can_view_reports': True,
        'can_manage_devices': True,
        'can_manage_products': True,
        'can_export_data': True,
        'can_access_api': True,
        'can_manage_locations': False
    },
    'staff': {
        'can_manage_users': False,
        'can_manage_billing': False,
        'can_view_reports': False,
        'can_manage_devices': False,
        'can_manage_products': False,
        'can_export_data': False,
        'can_access_api': False,
        'can_manage_locations': False
    }
}

def get_users_for_account(account):
    """Determine number of users based on account size"""
    size = account['account_size']
    distribution = config.get_account_distribution()[size]
    
    # Get the range for this account size
    min_users = distribution['users_min']
    max_users = distribution['users_max']
    
    # Use a weighted distribution within the range
    if size == 'small':
        # Most small accounts have minimum users
        if random.random() < 0.6:
            return min_users
        else:
            return random.randint(min_users, min(max_users, 3))
    elif size == 'medium':
        # Medium accounts spread across range
        return random.randint(min_users, max_users)
    elif size == 'large':
        # Large accounts tend toward middle of range
        mid = (min_users + max_users) // 2
        return random.randint(mid - 10, mid + 10)
    else:  # enterprise
        # Enterprise accounts have many users
        return random.randint(min_users, max_users)

def generate_email(first_name, last_name, domain, index):
    """Generate email address with various patterns"""
    # First user (admin) gets a standard pattern
    if index == 0:
        return f"admin@{domain}"
    
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}@{domain}",
        f"{first_name[0].lower()}{last_name.lower()}@{domain}",
        f"{first_name.lower()}{last_name[0].lower()}@{domain}",
        f"{first_name.lower()}_{last_name.lower()}@{domain}",
        f"{first_name.lower()}{index}@{domain}"
    ]
    return random.choice(patterns)

def get_login_frequency(role):
    """Get average days between logins based on role"""
    if role == 'admin':
        return random.uniform(0.5, 2)  # Admins login very frequently
    elif role == 'manager':
        return random.uniform(1, 4)  # Managers login regularly
    else:  # staff
        return random.uniform(2, 7)  # Staff login less frequently

def assign_user_roles(num_users):
    """Assign roles to users based on configuration percentages"""
    roles = []
    role_config = config.get_user_roles()
    
    # First user is always admin
    roles.append('admin')
    
    # Calculate remaining role distribution
    remaining = num_users - 1
    if remaining > 0:
        # Calculate counts for each role
        admin_count = max(0, int(remaining * role_config['admin']['percentage']) - 1)  # Subtract 1 for first admin
        manager_count = int(remaining * role_config['manager']['percentage'])
        staff_count = remaining - admin_count - manager_count
        
        # Add roles
        roles.extend(['admin'] * admin_count)
        roles.extend(['manager'] * manager_count)
        roles.extend(['staff'] * staff_count)
        
        # Shuffle non-first roles for variety
        if len(roles) > 1:
            tail = roles[1:]
            random.shuffle(tail)
            roles = [roles[0]] + tail
    
    return roles

def generate_users():
    """Generate deterministic user data"""
    # Load accounts from the saved mapping
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_accounts.json'
    )
    
    with open(mapping_file, 'r') as f:
        accounts = json.load(f)
    
    # Convert ISO strings back to datetime
    for acc in accounts:
        acc['created_at'] = datetime.fromisoformat(acc['created_at'])
        acc['updated_at'] = datetime.fromisoformat(acc['updated_at'])
    
    users = []
    
    print(f"Generating users for {len(accounts)} accounts...")
    
    # Reset ID allocator for users
    id_allocator.current_ids['users'] = 1
    
    total_users = 0
    
    for account in accounts:
        num_users = get_users_for_account(account)
        
        # Extract domain from email
        domain = account['email'].split('@')[1]
        
        # Assign roles
        roles = assign_user_roles(num_users)
        
        for i, role in enumerate(roles):
            # Generate user details
            fake.seed_instance(account['id'] * 1000 + i)  # Deterministic per user
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Get sequential user ID
            user_id = id_allocator.get_next_id('users')
            
            # Calculate dates
            created_at = account['created_at'] + timedelta(days=random.randint(0, 30))
            
            # Last login based on role and account activity
            if account['is_active']:
                login_freq = get_login_frequency(role)
                days_since_login = int(random.expovariate(1/login_freq))
                last_login = datetime.now() - timedelta(days=days_since_login)
                
                # Ensure last login is after creation
                if last_login < created_at:
                    last_login = created_at + timedelta(days=1)
            else:
                # Inactive accounts have old last logins
                last_login = created_at + timedelta(days=random.randint(30, 180))
            
            # Calculate login count based on account age and role
            account_age_days = (datetime.now() - created_at).days
            if account_age_days > 0:
                if role == 'admin':
                    avg_logins_per_day = 2.0
                elif role == 'manager':
                    avg_logins_per_day = 1.0
                else:
                    avg_logins_per_day = 0.5
                
                login_count = int(account_age_days * avg_logins_per_day * random.uniform(0.7, 1.3))
            else:
                login_count = 1
            
            user = {
                'id': user_id,
                'customer_id': account['id'],
                'email': generate_email(first_name, last_name, domain, i),
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'permissions': json.dumps(ROLE_PERMISSIONS[role]),
                'is_active': account['is_active'] and random.random() < 0.95,
                'phone': fake.phone_number(),
                'last_login_at': last_login,
                'login_count': login_count,
                'created_at': created_at,
                'updated_at': created_at + timedelta(days=random.randint(0, 90))
            }
            
            users.append(user)
            total_users += 1
    
    print(f"  Generated {total_users} total users")
    print(f"  Average users per account: {total_users / len(accounts):.2f}")
    
    return users

def insert_users(users):
    """Insert users into the database"""
    print(f"\nInserting {len(users)} users into database...")
    
    # Map our generated data to actual table columns
    mapped_users = []
    for user in users:
        mapped = {
            'id': user['id'],
            'customer_id': user['customer_id'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'email': user['email'],
            'role': user['role'],
            'created_date': user['created_at'].date(),
            'last_login_date': user['last_login_at'].date(),
            'created_at': user['created_at'],
            'updated_at': user['updated_at']
        }
        mapped_users.append(mapped)
    
    # Insert using bulk insert helper
    inserted = db_helper.bulk_insert('app_database_users', mapped_users)
    return inserted

def save_user_mapping(users):
    """Save user mapping to JSON file for use by other generators"""
    mapping_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'generated_users.json'
    )
    
    # Save the full user data
    serializable_users = []
    for user in users:
        user_copy = user.copy()
        user_copy['created_at'] = user_copy['created_at'].isoformat()
        user_copy['updated_at'] = user_copy['updated_at'].isoformat()
        user_copy['last_login_at'] = user_copy['last_login_at'].isoformat()
        # Keep permissions as string (already JSON)
        serializable_users.append(user_copy)
    
    with open(mapping_file, 'w') as f:
        json.dump(serializable_users, f, indent=2)
    
    print(f"\n✓ Saved user mapping to {mapping_file}")

def verify_users():
    """Verify the inserted users"""
    count = db_helper.get_row_count('app_database_users')
    print(f"\n✓ Verification: {count} users in database")
    
    # Show distribution statistics
    with db_helper.config.get_cursor() as cursor:
        # Role distribution
        cursor.execute("""
            SELECT role, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_users
            GROUP BY role
            ORDER BY count DESC
        """)
        role_dist = cursor.fetchall()
        
        print("\nRole distribution:")
        for row in role_dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        # Users per account
        cursor.execute("""
            SELECT user_count, COUNT(*) as account_count
            FROM (
                SELECT customer_id, COUNT(*) as user_count
                FROM raw.app_database_users
                GROUP BY customer_id
            ) uc
            GROUP BY user_count
            ORDER BY user_count
            LIMIT 10
        """)
        per_account = cursor.fetchall()
        
        print("\nUsers per account distribution (top 10):")
        for row in per_account:
            print(f"  {row[0]} users: {row[1]} accounts")
        
        # Account size vs user count
        cursor.execute("""
            WITH account_data AS (
                SELECT 
                    a.id,
                    CASE 
                        WHEN a.id::integer <= 105 THEN 'small'
                        WHEN a.id::integer <= 135 THEN 'medium'
                        WHEN a.id::integer <= 147 THEN 'large'
                        ELSE 'enterprise'
                    END as size
                FROM raw.app_database_accounts a
            )
            SELECT 
                ad.size,
                COUNT(DISTINCT a.id) as accounts,
                COUNT(u.id) as total_users,
                ROUND(AVG(user_count), 1) as avg_users_per_account
            FROM raw.app_database_accounts a
            JOIN account_data ad ON a.id = ad.id
            JOIN (
                SELECT customer_id, COUNT(*) as user_count
                FROM raw.app_database_users
                GROUP BY customer_id
            ) uc ON a.id = uc.customer_id
            LEFT JOIN raw.app_database_users u ON a.id = u.customer_id
            GROUP BY ad.size
            ORDER BY 
                CASE ad.size
                    WHEN 'small' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'large' THEN 3
                    WHEN 'enterprise' THEN 4
                END
        """)
        size_users = cursor.fetchall()
        
        print("\nUsers by account size:")
        for row in size_users:
            print(f"  {row[0]}: {row[1]} accounts, {row[2]} users (avg {row[3]} per account)")

def main():
    """Main execution function"""
    print("=" * 60)
    print("User Generation for TapFlow Analytics Platform")
    print("Using deterministic configuration")
    print("=" * 60)
    
    # Check if users already exist
    existing_count = db_helper.get_row_count('app_database_users')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} users already exist")
        if should_truncate():
            db_helper.truncate_table('app_database_users')
        else:
            print("Aborting...")
            return
    
    # Generate users
    users = generate_users()
    
    # Save mapping for other generators
    save_user_mapping(users)
    
    # Insert into database
    inserted = insert_users(users)
    
    # Verify
    verify_users()
    
    print(f"\n✅ Successfully generated {inserted} users!")

if __name__ == "__main__":
    main()