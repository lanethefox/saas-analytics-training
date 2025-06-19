#!/usr/bin/env python3
"""
Comprehensive data loading script for SaaS Platform
Loads all synthetic data into PostgreSQL raw schema tables
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import glob
from typing import Dict, List, Any

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

# Base directory for synthetic data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic')

# Table definitions for each source system
# NOTE: Tables should be created using 00_complete_raw_schema_fixed.sql
# This dict is kept for reference but table creation is skipped
TABLE_DEFINITIONS = {
    # App Database Tables - use proper source_table naming
    'app_database_accounts': '''-- Created by schema file''',
    'app_database_locations': '''-- Created by schema file''',
    'app_database_users': '''-- Created by schema file''',
    'app_database_devices': '''-- Created by schema file''',
    'app_database_subscriptions': '''-- Created by schema file''',
    'app_database_tap_events': '''-- Created by schema file''',
    'app_database_user_sessions': '''-- Created by schema file''',
    'app_database_page_views': '''-- Created by schema file''',
    'app_database_feature_usage': '''-- Created by schema file''',
    'page_views': '''
        CREATE TABLE IF NOT EXISTS raw.page_views (
            id VARCHAR(50) PRIMARY KEY,
            session_id VARCHAR(50),
            user_id INTEGER,
            account_id INTEGER,
            page_url VARCHAR(500),
            page_title VARCHAR(255),
            timestamp TIMESTAMP,
            time_on_page_seconds INTEGER,
            referrer_url VARCHAR(500),
            exit_page BOOLEAN
        )
    ''',
    'feature_usage': '''
        CREATE TABLE IF NOT EXISTS raw.feature_usage (
            id VARCHAR(50) PRIMARY KEY,
            user_id INTEGER,
            account_id INTEGER,
            feature_name VARCHAR(100),
            feature_category VARCHAR(50),
            timestamp TIMESTAMP,
            usage_count INTEGER,
            success BOOLEAN,
            error_message VARCHAR(500)
        )
    ''',
    
    # Stripe Tables
    'stripe_customers': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_customers (
            id VARCHAR(50) PRIMARY KEY,
            account_id INTEGER,
            email VARCHAR(255),
            name VARCHAR(255),
            created TIMESTAMP,
            currency VARCHAR(10),
            default_source VARCHAR(50),
            delinquent BOOLEAN,
            balance INTEGER,
            metadata TEXT
        )
    ''',
    'stripe_prices': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_prices (
            id VARCHAR(50) PRIMARY KEY,
            product VARCHAR(50),
            active BOOLEAN,
            currency VARCHAR(10),
            unit_amount INTEGER,
            type VARCHAR(20),
            recurring_interval VARCHAR(20),
            recurring_interval_count INTEGER,
            nickname VARCHAR(100),
            created TIMESTAMP
        )
    ''',
    'stripe_subscriptions': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_subscriptions (
            id VARCHAR(50) PRIMARY KEY,
            customer VARCHAR(50),
            status VARCHAR(50),
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            created TIMESTAMP,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            cancel_at TIMESTAMP,
            canceled_at TIMESTAMP,
            trial_start TIMESTAMP,
            trial_end TIMESTAMP
        )
    ''',
    'stripe_subscription_items': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_subscription_items (
            id VARCHAR(50) PRIMARY KEY,
            subscription VARCHAR(50),
            price VARCHAR(50),
            quantity INTEGER,
            created TIMESTAMP,
            metadata TEXT
        )
    ''',
    'stripe_invoices': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_invoices (
            id VARCHAR(50) PRIMARY KEY,
            customer VARCHAR(50),
            subscription VARCHAR(50),
            status VARCHAR(50),
            amount_due INTEGER,
            amount_paid INTEGER,
            currency VARCHAR(10),
            created TIMESTAMP,
            due_date TIMESTAMP,
            paid_at TIMESTAMP,
            period_start TIMESTAMP,
            period_end TIMESTAMP
        )
    ''',
    'stripe_charges': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_charges (
            id VARCHAR(50) PRIMARY KEY,
            customer VARCHAR(50),
            invoice VARCHAR(50),
            amount INTEGER,
            currency VARCHAR(10),
            status VARCHAR(50),
            created TIMESTAMP,
            paid BOOLEAN,
            payment_method_details TEXT,
            failure_code VARCHAR(50),
            failure_message TEXT
        )
    ''',
    'stripe_payment_intents': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_payment_intents (
            id VARCHAR(50) PRIMARY KEY,
            customer VARCHAR(50),
            amount INTEGER,
            currency VARCHAR(10),
            status VARCHAR(50),
            created TIMESTAMP,
            payment_method VARCHAR(50),
            confirmation_method VARCHAR(50),
            invoice VARCHAR(50),
            metadata TEXT
        )
    ''',
    'stripe_events': '''
        CREATE TABLE IF NOT EXISTS raw.stripe_events (
            id VARCHAR(50) PRIMARY KEY,
            type VARCHAR(100),
            created TIMESTAMP,
            data TEXT,
            request_id VARCHAR(50),
            idempotency_key VARCHAR(50),
            api_version VARCHAR(20)
        )
    ''',
    
    # HubSpot Tables
    'hubspot_companies': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_companies (
            id INTEGER PRIMARY KEY,
            properties TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            archived BOOLEAN
        )
    ''',
    'hubspot_contacts': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_contacts (
            id INTEGER PRIMARY KEY,
            properties TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            archived BOOLEAN
        )
    ''',
    'hubspot_deals': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_deals (
            id INTEGER PRIMARY KEY,
            properties TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            archived BOOLEAN
        )
    ''',
    'hubspot_engagements': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_engagements (
            id INTEGER PRIMARY KEY,
            type VARCHAR(50),
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            owner_id INTEGER,
            portal_id INTEGER,
            active BOOLEAN,
            metadata TEXT,
            associations TEXT
        )
    ''',
    'hubspot_owners': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_owners (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            user_id INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            archived BOOLEAN
        )
    ''',
    'hubspot_tickets': '''
        CREATE TABLE IF NOT EXISTS raw.hubspot_tickets (
            id INTEGER PRIMARY KEY,
            properties TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            archived BOOLEAN
        )
    ''',
    
    # Marketing Tables
    'attribution_touchpoints': '''
        CREATE TABLE IF NOT EXISTS raw.attribution_touchpoints (
            id VARCHAR(50) PRIMARY KEY,
            contact_id INTEGER,
            account_id INTEGER,
            touchpoint_type VARCHAR(50),
            channel VARCHAR(50),
            campaign_id VARCHAR(50),
            timestamp TIMESTAMP,
            attribution_credit DECIMAL(5,4),
            position_in_journey INTEGER,
            days_to_conversion INTEGER
        )
    ''',
    'facebook_ads_campaigns': '''
        CREATE TABLE IF NOT EXISTS raw.facebook_ads_campaigns (
            campaign_id VARCHAR(50) PRIMARY KEY,
            campaign_name VARCHAR(255),
            status VARCHAR(50),
            objective VARCHAR(50),
            created_time TIMESTAMP,
            start_time TIMESTAMP,
            stop_time TIMESTAMP,
            daily_budget DECIMAL(10,2),
            lifetime_budget DECIMAL(10,2),
            impressions INTEGER,
            clicks INTEGER,
            spend DECIMAL(10,2),
            conversions INTEGER
        )
    ''',
    'google_ads_campaigns': '''
        CREATE TABLE IF NOT EXISTS raw.google_ads_campaigns (
            campaign_id VARCHAR(50) PRIMARY KEY,
            campaign_name VARCHAR(255),
            status VARCHAR(50),
            campaign_type VARCHAR(50),
            start_date DATE,
            end_date DATE,
            budget_amount DECIMAL(10,2),
            impressions INTEGER,
            clicks INTEGER,
            cost DECIMAL(10,2),
            conversions INTEGER,
            conversion_value DECIMAL(10,2)
        )
    ''',
    'google_analytics_sessions': '''
        CREATE TABLE IF NOT EXISTS raw.google_analytics_sessions (
            session_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            session_date DATE,
            source VARCHAR(100),
            medium VARCHAR(50),
            campaign VARCHAR(100),
            device_category VARCHAR(50),
            landing_page VARCHAR(500),
            session_duration INTEGER,
            page_views INTEGER,
            goal_completions INTEGER,
            ecommerce_revenue DECIMAL(10,2)
        )
    ''',
    'iterable_campaigns': '''
        CREATE TABLE IF NOT EXISTS raw.iterable_campaigns (
            campaign_id VARCHAR(50) PRIMARY KEY,
            campaign_name VARCHAR(255),
            campaign_type VARCHAR(50),
            status VARCHAR(50),
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            start_at TIMESTAMP,
            ended_at TIMESTAMP,
            send_size INTEGER,
            message_medium VARCHAR(50),
            labels TEXT
        )
    ''',
    'linkedin_ads_campaigns': '''
        CREATE TABLE IF NOT EXISTS raw.linkedin_ads_campaigns (
            campaign_id VARCHAR(50) PRIMARY KEY,
            campaign_name VARCHAR(255),
            status VARCHAR(50),
            campaign_type VARCHAR(50),
            objective_type VARCHAR(50),
            created_time TIMESTAMP,
            start_date DATE,
            end_date DATE,
            daily_budget DECIMAL(10,2),
            total_budget DECIMAL(10,2),
            impressions INTEGER,
            clicks INTEGER,
            cost DECIMAL(10,2),
            conversions INTEGER
        )
    ''',
    'marketing_qualified_leads': '''
        CREATE TABLE IF NOT EXISTS raw.marketing_qualified_leads (
            lead_id VARCHAR(50) PRIMARY KEY,
            contact_id INTEGER,
            account_id INTEGER,
            mql_date TIMESTAMP,
            mql_score DECIMAL(5,2),
            lead_source VARCHAR(100),
            campaign_id VARCHAR(50),
            conversion_probability DECIMAL(5,4),
            days_to_mql INTEGER,
            engagement_score DECIMAL(5,2)
        )
    '''
}

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


class DataLoader:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
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
        
    def create_schema(self):
        """Create raw schema if it doesn't exist"""
        try:
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
            self.conn.commit()
            print("✅ Raw schema created/verified")
        except Exception as e:
            print(f"❌ Failed to create schema: {e}")
            self.conn.rollback()
            raise
            
    def create_tables(self):
        """Create all tables in the raw schema"""
        for table_name, create_sql in TABLE_DEFINITIONS.items():
            try:
                self.cursor.execute(create_sql)
                self.conn.commit()
                print(f"✅ Created table: raw.{table_name}")
            except Exception as e:
                print(f"❌ Failed to create table {table_name}: {e}")
                self.conn.rollback()
                
    def load_json_file(self, file_path: str, table_name: str):
        """Load a JSON file into the specified table"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if not data:
                print(f"⚠️  No data in {file_path}")
                return
                
            # Get column names from the first record
            columns = list(data[0].keys())
            
            # Prepare INSERT query
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            insert_query = f"""
                INSERT INTO raw.{table_name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # Prepare data for insertion
            values = []
            for record in data:
                row = []
                for col in columns:
                    value = record.get(col)
                    # Convert JSON objects/arrays to strings
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    row.append(value)
                values.append(tuple(row))
            
            # Execute batch insert
            execute_batch(self.cursor, insert_query, values, page_size=1000)
            self.conn.commit()
            
            print(f"✅ Loaded {len(data)} records into raw.{table_name}")
            
        except Exception as e:
            print(f"❌ Failed to load {file_path}: {e}")
            self.conn.rollback()
            
    def load_tap_events(self):
        """Load device events from multiple batch files into app_database_tap_events"""
        try:
            event_files = glob.glob(os.path.join(DATA_DIR, 'devices', 'device_events_batch_*.json'))
            total_events = 0
            
            # Limit to first 10 files for XS scale testing
            event_files = sorted(event_files)[:10]  
            
            for file_path in event_files:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if not data:
                    continue
                
                # Get column names from the first record (dynamic loading)
                columns = list(data[0].keys())
                
                # Prepare INSERT query for app_database_tap_events
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                insert_query = f"""
                    INSERT INTO raw.app_database_tap_events ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
                
                # Prepare data for insertion
                values = []
                for record in data:
                    row = []
                    for col in columns:
                        value = record.get(col)
                        # Convert metrics dict to JSON string for JSONB column
                        if col == 'metrics' and isinstance(value, dict):
                            value = json.dumps(value)
                        elif col == 'timestamp' and isinstance(value, str):
                            # Ensure timestamp format is correct
                            value = value
                        row.append(value)
                    values.append(tuple(row))
                
                # Insert data in batches
                execute_batch(self.cursor, insert_query, values, page_size=1000)
                total_events += len(values)
                
                print(f"✅ Loaded {len(values)} events from {os.path.basename(file_path)}")
            
            self.conn.commit()
            print(f"✅ Total device events loaded: {total_events}")
            
        except Exception as e:
            print(f"❌ Failed to load tap events: {e}")
            if hasattr(e, 'pgerror'):
                print(f"   PostgreSQL error: {e.pgerror}")
            self.conn.rollback()
            
    def verify_data_loading(self):
        """Verify that all tables have been loaded with data"""
        print("\n📊 Data Loading Verification:")
        print("-" * 50)
        
        total_tables = 0
        loaded_tables = 0
        
        for table_name in TABLE_DEFINITIONS.keys():
            self.cursor.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
            count = self.cursor.fetchone()[0]
            total_tables += 1
            
            if count > 0:
                loaded_tables += 1
                print(f"✅ raw.{table_name}: {count:,} records")
            else:
                print(f"❌ raw.{table_name}: 0 records")
                
        print("-" * 50)
        print(f"📈 Progress: {loaded_tables}/{total_tables} tables loaded ({loaded_tables/total_tables*100:.1f}%)")
        
        return loaded_tables, total_tables
        
    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting SaaS Platform Data Loading")
            print("=" * 50)
            
            # Connect to database
            self.connect()
            
            # Create schema
            self.create_schema()
            
            # Tables should already exist from schema file - skip creation
            print("\n📋 Using existing tables (created by schema file)...")
            
            # Load data files
            print("\n📥 Loading data files...")
            
            # Load regular JSON files
            for file_pattern, table_name in FILE_TABLE_MAPPING.items():
                file_path = os.path.join(DATA_DIR, file_pattern)
                if os.path.exists(file_path):
                    self.load_json_file(file_path, table_name)
                else:
                    print(f"⚠️  File not found: {file_path}")
            
            # Load tap events (special case with multiple files)
            self.load_tap_events()
            
            # Verify data loading
            loaded, total = self.verify_data_loading()
            
            print("\n" + "=" * 50)
            if loaded == total:
                print("✅ Stage 1 Complete! All source data loaded successfully.")
            else:
                print(f"⚠️  Stage 1 Incomplete: {loaded}/{total} tables loaded")
                print("   Please generate missing data files and run again.")
                
        except Exception as e:
            print(f"\n❌ Error during data loading: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    loader = DataLoader()
    loader.run()


if __name__ == "__main__":
    main()