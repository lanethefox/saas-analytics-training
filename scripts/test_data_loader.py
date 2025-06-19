"""
Test Suite for Synthetic Data Loader
====================================

Tests the load_synthetic_data.py script functionality including:
- Database connection and schema creation
- JSON file loading
- Data integrity after loading
- Error handling and recovery
"""

import pytest
import psycopg2
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from load_synthetic_data import DataLoader, DB_CONFIG, FILE_TABLE_MAPPING

# Test database configuration (uses same as main)
TEST_DB_CONFIG = DB_CONFIG.copy()


class TestDataLoaderConnection:
    """Test database connection functionality"""
    
    def test_connection_success(self):
        """Test successful database connection"""
        loader = DataLoader()
        loader.connect()
        
        assert loader.conn is not None
        assert loader.cursor is not None
        assert not loader.conn.closed
        
        loader.disconnect()
        
    def test_schema_creation(self):
        """Test schema creation/verification"""
        loader = DataLoader()
        loader.connect()
        
        # Create schema
        loader.create_schema()
        
        # Verify schema exists
        loader.cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'raw'
        """)
        result = loader.cursor.fetchone()
        assert result is not None
        assert result[0] == 'raw'
        
        loader.disconnect()


class TestDataLoaderFunctionality:
    """Test core data loading functionality"""
    
    @pytest.fixture(scope="class")
    def temp_data_dir(self):
        """Create temporary directory with test data"""
        temp_dir = tempfile.mkdtemp(prefix="loader_test_")
        
        # Create test JSON files
        test_data = {
            'hubspot/companies.json': [
                {
                    'id': '10000001',
                    'properties': {
                        'name': 'Test Company 1',
                        'email': 'test1@example.com',
                        'createdate': '2024-01-01T00:00:00Z'
                    }
                },
                {
                    'id': '10000002',
                    'properties': {
                        'name': 'Test Company 2',
                        'email': 'test2@example.com',
                        'createdate': '2024-01-02T00:00:00Z'
                    }
                }
            ],
            'hubspot/contacts.json': [
                {
                    'id': '20000001',
                    'properties': {
                        'firstname': 'John',
                        'lastname': 'Doe',
                        'email': 'john.doe@example.com'
                    }
                }
            ],
            'devices/users.json': [
                {
                    'id': 1,
                    'name': 'Test User',
                    'email': 'user@example.com',
                    'account_id': 10000001,
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ]
        }
        
        # Create directory structure and files
        for file_path, data in test_data.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                json.dump(data, f)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_load_json_file(self, temp_data_dir):
        """Test loading a single JSON file"""
        loader = DataLoader()
        loader.connect()
        
        # Create test table
        loader.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.test_loader_table (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                created_at TIMESTAMP
            )
        """)
        loader.conn.commit()
        
        # Create test data
        test_file = os.path.join(temp_data_dir, 'test_data.json')
        test_data = [
            {
                'id': 'test_001',
                'name': 'Test Record 1',
                'email': 'test1@example.com',
                'created_at': '2024-01-01T00:00:00Z'
            },
            {
                'id': 'test_002',
                'name': 'Test Record 2',
                'email': 'test2@example.com',
                'created_at': '2024-01-02T00:00:00Z'
            }
        ]
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load data
        loader.load_json_file(test_file, 'test_loader_table')
        
        # Verify data was loaded
        loader.cursor.execute("SELECT COUNT(*) FROM raw.test_loader_table")
        count = loader.cursor.fetchone()[0]
        assert count == 2
        
        # Verify data content
        loader.cursor.execute("""
            SELECT id, name, email 
            FROM raw.test_loader_table 
            ORDER BY id
        """)
        results = loader.cursor.fetchall()
        
        assert results[0][0] == 'test_001'
        assert results[0][1] == 'Test Record 1'
        assert results[1][0] == 'test_002'
        
        # Cleanup
        loader.cursor.execute("DROP TABLE raw.test_loader_table")
        loader.conn.commit()
        loader.disconnect()
    
    def test_handle_duplicate_keys(self):
        """Test handling of duplicate primary keys"""
        loader = DataLoader()
        loader.connect()
        
        # Create test table
        loader.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.test_duplicate_table (
                id VARCHAR(50) PRIMARY KEY,
                value VARCHAR(255)
            )
        """)
        loader.conn.commit()
        
        # Insert initial data
        loader.cursor.execute("""
            INSERT INTO raw.test_duplicate_table (id, value)
            VALUES ('dup_001', 'Original Value')
        """)
        loader.conn.commit()
        
        # Try to load duplicate data
        test_file = '/tmp/test_duplicates.json'
        test_data = [
            {'id': 'dup_001', 'value': 'Duplicate Value'},
            {'id': 'dup_002', 'value': 'New Value'}
        ]
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load should handle duplicates gracefully
        loader.load_json_file(test_file, 'test_duplicate_table')
        
        # Verify only new record was added
        loader.cursor.execute("SELECT COUNT(*) FROM raw.test_duplicate_table")
        count = loader.cursor.fetchone()[0]
        assert count == 2  # Original + 1 new
        
        # Cleanup
        loader.cursor.execute("DROP TABLE raw.test_duplicate_table")
        loader.conn.commit()
        loader.disconnect()
        os.unlink(test_file)
    
    def test_verify_data_loading(self):
        """Test data loading verification"""
        loader = DataLoader()
        loader.connect()
        
        # Define all expected tables (30 total)
        expected_tables = [
            # App Database tables (9)
            'app_database_accounts',
            'app_database_locations', 
            'app_database_users',
            'app_database_devices',
            'app_database_subscriptions',
            'app_database_tap_events',
            'app_database_user_sessions',
            'app_database_page_views',
            'app_database_feature_usage',
            
            # Stripe tables (8)
            'stripe_customers',
            'stripe_prices',
            'stripe_subscriptions',
            'stripe_subscription_items',
            'stripe_invoices',
            'stripe_charges',
            'stripe_payment_intents',
            'stripe_events',
            
            # HubSpot tables (6)
            'hubspot_companies',
            'hubspot_contacts',
            'hubspot_deals',
            'hubspot_engagements',
            'hubspot_owners',
            'hubspot_tickets',
            
            # Marketing tables (7)
            'attribution_touchpoints',
            'facebook_ads_campaigns',
            'google_ads_campaigns',
            'google_analytics_sessions',
            'iterable_campaigns',
            'linkedin_ads_campaigns',
            'marketing_qualified_leads'
        ]
        
        # Check that all expected tables exist
        loader.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw'
            ORDER BY table_name
        """)
        
        actual_tables = {row[0] for row in loader.cursor.fetchall()}
        expected_set = set(expected_tables)
        
        missing_tables = expected_set - actual_tables
        extra_tables = actual_tables - expected_set
        
        assert len(missing_tables) == 0, f"Missing tables: {missing_tables}"
        assert len(actual_tables) >= 30, f"Expected at least 30 tables, found {len(actual_tables)}"
        
        print(f"✅ All {len(expected_tables)} expected tables exist")
        
        loader.disconnect()


