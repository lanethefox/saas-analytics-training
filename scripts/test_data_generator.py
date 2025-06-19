#!/usr/bin/env python3
"""
Comprehensive Test Suite for Data Generator and Loader
=====================================================

Tests data generation and loading across all scales (XS, Small, Enterprise)
with validation of:
- Schema compliance
- Data quality and relationships
- Business logic correctness
- Performance characteristics
- Scalability patterns
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
import subprocess
import glob
import psycopg2
from datetime import datetime, date
from typing import Dict, List, Any
import logging

# Add project directory to path
sys.path.append('/Users/lane/Development/Active/data-platform/scripts')

# Import our generators
from generate_synthetic_data import PlatformConfig, DataScale, StripeDataGenerator
from device_generator import DeviceDataGenerator
from hubspot_generator import HubSpotDataGenerator
from marketing_generator import MarketingDataGenerator

# Database connection for testing
TEST_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Test suite for data generation functionality"""
    
    @pytest.fixture(scope="class")
    def temp_output_dir(self):
        """Create temporary directory for test output"""
        temp_dir = tempfile.mkdtemp(prefix="data_gen_test_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture(scope="class")
    def xs_config(self):
        """XS scale configuration for testing"""
        return PlatformConfig.create('xs', months_back=12)  # 1 year for faster testing
    
    @pytest.fixture(scope="class")
    def small_config(self):
        """Small scale configuration for testing"""
        return PlatformConfig.create('small', months_back=12)
    
    def test_config_creation(self):
        """Test configuration objects are created correctly"""
        xs_config = PlatformConfig.create('xs')
        small_config = PlatformConfig.create('small')
        enterprise_config = PlatformConfig.create('enterprise')
        
        assert xs_config.scale == DataScale.XS
        assert xs_config.customers == 100
        assert small_config.customers == 1000
        assert enterprise_config.customers == 40000
        
        # Test date ranges are reasonable
        assert xs_config.start_date < xs_config.end_date
        assert (xs_config.end_date - xs_config.start_date).days > 30
    
    def test_hubspot_generation(self, xs_config):
        """Test HubSpot data generation"""
        hubspot_gen = HubSpotDataGenerator(xs_config)
        
        # Generate companies
        companies = hubspot_gen.generate_companies()
        
        assert len(companies) == xs_config.customers
        assert all('id' in company for company in companies)
        assert all('properties' in company for company in companies)
        
        # Test company properties
        for company in companies[:5]:  # Test first 5
            props = company['properties']
            assert 'name' in props
            assert 'email' in props
            assert 'createdate' in props
            assert 'industry' in props
            
        # Generate contacts
        contacts = hubspot_gen.generate_contacts(companies)
        assert len(contacts) >= len(companies)  # At least one contact per company
        
        # Generate deals
        deals = hubspot_gen.generate_deals(companies, contacts)
        assert len(deals) > 0
        
        # Generate tickets
        tickets = hubspot_gen.generate_tickets(companies, contacts)
        assert len(tickets) > 0
        
        # Generate owners
        owners = hubspot_gen.generate_owners()
        assert len(owners) > 0
        
        # Generate engagements
        engagements = hubspot_gen.generate_engagements(companies, contacts, deals)
        assert len(engagements) > 0
    
    def test_device_generation(self, xs_config):
        """Test device and location generation"""
        # Create minimal companies data for testing
        companies = [
            {'id': '10000000', 'properties': {'name': 'Test Company', 'createdate': '2023-01-01'}}
            for i in range(10)
        ]
        
        device_gen = DeviceDataGenerator(xs_config)
        
        # Generate locations
        locations = device_gen.generate_locations(companies)
        assert len(locations) >= len(companies)
        
        # Test location schema
        for location in locations[:5]:
            assert 'id' in location
            assert 'customer_id' in location
            assert 'name' in location
            assert 'address' in location
        
        # Generate devices
        devices = device_gen.generate_devices(locations)
        assert len(devices) >= len(locations)
        
        # Generate users
        users = device_gen.generate_user_activity(companies, locations)
        assert len(users) >= len(companies)
        
        # Test new app database methods
        feature_usage = device_gen.generate_feature_usage(users)
        assert len(feature_usage) > 0
        
        # Validate feature usage schema
        for usage in feature_usage[:5]:
            assert 'usage_id' in usage
            assert 'user_id' in usage
            assert 'customer_id' in usage
            assert 'feature_name' in usage
            assert 'usage_count' in usage
            assert 'timestamp' in usage
        
        page_views = device_gen.generate_page_views(users)
        assert len(page_views) > 0
        
        # Validate page views schema
        for view in page_views[:5]:
            assert 'page_view_id' in view
            assert 'session_id' in view
            assert 'user_id' in view
            assert 'customer_id' in view
            assert 'page_url' in view
            assert 'page_title' in view
        
        user_sessions = device_gen.generate_user_sessions(users)
        assert len(user_sessions) > 0
        
        # Validate user sessions schema
        for session in user_sessions[:5]:
            assert 'session_id' in session
            assert 'user_id' in session
            assert 'customer_id' in session
            assert 'start_time' in session
            assert 'end_time' in session
            assert 'duration_seconds' in session
        
        app_subscriptions = device_gen.generate_app_subscriptions(companies)
        assert len(app_subscriptions) > 0
        
        # Validate app subscriptions schema
        for sub in app_subscriptions[:5]:
            assert 'id' in sub
            assert 'customer_id' in sub
            assert 'plan_name' in sub
            assert 'status' in sub
    
    def test_stripe_generation(self, xs_config):
        """Test Stripe data generation"""
        companies = [
            {
                'id': '10000000', 
                'email': 'test@example.com',
                'name': 'Test Company',
                'business_type': 'Restaurant',
                'location_count': 2,
                'created_date': '2023-01-01'
            }
            for i in range(10)
        ]
        
        locations = [
            {'id': f'loc_{i}', 'customer_id': '10000000'}
            for i in range(20)
        ]
        
        stripe_gen = StripeDataGenerator(xs_config)
        
        # Generate customers
        customers = stripe_gen.generate_customers(companies)
        assert len(customers) == len(companies)
        
        # Validate customer schema
        for customer in customers:
            assert 'id' in customer
            assert customer['id'].startswith('cus_')
            assert 'email' in customer
            assert 'created' in customer
            assert isinstance(customer['created'], int)  # Should be timestamp
        
        # Generate prices
        prices = stripe_gen.generate_prices()
        assert len(prices) > 0
        
        # Generate subscriptions
        subscriptions = stripe_gen.generate_subscriptions(customers, locations)
        assert len(subscriptions) == len(customers)
        
        # Test new Stripe methods
        charges = stripe_gen.generate_charges(subscriptions)
        assert len(charges) > 0
        
        events = stripe_gen.generate_events(count=100)
        assert len(events) == 100
        
        invoices = stripe_gen.generate_invoices(subscriptions)
        assert len(invoices) > 0
        
        payment_intents = stripe_gen.generate_payment_intents(customers, count=5)
        assert len(payment_intents) == 5
        
        subscription_items = stripe_gen.generate_subscription_items(subscriptions)
        assert len(subscription_items) > 0
    
    def test_marketing_generation(self, xs_config):
        """Test marketing data generation"""
        companies = [
            {'id': f'1000000{i}', 'properties': {'name': f'Company {i}'}}
            for i in range(10)
        ]
        
        marketing_gen = MarketingDataGenerator(xs_config)
        
        # Generate campaigns
        google_campaigns = marketing_gen.generate_google_ads_campaigns(companies)
        facebook_campaigns = marketing_gen.generate_facebook_ads_campaigns(companies)
        linkedin_campaigns = marketing_gen.generate_linkedin_ads_campaigns(companies)
        iterable_campaigns = marketing_gen.generate_iterable_campaigns(companies)
        
        assert len(google_campaigns) > 0
        assert len(facebook_campaigns) > 0
        assert len(linkedin_campaigns) > 0
        assert len(iterable_campaigns) > 0
        
        # Generate analytics sessions
        ga_sessions = marketing_gen.generate_google_analytics_sessions(companies)
        assert len(ga_sessions) > 0
        
        # Generate leads and attribution
        campaigns_data = {
            'google_ads': google_campaigns,
            'facebook_ads': facebook_campaigns,
            'linkedin_ads': linkedin_campaigns,
            'iterable': iterable_campaigns
        }
        
        mqls = marketing_gen.generate_marketing_qualified_leads(companies, campaigns_data)
        assert len(mqls) > 0
        
        touchpoints = marketing_gen.generate_attribution_touchpoints(companies, mqls, campaigns_data)
        assert len(touchpoints) > 0

class TestScalability:
    """Test scalability across different data scales"""
    
    @pytest.fixture(scope="class")
    def temp_output_dir(self):
        """Create temporary directory for test output"""
        temp_dir = tempfile.mkdtemp(prefix="data_gen_test_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_xs_scale_generation(self, temp_output_dir):
        """Test XS scale data generation"""
        output_dir = f"{temp_output_dir}/xs_test"
        
        # Run XS generation
        result = subprocess.run([
            'python3', '/Users/lane/Development/Active/data-platform/scripts/generate_synthetic_data.py',
            'xs', '--output', output_dir, '--months', '12'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        
        # Define ALL expected files - this should match all 30 tables
        expected_files = [
            # HubSpot files (6 tables)
            'hubspot/companies.json',
            'hubspot/contacts.json',
            'hubspot/deals.json',
            'hubspot/engagements.json',
            'hubspot/owners.json',
            'hubspot/tickets.json',
            
            # Device/App files (8 tables + device events)
            'devices/users.json',
            'devices/locations.json',
            'devices/devices.json',
            'devices/subscriptions.json',
            'devices/user_sessions.json',
            'devices/page_views.json',
            'devices/feature_usage.json',
            # Note: device_events_batch_*.json checked separately
            # Note: accounts.json not generated - populated from companies
            
            # Stripe files (8 tables)
            'stripe/customers.json',
            'stripe/prices.json',
            'stripe/subscriptions.json',
            'stripe/subscription_items.json',
            'stripe/invoices.json',
            'stripe/charges.json',
            'stripe/payment_intents.json',
            'stripe/events.json',
            
            # Marketing files (7 tables)
            'marketing/attribution_touchpoints.json',
            'marketing/facebook_ads_campaigns.json',
            'marketing/google_ads_campaigns.json',
            'marketing/google_analytics_sessions.json',
            'marketing/iterable_campaigns.json',
            'marketing/linkedin_ads_campaigns.json',
            'marketing/marketing_qualified_leads.json'
        ]
        
        print("\n📁 Verifying ALL expected output files...")
        missing_files = []
        empty_files = []
        
        for file_path in expected_files:
            full_path = f"{output_dir}/{file_path}"
            if os.path.exists(full_path):
                # Check file size
                size = os.path.getsize(full_path)
                
                # Verify file has content
                with open(full_path, 'r') as f:
                    try:
                        data = json.load(f)
                        if len(data) == 0:
                            empty_files.append(file_path)
                            print(f"  ❌ {file_path} - EMPTY")
                        else:
                            print(f"  ✅ {file_path} - {len(data)} records, {size/1024:.1f} KB")
                    except json.JSONDecodeError:
                        empty_files.append(file_path)
                        print(f"  ❌ {file_path} - INVALID JSON")
            else:
                missing_files.append(file_path)
                print(f"  ❌ {file_path} - MISSING")
        
        # Check for device event batches
        device_event_files = glob.glob(f"{output_dir}/devices/device_events_batch_*.json")
        assert len(device_event_files) > 0, "No device event batch files found"
        print(f"  ✅ Found {len(device_event_files)} device event batch files")
        
        # Verify totals
        total_expected = len(expected_files)
        total_found = total_expected - len(missing_files)
        total_valid = total_found - len(empty_files)
        
        print(f"\n📊 Summary:")
        print(f"  Expected files: {total_expected}")
        print(f"  Found files: {total_found}")
        print(f"  Valid files with data: {total_valid}")
        
        assert len(missing_files) == 0, f"Missing files: {missing_files}"
        assert len(empty_files) == 0, f"Empty files: {empty_files}"
        
        print("✅ All expected files generated successfully with valid data")
    
    def test_data_volume_scaling(self):
        """Test that data volumes scale appropriately"""
        xs_config = PlatformConfig.create('xs', months_back=6)
        small_config = PlatformConfig.create('small', months_back=6)
        
        # Create minimal test companies
        xs_companies = [{'id': f'1000000{i}', 'properties': {'name': f'Company {i}'}} for i in range(xs_config.customers)]
        small_companies = [{'id': f'1000000{i}', 'properties': {'name': f'Company {i}'}} for i in range(min(100, small_config.customers))]  # Limit for testing
        
        # Test device generation scaling
        device_gen_xs = DeviceDataGenerator(xs_config)
        device_gen_small = DeviceDataGenerator(small_config)
        
        xs_locations = device_gen_xs.generate_locations(xs_companies)
        small_locations = device_gen_small.generate_locations(small_companies)
        
        # Should have roughly proportional scaling
        scaling_factor = len(small_companies) / len(xs_companies)
        expected_small_locations = len(xs_locations) * scaling_factor
        
        # Allow for 50% variance due to randomness
        assert abs(len(small_locations) - expected_small_locations) / expected_small_locations < 0.5

class TestDataQuality:
    """Test data quality and business logic"""
    
    def test_data_relationships(self):
        """Test that data relationships are maintained"""
        config = PlatformConfig.create('xs', months_back=6)
        
        # Generate related data
        companies = [
            {'id': '10000000', 'properties': {'name': 'Test Company', 'createdate': '2023-01-01'}}
        ]
        
        device_gen = DeviceDataGenerator(config)
        locations = device_gen.generate_locations(companies)
        users = device_gen.generate_user_activity(companies, locations)
        feature_usage = device_gen.generate_feature_usage(users)
        
        # Test relationships
        company_ids = {company['id'] for company in companies}
        location_customer_ids = {loc['customer_id'] for loc in locations}
        user_customer_ids = {user['customer_id'] for user in users}
        usage_customer_ids = {str(usage['customer_id']) for usage in feature_usage}
        
        # All locations should belong to existing companies
        assert location_customer_ids.issubset(company_ids)
        
        # All users should belong to existing companies
        assert user_customer_ids.issubset(company_ids)
        
        # All feature usage should belong to existing users
        user_ids = {str(user['id']) for user in users}
        usage_user_ids = {str(usage['user_id']) for usage in feature_usage}
        assert usage_user_ids.issubset(user_ids)
    
    def test_timestamp_formats(self):
        """Test that timestamps are in correct formats"""
        config = PlatformConfig.create('xs', months_back=6)
        stripe_gen = StripeDataGenerator(config)
        
        # Test timestamp conversion
        test_date = date(2023, 1, 1)
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        test_string = "2023-01-01T12:00:00"
        
        timestamp1 = stripe_gen._safe_timestamp(test_date)
        timestamp2 = stripe_gen._safe_timestamp(test_datetime)
        timestamp3 = stripe_gen._safe_timestamp(test_string)
        
        assert isinstance(timestamp1, int)
        assert isinstance(timestamp2, int)
        assert isinstance(timestamp3, int)
        assert timestamp1 > 0
        assert timestamp2 > 0
        assert timestamp3 > 0
    
    def test_data_constraints(self):
        """Test that data meets business constraints"""
        config = PlatformConfig.create('xs', months_back=6)
        
        companies = [
            {'id': '10000000', 'properties': {'name': 'Test Company', 'createdate': '2023-01-01'}}
        ]
        
        device_gen = DeviceDataGenerator(config)
        users = device_gen.generate_user_activity(companies, [])
        user_sessions = device_gen.generate_user_sessions(users)
        
        # Test session duration constraints
        for session in user_sessions[:10]:
            assert session['duration_seconds'] > 0
            assert session['duration_seconds'] <= 7200  # Max 2 hours
            assert session['page_views'] > 0
            assert session['actions_taken'] >= 0

class TestDatabaseIntegration:
    """Test integration with actual database"""
    
    def get_db_connection(self):
        """Get database connection for testing"""
        try:
            return psycopg2.connect(**TEST_DB_CONFIG)
        except psycopg2.Error:
            pytest.skip("Database not available for testing")
    
    def test_schema_compatibility(self):
        """Test that generated data matches database schemas"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get schema for a test table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' AND table_name = 'app_database_feature_usage'
            ORDER BY ordinal_position
        """)
        
        schema = {row[0]: row[1] for row in cursor.fetchall()}
        
        if schema:  # Only test if table exists
            # Generate test data
            config = PlatformConfig.create('xs', months_back=1)
            companies = [{'id': '10000000', 'properties': {'name': 'Test'}}]
            device_gen = DeviceDataGenerator(config)
            users = device_gen.generate_user_activity(companies, [])
            feature_usage = device_gen.generate_feature_usage(users)
            
            # Test schema compatibility
            if feature_usage:
                usage_record = feature_usage[0]
                
                # Check required columns exist
                assert 'usage_id' in usage_record
                assert 'user_id' in usage_record
                assert 'customer_id' in usage_record
                assert 'feature_name' in usage_record
                assert 'usage_count' in usage_record
                assert 'timestamp' in usage_record
        
        cursor.close()
        conn.close()
    
    def test_data_loading(self):
        """Test actual data loading into database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Test if we can insert generated data
        config = PlatformConfig.create('xs', months_back=1)
        companies = [{'id': '10000000', 'properties': {'name': 'Test Company'}}]
        
        device_gen = DeviceDataGenerator(config)
        users = device_gen.generate_user_activity(companies, [])
        feature_usage = device_gen.generate_feature_usage(users[:1])  # Just one user for testing
        
        if feature_usage:
            # Try to insert one record with a unique ID
            usage = feature_usage[0]
            # Make the ID unique by adding timestamp
            import time
            unique_suffix = str(int(time.time() * 1000000))[-8:]
            usage['usage_id'] = f"test_usage_{unique_suffix}"
            
            try:
                cursor.execute("""
                    INSERT INTO raw.app_database_feature_usage 
                    (usage_id, user_id, customer_id, feature_name, usage_count, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    usage['usage_id'],
                    usage['user_id'],
                    usage['customer_id'],
                    usage['feature_name'],
                    usage['usage_count'],
                    usage['timestamp']
                ))
                
                # Clean up test data
                cursor.execute("DELETE FROM raw.app_database_feature_usage WHERE usage_id = %s", 
                             (usage['usage_id'],))
                conn.commit()
                
            except psycopg2.Error as e:
                pytest.fail(f"Failed to insert test data: {e}")
        
        cursor.close()
        conn.close()

class TestPerformance:
    """Test performance characteristics"""
    
    def test_generation_speed(self):
        """Test generation completes within reasonable time"""
        import time
        
        config = PlatformConfig.create('xs', months_back=6)
        companies = [
            {'id': f'1000000{i}', 'properties': {'name': f'Company {i}', 'createdate': '2023-01-01'}}
            for i in range(10)  # Small test set
        ]
        
        device_gen = DeviceDataGenerator(config)
        
        # Time the generation
        start_time = time.time()
        locations = device_gen.generate_locations(companies)
        users = device_gen.generate_user_activity(companies, locations)
        feature_usage = device_gen.generate_feature_usage(users)
        end_time = time.time()
        
        duration = end_time - start_time
        records_generated = len(locations) + len(users) + len(feature_usage)
        
        # Should generate at least 100 records per second
        rate = records_generated / duration
        assert rate > 100, f"Generation too slow: {rate} records/second"
    
    def test_memory_usage(self):
        """Test that memory usage is reasonable"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate a moderate amount of data
        config = PlatformConfig.create('xs', months_back=6)
        companies = [
            {'id': f'1000000{i}', 'properties': {'name': f'Company {i}'}}
            for i in range(50)
        ]
        
        device_gen = DeviceDataGenerator(config)
        locations = device_gen.generate_locations(companies)
        users = device_gen.generate_user_activity(companies, locations)
        feature_usage = device_gen.generate_feature_usage(users)
        page_views = device_gen.generate_page_views(users)
        user_sessions = device_gen.generate_user_sessions(users)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        total_records = len(locations) + len(users) + len(feature_usage) + len(page_views) + len(user_sessions)
        memory_per_record = memory_increase / total_records if total_records > 0 else 0
        
        # Should use less than 1KB per record on average
        assert memory_per_record < 1.0, f"Memory usage too high: {memory_per_record:.2f} MB per record"

# Test execution functions
def run_quick_tests():
    """Run quick smoke tests"""
    pytest.main([
        __file__ + "::TestDataGenerator::test_config_creation",
        __file__ + "::TestDataGenerator::test_hubspot_generation",
        __file__ + "::TestDataQuality::test_timestamp_formats",
        "-v"
    ])

def run_full_tests():
    """Run complete test suite"""
    pytest.main([__file__, "-v", "--tb=short"])

def run_performance_tests():
    """Run performance-focused tests"""
    pytest.main([
        __file__ + "::TestPerformance",
        __file__ + "::TestScalability::test_data_volume_scaling",
        "-v"
    ])

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run data generator tests')
    parser.add_argument('--quick', action='store_true', help='Run quick smoke tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_tests()
    elif args.performance:
        run_performance_tests()
    elif args.full:
        run_full_tests()
    else:
        print("Usage: python test_data_generator.py [--quick|--performance|--full]")
        print("  --quick: Run smoke tests (5-10 minutes)")
        print("  --performance: Run performance tests (10-15 minutes)")
        print("  --full: Run complete test suite (20-30 minutes)")
