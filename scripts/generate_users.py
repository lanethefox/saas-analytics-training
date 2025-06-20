#!/usr/bin/env python3
"""
Generate synthetic users data for the bar management SaaS platform.

This module creates realistic user data with:
- 2-10 users per account based on tier
- Role distribution (Admin 10%, Manager 30%, Staff 60%)
- Email patterns matching company domains
- Login frequency patterns by role
- Permissions JSON based on roles
"""

import sys
import os
import random
import json
from datetime import datetime, timedelta
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.environment_config import current_env

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# User configuration
USER_ROLES = [
    ('admin', 0.10),
    ('manager', 0.30),
    ('staff', 0.60)
]

# Permissions by role
ROLE_PERMISSIONS = {
    'admin': {
        'can_manage_users': True,
        'can_manage_billing': True,
        'can_view_reports': True,
        'can_manage_devices': True,
        'can_manage_products': True,
        'can_export_data': True
    },
    'manager': {
        'can_manage_users': False,
        'can_manage_billing': False,
        'can_view_reports': True,
        'can_manage_devices': True,
        'can_manage_products': True,
        'can_export_data': True
    },
    'staff': {
        'can_manage_users': False,
        'can_manage_billing': False,
        'can_view_reports': False,
        'can_manage_devices': False,
        'can_manage_products': False,
        'can_export_data': False
    }
}
def weighted_choice(choices):
    """Make a weighted random choice"""
    population = [item[0] for item in choices]
    weights = [item[1] for item in choices]
    return random.choices(population, weights=weights)[0]

def load_accounts():
    """Load generated accounts from JSON file"""
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
    
    return accounts

def get_users_per_account(tier):
    """Get number of users based on account tier"""
    if tier == 'basic':
        return random.randint(2, 4)
    elif tier == 'pro':
        return random.randint(3, 7)
    else:  # enterprise
        return random.randint(5, 10)

def generate_email(first_name, last_name, domain):
    """Generate email address with various patterns"""
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}@{domain}",
        f"{first_name[0].lower()}{last_name.lower()}@{domain}",
        f"{first_name.lower()}{last_name[0].lower()}@{domain}",
        f"{first_name.lower()}_{last_name.lower()}@{domain}",
    ]
    return random.choice(patterns)

def get_login_frequency(role):
    """Get average days between logins based on role"""
    if role == 'admin':
        return random.uniform(1, 3)  # Admins login frequently
    elif role == 'manager':
        return random.uniform(1, 5)  # Managers login regularly
    else:  # staff
        return random.uniform(2, 7)  # Staff login less frequently

def generate_users(accounts, total_users):
    """Generate synthetic user data"""
    users = []
    user_id = 1
    
    print(f"Generating {total_users:,} users for {len(accounts):,} accounts...")
    
    # Calculate users per account
    users_needed = total_users
    account_users = []
    
    for account in accounts:
        num_users = get_users_per_account(account['subscription_tier'])
        account_users.append((account, num_users))
        users_needed -= num_users
    
    # Adjust if we need more users
    while users_needed > 0:
        idx = random.randint(0, len(account_users) - 1)
        account, current_count = account_users[idx]
        if current_count < 10:  # Max 10 users per account
            account_users[idx] = (account, current_count + 1)
            users_needed -= 1
    
    # Adjust if we have too many users
    while users_needed < 0:
        idx = random.randint(0, len(account_users) - 1)
        account, current_count = account_users[idx]
        if current_count > 2:  # Min 2 users per account
            account_users[idx] = (account, current_count - 1)
            users_needed += 1
    
    # Generate users for each account
    for account, num_users in account_users:
        # First user is always admin
        roles = ['admin'] + [weighted_choice(USER_ROLES) for _ in range(num_users - 1)]
        
        # Extract domain from primary contact email
        domain = account['primary_contact_email'].split('@')[1]
        
        for i, role in enumerate(roles):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Calculate dates
            created_at = account['created_at'] + timedelta(days=random.randint(0, 30))
            last_login_freq = get_login_frequency(role)
            days_since_last_login = int(random.expovariate(1/last_login_freq))
            last_login = datetime.now() - timedelta(days=days_since_last_login)
            
            user = {
                'id': user_id,
                'account_id': account['id'],
                'email': generate_email(first_name, last_name, domain),
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'permissions': json.dumps(ROLE_PERMISSIONS[role]),
                'is_active': account['is_active'] and random.random() < 0.95,
                'phone': fake.phone_number(),
                'last_login_at': last_login if last_login > created_at else created_at,
                'login_count': int(random.expovariate(1/20)),  # Average 20 logins
                'created_at': created_at,
                'updated_at': created_at + timedelta(days=random.randint(0, 90))
            }
            
            users.append(user)
            user_id += 1
    
    return users

def insert_users(users):
    """Insert users into the database"""
    print(f"\nInserting {len(users):,} users into database...")
    
    # Check table structure
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_users'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\nTable structure for raw.app_database_users:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    
    # Map our generated data to actual table columns
    mapped_users = []
    for user in users:
        mapped = {
            'id': user['id'],
            'customer_id': user['account_id'],  # customer_id maps to account_id
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
    with open(mapping_file, 'w') as f:
        # Convert datetime objects to strings
        serializable_users = []
        for user in users:
            user_copy = user.copy()
            user_copy['created_at'] = user_copy['created_at'].isoformat()
            user_copy['updated_at'] = user_copy['updated_at'].isoformat()
            user_copy['last_login_at'] = user_copy['last_login_at'].isoformat()
            serializable_users.append(user_copy)
        
        json.dump(serializable_users, f, indent=2)
    
    print(f"\n✓ Saved user mapping to {mapping_file}")

def verify_users():
    """Verify the inserted users"""
    count = db_helper.get_row_count('app_database_users')
    print(f"\n✓ Verification: {count:,} users in database")
    
    # Show sample data
    with db_helper.config.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT u.*, a.name as account_name
            FROM raw.app_database_users u
            JOIN raw.app_database_accounts a ON u.customer_id = a.id
            ORDER BY u.created_at DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\nSample users (most recent):")
        for user in samples:
            print(f"  {user['first_name']} {user['last_name']} ({user['role']}) - {user['email']} - Account: {user['account_name']}")
    
    # Show role distribution
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT role, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM raw.app_database_users
            GROUP BY role
            ORDER BY count DESC
        """)
        dist = cursor.fetchall()
        
        print("\nRole distribution:")
        for row in dist:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")

def main():
    """Main execution function"""
    print("=" * 60)
    print("User Generation for Bar Management SaaS Platform")
    print(f"Environment: {current_env.name}")
    print("=" * 60)
    
    # Check if users already exist
    existing_count = db_helper.get_row_count('app_database_users')
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count:,} users already exist")
        response = input("Do you want to truncate and regenerate? (y/N): ")
        if response.lower() == 'y':
            db_helper.truncate_table('app_database_users')
        else:
            print("Aborting...")
            return
    
    # Load accounts
    accounts = load_accounts()
    print(f"\n✓ Loaded {len(accounts):,} accounts")
    
    # Generate users
    users = generate_users(accounts, current_env.users)
    
    # Save mapping for other generators
    save_user_mapping(users)
    
    # Insert into database
    inserted = insert_users(users)
    
    # Verify
    verify_users()
    
    print(f"\n✅ Successfully generated {inserted:,} users!")

if __name__ == "__main__":
    main()
