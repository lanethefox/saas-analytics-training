#!/usr/bin/env python3
"""
Portable Data Generation Script for B2B SaaS Analytics Platform
Generates synthetic data for educational use with configurable sizes
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import uuid

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
        'description': 'Quick demos (1 min)'
    },
    'small': {
        'accounts': 1000,
        'locations_per_account': (1, 5),
        'devices_per_location': (2, 10),
        'users_per_account': (2, 10),
        'description': 'Exercises (5 min)'
    },
    'medium': {
        'accounts': 10000,
        'locations_per_account': (1, 10),
        'devices_per_location': (3, 15),
        'users_per_account': (3, 20),
        'description': 'Projects (15 min)'
    },
    'large': {
        'accounts': 40000,
        'locations_per_account': (1, 20),
        'devices_per_location': (5, 30),
        'users_per_account': (5, 50),
        'description': 'Full platform (30 min)'
    }
}

# Industries and company name patterns
INDUSTRIES = ['Technology', 'Healthcare', 'Retail', 'Manufacturing', 'Finance', 
              'Education', 'Hospitality', 'Real Estate', 'Transportation', 'Energy']

COMPANY_PREFIXES = ['Acme', 'Global', 'Premier', 'Elite', 'Advanced', 'Dynamic',
                    'Strategic', 'Innovative', 'Digital', 'Smart', 'Future', 'Next']

COMPANY_SUFFIXES = ['Corp', 'Inc', 'LLC', 'Group', 'Holdings', 'Partners',
                    'Solutions', 'Systems', 'Technologies', 'Enterprises']

# Device types and statuses
DEVICE_TYPES = ['beer_tap', 'wine_tap', 'cocktail_dispenser', 'water_tap', 'coffee_tap']
DEVICE_STATUSES = ['active', 'inactive', 'maintenance']

# US States for location generation
US_STATES = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
             'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI']


class DataGenerator:
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
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def clear_existing_data(self):
        """Clear existing data from all tables"""
        print("🧹 Clearing existing data...")
        
        tables = [
            'raw.stripe_database_subscription_items',
            'raw.stripe_database_subscriptions',
            'raw.stripe_database_invoices',
            'raw.stripe_database_charges',
            'raw.stripe_database_events',
            'raw.stripe_database_prices',
            'raw.stripe_database_customers',
            'raw.sensor_database_events',
            'raw.device_database_maintenance_logs',
            'raw.app_database_campaign_participants',
            'raw.app_database_campaigns',
            'raw.app_database_feature_usage',
            'raw.app_database_features',
            'raw.app_database_user_activities',
            'raw.app_database_devices',
            'raw.app_database_users',
            'raw.app_database_locations',
            'raw.app_database_accounts'
        ]
        
        for table in tables:
            try:
                self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            except Exception as e:
                print(f"  Warning: Could not truncate {table}: {e}")
        
        self.conn.commit()
        print("✓ Data cleared")
    
    def generate_company_name(self) -> str:
        """Generate a realistic company name"""
        prefix = random.choice(COMPANY_PREFIXES)
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{prefix} {suffix}"
    
    def generate_accounts(self, count: int) -> List[Dict]:
        """Generate account data"""
        print(f"🏭 Generating {count} accounts...")
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
                'website': f"https://www.{account_id}.com",
                'status': random.choice(['active', 'inactive', 'prospect'])
            }
            accounts.append(account)
            
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1} accounts...")
        
        return accounts
    
    def generate_locations(self, accounts: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate location data for accounts"""
        print("📍 Generating locations...")
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
                    'zip_code': f"{random.randint(10000, 99999)}",
                    'latitude': round(random.uniform(25.0, 48.0), 6),
                    'longitude': round(random.uniform(-125.0, -70.0), 6),
                    'location_type': random.choice(['bar', 'restaurant', 'hotel', 'venue', 'retail']),
                    'capacity': random.randint(50, 500),
                    'created_at': account['created_at'] + timedelta(days=random.randint(0, 30)),
                    'is_active': random.choice([True, True, True, False])  # 75% active
                }
                locations.append(location)
        
        print(f"✓ Generated {len(locations)} locations")
        return locations
    
    def generate_devices(self, locations: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate device data for locations"""
        print("🔧 Generating devices...")
        devices = []
        
        for location in locations:
            if not location['is_active']:
                continue
                
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
                    'status': random.choice(DEVICE_STATUSES),
                    'is_online': random.choice([True, True, True, False])  # 75% online
                }
                devices.append(device)
        
        print(f"✓ Generated {len(devices)} devices")
        return devices
    
    def generate_users(self, accounts: List[Dict], size_config: Dict) -> List[Dict]:
        """Generate user data for accounts"""
        print("👤 Generating users...")
        users = []
        
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller']
        
        for account in accounts:
            num_users = random.randint(*size_config['users_per_account'])
            
            for i in range(num_users):
                user_id = f"usr_{uuid.uuid4().hex[:8]}"
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                
                user = {
                    'id': user_id,
                    'customer_id': account['id'],
                    'email': f"{first_name.lower()}.{last_name.lower()}@{account['id']}.com",
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': random.choice(['admin', 'manager', 'user', 'viewer']),
                    'created_at': account['created_at'] + timedelta(days=random.randint(0, 30)),
                    'last_login_at': datetime.now() - timedelta(days=random.randint(0, 30)),
                    'is_active': random.choice([True, True, True, False])  # 75% active
                }
                users.append(user)
        
        print(f"✓ Generated {len(users)} users")
        return users
    
    def insert_data(self, table: str, data: List[Dict]):
        """Insert data into specified table"""
        if not data:
            return
        
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
        """
        
        execute_batch(self.cursor, query, values, page_size=1000)
        self.conn.commit()
    
    def generate_and_load_data(self, size: str):
        """Generate and load all data for specified size"""
        config = SIZES[size]
        print(f"\n📊 Generating {size} dataset: {config['description']}")
        print("=" * 50)
        
        # Generate data
        accounts = self.generate_accounts(config['accounts'])
        locations = self.generate_locations(accounts, config)
        devices = self.generate_devices(locations, config)
        users = self.generate_users(accounts, config)
        
        # Insert data
        print("\n💾 Loading data into database...")
        self.insert_data('raw.app_database_accounts', accounts)
        self.insert_data('raw.app_database_locations', locations)
        self.insert_data('raw.app_database_devices', devices)
        self.insert_data('raw.app_database_users', users)
        
        # Generate some basic metrics
        print("\n📈 Generating initial metrics...")
        self.generate_basic_metrics()
        
        print("\n✅ Data generation complete!")
        print(f"   Accounts: {len(accounts):,}")
        print(f"   Locations: {len(locations):,}")
        print(f"   Devices: {len(devices):,}")
        print(f"   Users: {len(users):,}")
    
    def generate_basic_metrics(self):
        """Generate some basic subscription and activity metrics"""
        # Create basic subscriptions for active accounts
        self.cursor.execute("""
            INSERT INTO raw.stripe_database_customers (id, customer_id, email, created_at)
            SELECT 
                'cus_' || substr(md5(random()::text), 1, 14),
                a.id,
                'billing@' || a.id || '.com',
                a.created_at
            FROM raw.app_database_accounts a
            WHERE a.status = 'active'
            ON CONFLICT (id) DO NOTHING
        """)
        
        # Create basic subscriptions
        self.cursor.execute("""
            INSERT INTO raw.stripe_database_subscriptions 
                (id, customer_id, status, current_period_start, current_period_end, created_at)
            SELECT 
                'sub_' || substr(md5(random()::text), 1, 14),
                c.id,
                'active',
                date_trunc('month', CURRENT_DATE),
                date_trunc('month', CURRENT_DATE) + interval '1 month',
                c.created_at
            FROM raw.stripe_database_customers c
            ON CONFLICT (id) DO NOTHING
        """)
        
        self.conn.commit()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Generate synthetic data for B2B SaaS Analytics Platform'
    )
    parser.add_argument(
        '--size',
        choices=['tiny', 'small', 'medium', 'large'],
        default='small',
        help='Dataset size to generate'
    )
    parser.add_argument(
        '--host',
        default=os.environ.get('DB_HOST', 'localhost'),
        help='Database host'
    )
    parser.add_argument(
        '--port',
        default=os.environ.get('DB_PORT', '5432'),
        help='Database port'
    )
    parser.add_argument(
        '--database',
        default=os.environ.get('POSTGRES_DB', 'saas_platform_dev'),
        help='Database name'
    )
    parser.add_argument(
        '--user',
        default=os.environ.get('POSTGRES_USER', 'saas_user'),
        help='Database user'
    )
    parser.add_argument(
        '--password',
        default=os.environ.get('POSTGRES_PASSWORD', 'saas_secure_password_2024'),
        help='Database password'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before generating'
    )
    
    args = parser.parse_args()
    
    # Connection parameters
    conn_params = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    # Create generator and run
    generator = DataGenerator(conn_params)
    
    try:
        generator.connect()
        
        if args.clear:
            generator.clear_existing_data()
        
        generator.generate_and_load_data(args.size)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        generator.disconnect()


if __name__ == '__main__':
    main()