#!/usr/bin/env python3
"""
Robust Data Generation Script for B2B SaaS Analytics Platform
Ensures schemas exist and handles errors gracefully
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import uuid
import json

# Check for required dependencies
try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("Error: psycopg2 is required. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Configuration
SIZES = {
    'tiny': {
        'accounts': 100,
        'locations_per_account': (1, 3),
        'devices_per_location': (1, 5),
        'users_per_account': (1, 5),
        'events_per_device_per_day': 100,
        'days_of_history': 30,
        'description': 'Quick testing (1-2 min)'
    },
    'small': {
        'accounts': 1000,
        'locations_per_account': (1, 5),
        'devices_per_location': (2, 10),
        'users_per_account': (2, 10),
        'events_per_device_per_day': 500,
        'days_of_history': 90,
        'description': 'Exercises & demos (5 min)'
    },
    'medium': {
        'accounts': 10000,
        'locations_per_account': (1, 10),
        'devices_per_location': (3, 15),
        'users_per_account': (3, 20),
        'events_per_device_per_day': 1000,
        'days_of_history': 180,
        'description': 'Projects (15 min)'
    },
    'large': {
        'accounts': 40000,
        'locations_per_account': (1, 20),
        'devices_per_location': (5, 30),
        'users_per_account': (5, 50),
        'events_per_device_per_day': 2000,
        'days_of_history': 365,
        'description': 'Full platform (30-45 min)'
    }
}

# Industries and company patterns
INDUSTRIES = ['Technology', 'Healthcare', 'Retail', 'Manufacturing', 'Finance', 
              'Education', 'Hospitality', 'Real Estate', 'Transportation', 'Energy']

COMPANY_PREFIXES = ['Acme', 'Global', 'Premier', 'Elite', 'Advanced', 'Dynamic',
                    'Strategic', 'Innovative', 'Digital', 'Smart', 'Future', 'Next']

COMPANY_SUFFIXES = ['Corp', 'Inc', 'LLC', 'Group', 'Holdings', 'Partners',
                    'Solutions', 'Systems', 'Technologies', 'Enterprises']

# Device types and statuses
DEVICE_TYPES = ['beer_tap', 'wine_tap', 'cocktail_dispenser', 'water_tap', 'coffee_tap']
DEVICE_STATUSES = ['active', 'inactive', 'maintenance']

# Subscription plans
SUBSCRIPTION_PLANS = ['starter', 'professional', 'enterprise']
PLAN_PRICES = {'starter': 299, 'professional': 999, 'enterprise': 2999}

# US States for location generation
US_STATES = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
             'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI']


class EducationalDataGenerator:
    def __init__(self, connection_params: Dict[str, str]):
        """Initialize the data generator with database connection parameters"""
        self.conn_params = connection_params
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
            print("✓ Connected to database")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def ensure_schema_exists(self):
        """Ensure the raw schema exists"""
        print("🔧 Ensuring database schema exists...")
        try:
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
            self.conn.commit()
            print("✓ Schema 'raw' is ready")
            return True
        except Exception as e:
            print(f"✗ Failed to create schema: {e}")
            return False
    
    def check_tables_exist(self) -> bool:
        """Check if required tables exist"""
        required_tables = [
            'app_database_accounts',
            'app_database_locations',
            'app_database_devices',
            'app_database_users',
            'app_database_subscriptions'
        ]
        
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw' 
            AND table_name = ANY(%s)
        """, (required_tables,))
        
        existing_tables = {row[0] for row in self.cursor.fetchall()}
        missing_tables = set(required_tables) - existing_tables
        
        if missing_tables:
            print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            print("   Run database initialization first or check docker-compose logs")
            return False
        
        print("✓ All required tables exist")
        return True
    
    def clear_existing_data(self):
        """Clear existing data from core tables only"""
        print("🧹 Clearing existing data...")
        
        # Only clear core tables that we'll be populating
        core_tables = [
            'raw.app_database_subscriptions',
            'raw.app_database_devices',
            'raw.app_database_users',
            'raw.app_database_locations',
            'raw.app_database_accounts'
        ]
        
        for table in core_tables:
            try:
                self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"  ✓ Cleared {table}")
            except Exception as e:
                print(f"  ⚠️  Could not clear {table}: {str(e)[:50]}")
        
        self.conn.commit()
        print("✓ Data cleared")
    
    def generate_company_name(self) -> str:
        """Generate a realistic company name"""
        prefix = random.choice(COMPANY_PREFIXES)
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{prefix} {suffix}"
    
    def generate_accounts(self, count: int) -> List[Dict]:
        """Generate account data"""
        print(f"\n🏭 Generating {count} accounts...")
        accounts = []
        
        for i in range(count):
            account_id = f"acc_{uuid.uuid4().hex[:8]}"
            created_date = datetime.now() - timedelta(days=random.randint(0, 1095))
            
            account = {
                'id': account_id,
                'name': self.generate_company_name(),
                'industry': random.choice(INDUSTRIES),
                'employee_count': random.randint(10, 5000),
                'annual_revenue': random.randint(1000000, 1000000000),
                'created_at': created_date,
                'updated_at': created_date + timedelta(days=random.randint(0, 30)),
                'website': f"https://www.{account_id.replace('_', '-')}.com",
                'status': random.choices(['active', 'inactive', 'prospect'], weights=[80, 15, 5])[0]
            }
            accounts.append(account)
            
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1} accounts...")
        
        print(f"✓ Generated {len(accounts)} accounts")
        return accounts
    
    def generate_locations(self, accounts: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate location data for accounts"""
        print(f"\n📍 Generating locations...")
        locations = []
        
        for account in accounts:
            num_locations = random.randint(*size_config['locations_per_account'])
            
            for j in range(num_locations):
                location_id = f"loc_{uuid.uuid4().hex[:8]}"
                
                location = {
                    'id': location_id,
                    'customer_id': account['id'],
                    'name': f"{account['name']} - Location {j+1}",
                    'address': f"{random.randint(100, 9999)} Main St",
                    'city': f"City_{random.randint(1, 100)}",
                    'state': random.choice(US_STATES),
                    'zip_code': f"{random.randint(10000, 99999):05d}",
                    'latitude': round(random.uniform(25.0, 48.0), 6),
                    'longitude': round(random.uniform(-125.0, -70.0), 6),
                    'location_type': random.choice(['bar', 'restaurant', 'hotel', 'venue', 'retail']),
                    'capacity': random.randint(50, 500),
                    'created_at': account['created_at'] + timedelta(days=random.randint(0, 30)),
                    'is_active': random.choices([True, False], weights=[85, 15])[0]
                }
                locations.append(location)
        
        print(f"✓ Generated {len(locations)} locations")
        return locations
    
    def generate_devices(self, locations: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate device data for locations"""
        print(f"\n🔧 Generating devices...")
        devices = []
        
        for location in locations:
            if not location['is_active']:
                # Inactive locations have fewer devices
                num_devices = random.randint(0, 2)
            else:
                num_devices = random.randint(*size_config['devices_per_location'])
            
            for k in range(num_devices):
                device_id = f"dev_{uuid.uuid4().hex[:8]}"
                install_date = location['created_at'] + timedelta(days=random.randint(0, 60))
                
                device = {
                    'id': device_id,
                    'location_id': location['id'],
                    'device_type': random.choice(DEVICE_TYPES),
                    'serial_number': f"SN{random.randint(100000, 999999)}",
                    'model': f"Model_{random.choice(['X', 'Y', 'Z'])}{random.randint(100, 999)}",
                    'firmware_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                    'installation_date': install_date,
                    'last_maintenance_date': install_date + timedelta(days=random.randint(30, 365)),
                    'status': random.choices(DEVICE_STATUSES, weights=[75, 20, 5])[0],
                    'is_online': random.choices([True, False], weights=[80, 20])[0]
                }
                devices.append(device)
        
        print(f"✓ Generated {len(devices)} devices")
        return devices
    
    def generate_users(self, accounts: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate user data for accounts"""
        print(f"\n👤 Generating users...")
        users = []
        
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa',
                       'James', 'Mary', 'William', 'Patricia', 'Richard', 'Jennifer']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                      'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez']
        
        for account in accounts:
            num_users = random.randint(*size_config['users_per_account'])
            
            # Ensure at least one admin per account
            roles = ['admin'] + [random.choice(['admin', 'manager', 'user', 'viewer']) 
                                for _ in range(num_users - 1)]
            random.shuffle(roles)
            
            for i in range(num_users):
                user_id = f"usr_{uuid.uuid4().hex[:8]}"
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                
                user = {
                    'id': user_id,
                    'customer_id': account['id'],
                    'email': f"{first_name.lower()}.{last_name.lower()}@{account['id'].replace('_', '-')}.com",
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': roles[i],
                    'created_at': account['created_at'] + timedelta(days=random.randint(0, 30)),
                    'last_login_at': datetime.now() - timedelta(days=random.randint(0, 30)),
                    'is_active': random.choices([True, False], weights=[85, 15])[0]
                }
                users.append(user)
        
        print(f"✓ Generated {len(users)} users")
        return users
    
    def generate_subscriptions(self, accounts: List[Dict]) -> List[Dict]:
        """Generate subscription data for accounts"""
        print(f"\n💳 Generating subscriptions...")
        subscriptions = []
        
        for account in accounts:
            if account['status'] != 'active':
                continue
                
            sub_id = f"sub_{uuid.uuid4().hex[:8]}"
            plan = random.choice(SUBSCRIPTION_PLANS)
            start_date = account['created_at'] + timedelta(days=random.randint(0, 30))
            
            subscription = {
                'id': sub_id,
                'customer_id': account['id'],
                'plan_name': plan,
                'status': random.choices(['active', 'cancelled', 'past_due'], weights=[85, 10, 5])[0],
                'monthly_amount': PLAN_PRICES[plan],
                'start_date': start_date,
                'created_at': start_date,
                'updated_at': start_date + timedelta(days=random.randint(0, 30))
            }
            
            # Add end_date for cancelled subscriptions
            if subscription['status'] == 'cancelled':
                subscription['end_date'] = start_date + timedelta(days=random.randint(30, 365))
            else:
                subscription['end_date'] = None
                
            subscriptions.append(subscription)
        
        print(f"✓ Generated {len(subscriptions)} subscriptions")
        return subscriptions
    
    def insert_data(self, table: str, data: List[Dict], batch_size: int = 1000):
        """Insert data into specified table in batches"""
        if not data:
            return
        
        total_records = len(data)
        print(f"  Loading {total_records} records into {table}...")
        
        # Get columns from first record
        columns = list(data[0].keys())
        
        # Process in batches
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            values = [[row[col] for col in columns] for row in batch]
            
            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
                ON CONFLICT (id) DO NOTHING
            """
            
            try:
                execute_batch(self.cursor, query, values, page_size=100)
                if (i + batch_size) % 10000 == 0:
                    print(f"    Loaded {min(i + batch_size, total_records)}/{total_records} records...")
            except Exception as e:
                print(f"    ⚠️  Error inserting batch: {str(e)[:100]}")
                # Try to continue with next batch
        
        self.conn.commit()
        print(f"  ✓ Completed loading {table}")
    
    def generate_summary_stats(self):
        """Generate and display summary statistics"""
        print("\n📊 Generating summary statistics...")
        
        queries = [
            ("Accounts", "SELECT COUNT(*) FROM raw.app_database_accounts"),
            ("Active Accounts", "SELECT COUNT(*) FROM raw.app_database_accounts WHERE status = 'active'"),
            ("Locations", "SELECT COUNT(*) FROM raw.app_database_locations"),
            ("Devices", "SELECT COUNT(*) FROM raw.app_database_devices"),
            ("Online Devices", "SELECT COUNT(*) FROM raw.app_database_devices WHERE is_online = true"),
            ("Users", "SELECT COUNT(*) FROM raw.app_database_users"),
            ("Subscriptions", "SELECT COUNT(*) FROM raw.app_database_subscriptions")
        ]
        
        print("\n  Summary:")
        print("  " + "-" * 40)
        
        for label, query in queries:
            try:
                self.cursor.execute(query)
                count = self.cursor.fetchone()[0]
                print(f"  {label:<20}: {count:,}")
            except Exception as e:
                print(f"  {label:<20}: Error - {str(e)[:30]}")
        
        print("  " + "-" * 40)
    
    def generate_and_load_data(self, size: str):
        """Generate and load all data for specified size"""
        config = SIZES[size]
        print(f"\n📊 Generating {size.upper()} dataset")
        print(f"   {config['description']}")
        print("=" * 60)
        
        # Ensure schema exists
        if not self.ensure_schema_exists():
            return False
        
        # Check if tables exist
        if not self.check_tables_exist():
            return False
        
        # Clear existing data
        self.clear_existing_data()
        
        # Generate data
        start_time = datetime.now()
        
        accounts = self.generate_accounts(config['accounts'])
        locations = self.generate_locations(accounts, config)
        devices = self.generate_devices(locations, config)
        users = self.generate_users(accounts, config)
        subscriptions = self.generate_subscriptions(accounts)
        
        # Insert data
        print("\n💾 Loading data into database...")
        self.insert_data('raw.app_database_accounts', accounts)
        self.insert_data('raw.app_database_locations', locations)
        self.insert_data('raw.app_database_devices', devices)
        self.insert_data('raw.app_database_users', users)
        self.insert_data('raw.app_database_subscriptions', subscriptions)
        
        # Generate summary stats
        self.generate_summary_stats()
        
        # Calculate time taken
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ Data generation complete in {duration:.1f} seconds!")
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic data for B2B SaaS Analytics Platform')
    parser.add_argument('--size', choices=['tiny', 'small', 'medium', 'large'], 
                        default='small', help='Dataset size to generate')
    parser.add_argument('--host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, help='PostgreSQL port')
    parser.add_argument('--database', default='saas_platform_dev', help='Database name')
    parser.add_argument('--user', default='saas_user', help='Database user')
    parser.add_argument('--password', default='saas_secure_password_2024', help='Database password')
    
    args = parser.parse_args()
    
    # Connection parameters
    conn_params = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    # Print configuration
    print("🚀 B2B SaaS Analytics Platform - Data Generator")
    print("=" * 60)
    print(f"Database: {args.user}@{args.host}:{args.port}/{args.database}")
    print(f"Dataset size: {args.size}")
    
    # Create generator
    generator = EducationalDataGenerator(conn_params)
    
    try:
        # Connect to database
        if not generator.connect():
            sys.exit(1)
        
        # Generate and load data
        success = generator.generate_and_load_data(args.size)
        
        if success:
            print("\n🎉 Success! Your educational platform is ready with sample data.")
            print("\n📚 Next steps:")
            print("   1. Run dbt transformations: docker-compose exec dbt bash -c 'cd /opt/dbt_project && dbt run --profiles-dir .'")
            print("   2. Access Superset at http://localhost:8088")
            print("   3. Explore the data in Jupyter at http://localhost:8888")
        else:
            print("\n❌ Data generation failed. Check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        generator.disconnect()


if __name__ == '__main__':
    main()