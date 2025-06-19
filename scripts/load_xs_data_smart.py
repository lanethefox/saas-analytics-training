#!/usr/bin/env python3
"""
Smart XS data loader that handles schema mismatches gracefully
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import glob
from typing import Dict, List, Any, Set

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

# Base directory for XS test data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'test_xs')

# Mapping of JSON files to table names
FILE_TABLE_MAPPING = {
    # Device/App Database files
    'devices/users.json': 'app_database_users',
    'devices/locations.json': 'app_database_locations',
    'devices/devices.json': 'app_database_devices',
    'devices/subscriptions.json': 'app_database_subscriptions',
    'devices/user_sessions.json': 'app_database_user_sessions',
    'devices/page_views.json': 'app_database_page_views',
    'devices/feature_usage.json': 'app_database_feature_usage',
    
    'stripe/customers.json': 'stripe_customers',
    'stripe/prices.json': 'stripe_prices',
    'stripe/subscriptions.json': 'stripe_subscriptions',
    'stripe/subscription_items.json': 'stripe_subscription_items',
    'stripe/invoices.json': 'stripe_invoices',
    'stripe/charges.json': 'stripe_charges',
    'stripe/payment_intents.json': 'stripe_payment_intents',
    'stripe/events.json': 'stripe_events',
    
    'hubspot/companies.json': 'hubspot_companies',
    'hubspot/contacts.json': 'hubspot_contacts',
    'hubspot/deals.json': 'hubspot_deals',
    'hubspot/engagements.json': 'hubspot_engagements',
    'hubspot/owners.json': 'hubspot_owners',
    'hubspot/tickets.json': 'hubspot_tickets',
    
    'marketing/attribution_touchpoints.json': 'attribution_touchpoints',
    'marketing/facebook_ads_campaigns.json': 'facebook_ads_campaigns',
    'marketing/google_ads_campaigns.json': 'google_ads_campaigns',
    'marketing/google_analytics_sessions.json': 'google_analytics_sessions',
    'marketing/iterable_campaigns.json': 'iterable_campaigns',
    'marketing/linkedin_ads_campaigns.json': 'linkedin_ads_campaigns',
    'marketing/marketing_qualified_leads.json': 'marketing_qualified_leads'
}


class SmartDataLoader:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.table_columns = {}  # Cache of table columns
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ Disconnected from database")
        
    def get_table_columns(self, table_name: str) -> Set[str]:
        """Get list of columns for a table"""
        if table_name not in self.table_columns:
            try:
                self.cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'raw' 
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = {row[0] for row in self.cursor.fetchall()}
                self.table_columns[table_name] = columns
            except Exception as e:
                print(f"❌ Failed to get columns for {table_name}: {e}")
                return set()
                
        return self.table_columns[table_name]
    
    def transform_value(self, value: Any, column_name: str, table_name: str) -> Any:
        """Transform values to match database schema"""
        # Handle timestamps
        if 'created' in column_name or 'timestamp' in column_name or 'date' in column_name:
            if isinstance(value, (int, float)):
                # Convert Unix timestamp to datetime
                try:
                    return datetime.fromtimestamp(value)
                except:
                    return None
            elif isinstance(value, str) and value.endswith('Z'):
                # Remove trailing Z from ISO timestamps
                return value[:-1]
                
        # Handle JSON objects/arrays
        if isinstance(value, (dict, list)):
            return json.dumps(value)
            
        return value
        
    def load_json_file(self, file_path: str, table_name: str):
        """Load a JSON file into the specified table, only using columns that exist"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if not data:
                print(f"⚠️  No data in {file_path}")
                return
                
            # Get columns that exist in the database
            db_columns = self.get_table_columns(table_name)
            if not db_columns:
                print(f"⚠️  Table {table_name} not found or has no columns")
                return
                
            # Handle special case for HubSpot data with properties
            if 'hubspot' in table_name and isinstance(data[0], dict) and 'properties' in data[0]:
                # Flatten HubSpot properties
                flattened_data = []
                for record in data:
                    flat_record = {'id': record.get('id')}
                    if 'properties' in record:
                        flat_record.update(record['properties'])
                    flattened_data.append(flat_record)
                data = flattened_data
                
            # Get columns from first record that exist in database
            data_columns = set(data[0].keys())
            columns_to_use = list(data_columns.intersection(db_columns))
            
            if not columns_to_use:
                print(f"❌ No matching columns between data and table {table_name}")
                print(f"   Data columns: {data_columns}")
                print(f"   DB columns: {db_columns}")
                return
                
            # Prepare INSERT query
            placeholders = ', '.join(['%s'] * len(columns_to_use))
            columns_str = ', '.join(columns_to_use)
            insert_query = f"""
                INSERT INTO raw.{table_name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # Prepare data for insertion
            values = []
            for record in data:
                row = []
                for col in columns_to_use:
                    value = record.get(col)
                    value = self.transform_value(value, col, table_name)
                    row.append(value)
                values.append(tuple(row))
            
            # Execute batch insert
            execute_batch(self.cursor, insert_query, values, page_size=1000)
            self.conn.commit()
            
            print(f"✅ Loaded {len(data)} records into raw.{table_name}")
            
        except Exception as e:
            print(f"❌ Failed to load {file_path}: {e}")
            if hasattr(e, 'pgerror'):
                print(f"   PostgreSQL error: {e.pgerror}")
            self.conn.rollback()
            
    def load_tap_events(self):
        """Load device events from batch files"""
        try:
            event_files = sorted(glob.glob(os.path.join(DATA_DIR, 'devices', 'device_events_batch_*.json')))
            
            if not event_files:
                print("⚠️  No device event files found")
                return
                
            total_events = 0
            
            for file_path in event_files:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if not data:
                    continue
                    
                # Get columns that exist in database
                db_columns = self.get_table_columns('app_database_tap_events')
                data_columns = set(data[0].keys())
                columns_to_use = list(data_columns.intersection(db_columns))
                
                if not columns_to_use:
                    print(f"❌ No matching columns for tap events")
                    continue
                    
                # Prepare INSERT query
                placeholders = ', '.join(['%s'] * len(columns_to_use))
                columns_str = ', '.join(columns_to_use)
                insert_query = f"""
                    INSERT INTO raw.app_database_tap_events ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
                
                # Prepare data
                values = []
                for record in data:
                    row = []
                    for col in columns_to_use:
                        value = record.get(col)
                        value = self.transform_value(value, col, 'app_database_tap_events')
                        row.append(value)
                    values.append(tuple(row))
                
                # Insert data
                execute_batch(self.cursor, insert_query, values, page_size=1000)
                total_events += len(values)
                
                print(f"✅ Loaded {len(values)} events from {os.path.basename(file_path)}")
            
            self.conn.commit()
            print(f"✅ Total device events loaded: {total_events}")
            
        except Exception as e:
            print(f"❌ Failed to load tap events: {e}")
            self.conn.rollback()
            
    def verify_data_loading(self):
        """Verify data loading for tables that exist"""
        print("\n📊 Data Loading Summary:")
        print("-" * 50)
        
        loaded = 0
        total = 0
        
        # Only check tables we tried to load
        tables_to_check = set()
        for file_pattern, table_name in FILE_TABLE_MAPPING.items():
            tables_to_check.add(table_name)
        tables_to_check.add('app_database_tap_events')
        
        for table_name in sorted(tables_to_check):
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
                count = self.cursor.fetchone()[0]
                total += 1
                
                if count > 0:
                    loaded += 1
                    print(f"✅ raw.{table_name}: {count:,} records")
                else:
                    print(f"❌ raw.{table_name}: 0 records")
                    
            except psycopg2.errors.UndefinedTable:
                print(f"⚠️  raw.{table_name}: table does not exist")
            except Exception as e:
                print(f"❌ raw.{table_name}: error - {e}")
                
        print(f"\nTotal: {loaded}/{total} tables loaded with data")
        return loaded, total
        
    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Smart XS Data Loading")
            print("=" * 50)
            
            # Connect to database
            self.connect()
            
            # Load data files
            print("\n📥 Loading data files...")
            
            # Load regular JSON files
            for file_pattern, table_name in FILE_TABLE_MAPPING.items():
                file_path = os.path.join(DATA_DIR, file_pattern)
                if os.path.exists(file_path):
                    self.load_json_file(file_path, table_name)
                else:
                    print(f"⚠️  File not found: {file_path}")
            
            # Load tap events
            self.load_tap_events()
            
            # Verify data loading
            loaded, total = self.verify_data_loading()
            
            print("\n" + "=" * 50)
            if loaded == total:
                print("✅ All data loaded successfully!")
            else:
                print(f"⚠️  Partial load: {loaded}/{total} tables loaded")
                print("   Some tables may have schema mismatches")
                
        except Exception as e:
            print(f"\n❌ Error during data loading: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    loader = SmartDataLoader()
    loader.run()


if __name__ == "__main__":
    main()