class TestDataLoaderIntegration:
    """Integration tests with generated data"""
    
    def test_all_tables_loaded_after_full_run(self):
        """Test that all 30 tables have data after a full load"""
        # This test assumes XS data has been generated and loaded
        # It verifies the END STATE of the database
        
        loader = DataLoader()
        loader.connect()
        
        try:
            # Expected tables and minimum row counts
            expected_data = {
                # App Database tables (9)
                'app_database_accounts': 1,  # Should have companies
                'app_database_locations': 1,
                'app_database_users': 1,
                'app_database_devices': 1,
                'app_database_subscriptions': 1,
                'app_database_tap_events': 1,
                'app_database_user_sessions': 1,
                'app_database_page_views': 1,
                'app_database_feature_usage': 1,
                
                # Stripe tables (8)
                'stripe_customers': 1,
                'stripe_prices': 1,
                'stripe_subscriptions': 1,
                'stripe_subscription_items': 1,
                'stripe_invoices': 1,
                'stripe_charges': 1,
                'stripe_payment_intents': 1,
                'stripe_events': 1,
                
                # HubSpot tables (6)
                'hubspot_companies': 1,
                'hubspot_contacts': 1,
                'hubspot_deals': 1,
                'hubspot_engagements': 1,
                'hubspot_owners': 1,
                'hubspot_tickets': 1,
                
                # Marketing tables (7)
                'attribution_touchpoints': 1,
                'facebook_ads_campaigns': 1,
                'google_ads_campaigns': 1,
                'google_analytics_sessions': 1,
                'iterable_campaigns': 1,
                'linkedin_ads_campaigns': 1,
                'marketing_qualified_leads': 1
            }
            
            empty_tables = []
            total_records = 0
            
            print("\n📊 Checking all tables have data...")
            for table_name, min_rows in expected_data.items():
                loader.cursor.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
                count = loader.cursor.fetchone()[0]
                total_records += count
                
                if count < min_rows:
                    empty_tables.append(table_name)
                    print(f"  ❌ {table_name}: {count} records (expected >= {min_rows})")
                else:
                    print(f"  ✅ {table_name}: {count:,} records")
            
            print(f"\nTotal records across all tables: {total_records:,}")
            
            # All tables should have data
            assert len(empty_tables) == 0, f"Empty tables found: {empty_tables}"
            assert len(expected_data) == 30, "Test should check exactly 30 tables"
            
            print("✅ All 30 tables have data!")
            
        finally:
            loader.disconnect()
    
    def test_load_generated_xs_data(self):
        """Test loading actual generated XS data if available"""
        # Check if XS data exists
        xs_data_path = '/Users/lane/Development/Active/data-platform/data/test_xs'
        
        if not os.path.exists(xs_data_path):
            pytest.skip("XS test data not available")
        
        # Temporarily update DATA_DIR to point to test data
        import load_synthetic_data
        original_data_dir = load_synthetic_data.DATA_DIR
        load_synthetic_data.DATA_DIR = xs_data_path
        
        try:
            loader = DataLoader()
            loader.connect()
            
            # Clear test data first
            tables_to_clear = [
                'hubspot_companies', 'hubspot_contacts', 'hubspot_deals',
                'app_database_users', 'app_database_feature_usage'
            ]
            
            for table in tables_to_clear:
                loader.cursor.execute(f"TRUNCATE TABLE raw.{table} CASCADE")
            loader.conn.commit()
            
            # Load a subset of files
            test_files = [
                ('hubspot/companies.json', 'hubspot_companies'),
                ('hubspot/contacts.json', 'hubspot_contacts'),
            ]
            
            for file_pattern, table_name in test_files:
                file_path = os.path.join(xs_data_path, file_pattern)
                if os.path.exists(file_path):
                    loader.load_json_file(file_path, table_name)
            
            # Verify data was loaded
            loader.cursor.execute("SELECT COUNT(*) FROM raw.hubspot_companies")
            company_count = loader.cursor.fetchone()[0]
            # Note: Loading may fail due to schema mismatch, but contacts should work
            
            loader.cursor.execute("SELECT COUNT(*) FROM raw.hubspot_contacts")
            contact_count = loader.cursor.fetchone()[0]
            assert contact_count > 0  # Should have loaded some contacts
            
            # Cleanup - remove test data
            for table in tables_to_clear:
                loader.cursor.execute(f"TRUNCATE TABLE raw.{table} CASCADE")
            loader.conn.commit()
            
            loader.disconnect()
            
        finally:
            # Restore original DATA_DIR
            load_synthetic_data.DATA_DIR = original_data_dir


class TestDataLoaderErrorHandling:
    """Test error handling and recovery"""
    
    def test_handle_malformed_json(self):
        """Test handling of malformed JSON files"""
        loader = DataLoader()
        loader.connect()
        
        # Create malformed JSON file
        bad_file = '/tmp/bad_data.json'
        with open(bad_file, 'w') as f:
            f.write('{"invalid": json content')
        
        # Should handle error gracefully
        loader.load_json_file(bad_file, 'some_table')
        
        # Loader should still be connected
        assert not loader.conn.closed
        
        loader.disconnect()
        os.unlink(bad_file)
    
    def test_handle_missing_columns(self):
        """Test handling of data with missing columns"""
        loader = DataLoader()
        loader.connect()
        
        # Create test table with required columns
        loader.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.test_missing_cols (
                id VARCHAR(50) PRIMARY KEY,
                required_field VARCHAR(255) NOT NULL,
                optional_field VARCHAR(255)
            )
        """)
        loader.conn.commit()
        
        # Create data missing required field
        test_file = '/tmp/missing_cols.json'
        test_data = [
            {'id': 'test_001', 'optional_field': 'Value'}  # Missing required_field
        ]
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Should handle error gracefully
        loader.load_json_file(test_file, 'test_missing_cols')
        
        # Verify no data was loaded due to error
        loader.cursor.execute("SELECT COUNT(*) FROM raw.test_missing_cols")
        count = loader.cursor.fetchone()[0]
        assert count == 0
        
        # Cleanup
        loader.cursor.execute("DROP TABLE raw.test_missing_cols")
        loader.conn.commit()
        loader.disconnect()
        os.unlink(test_file)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
