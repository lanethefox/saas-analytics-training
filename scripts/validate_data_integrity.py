#!/usr/bin/env python3
"""
Validate data integrity after generation.

This script checks:
- All foreign key relationships are valid
- ID ranges match configuration
- Business rules are satisfied
- Data distributions match expectations
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
from scripts.config_loader import DataGenerationConfig

# Initialize configuration
config = DataGenerationConfig()

class DataValidator:
    """Validates generated data integrity"""
    
    def __init__(self):
        self.config = config
        self.errors = []
        self.warnings = []
        self.info = []
        
    def add_error(self, message):
        """Add an error message"""
        self.errors.append(f"❌ ERROR: {message}")
        
    def add_warning(self, message):
        """Add a warning message"""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def add_info(self, message):
        """Add an info message"""
        self.info.append(f"ℹ️  INFO: {message}")
        
    def validate_id_ranges(self):
        """Validate that all IDs are within configured ranges"""
        print("\n🔍 Validating ID ranges...")
        id_ranges = self.config.get_id_ranges()
        
        checks = [
            ('accounts', 'app_database_accounts'),
            ('locations', 'app_database_locations'),
            ('devices', 'app_database_devices'),
            ('users', 'app_database_users'),
            ('subscriptions', 'app_database_subscriptions')
        ]
        
        for entity, table in checks:
            min_id, max_id = id_ranges[entity]
            
            with db_helper.config.get_cursor() as cursor:
                cursor.execute(f"""
                    SELECT MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count
                    FROM raw.{table}
                """)
                result = cursor.fetchone()
                
                if result[2] > 0:  # Has data
                    actual_min, actual_max = result[0], result[1]
                    
                    if actual_min < min_id:
                        self.add_error(f"{entity}: Minimum ID {actual_min} is below range start {min_id}")
                    if actual_max > max_id:
                        self.add_error(f"{entity}: Maximum ID {actual_max} exceeds range limit {max_id}")
                    
                    self.add_info(f"{entity}: IDs range from {actual_min} to {actual_max} (configured: {min_id}-{max_id})")
                else:
                    self.add_warning(f"{entity}: No data found in {table}")
    
    def validate_foreign_keys(self):
        """Validate all foreign key relationships"""
        print("\n🔍 Validating foreign key relationships...")
        
        # Check locations -> accounts
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as orphaned
                FROM raw.app_database_locations l
                LEFT JOIN raw.app_database_accounts a ON l.customer_id = a.id
                WHERE a.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                self.add_error(f"Found {orphaned} locations with invalid customer_id")
            else:
                self.add_info("✓ All locations have valid account references")
        
        # Check devices -> locations
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as orphaned
                FROM raw.app_database_devices d
                LEFT JOIN raw.app_database_locations l ON d.location_id = l.id
                WHERE l.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                self.add_error(f"Found {orphaned} devices with invalid location_id")
            else:
                self.add_info("✓ All devices have valid location references")
                
            # Also check max location_id in devices
            cursor.execute("SELECT MAX(location_id) FROM raw.app_database_devices")
            max_location_ref = cursor.fetchone()[0]
            cursor.execute("SELECT MAX(id) FROM raw.app_database_locations")
            max_location_id = cursor.fetchone()[0]
            
            if max_location_ref and max_location_id:
                self.add_info(f"Max location_id referenced by devices: {max_location_ref}")
                self.add_info(f"Max location id that exists: {max_location_id}")
        
        # Check users -> accounts
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as orphaned
                FROM raw.app_database_users u
                LEFT JOIN raw.app_database_accounts a ON u.customer_id = a.id
                WHERE a.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                self.add_error(f"Found {orphaned} users with invalid customer_id")
            else:
                self.add_info("✓ All users have valid account references")
        
        # Check subscriptions -> accounts
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as orphaned
                FROM raw.app_database_subscriptions s
                LEFT JOIN raw.app_database_accounts a ON s.customer_id = a.id
                WHERE a.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                self.add_error(f"Found {orphaned} subscriptions with invalid customer_id")
            else:
                self.add_info("✓ All subscriptions have valid account references")
    
    def validate_business_rules(self):
        """Validate business rules and data quality"""
        print("\n🔍 Validating business rules...")
        
        # Check account size distribution
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN id <= 105 THEN 'small'
                        WHEN id <= 135 THEN 'medium'
                        WHEN id <= 147 THEN 'large'
                        ELSE 'enterprise'
                    END as size,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
                FROM raw.app_database_accounts
                GROUP BY size
                ORDER BY 
                    CASE size
                        WHEN 'small' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'large' THEN 3
                        WHEN 'enterprise' THEN 4
                    END
            """)
            
            expected = {'small': 70, 'medium': 20, 'large': 8, 'enterprise': 2}
            
            for row in cursor.fetchall():
                size, count, percentage = row
                expected_pct = expected.get(size, 0)
                
                if abs(percentage - expected_pct) > 5:  # 5% tolerance
                    self.add_warning(f"Account size '{size}': {percentage}% (expected ~{expected_pct}%)")
                else:
                    self.add_info(f"Account size '{size}': {count} accounts ({percentage}%)")
        
        # Check device operational status
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
                FROM raw.app_database_devices
                GROUP BY status
            """)
            
            device_dist = self.config.get_device_config()['operational_distribution']
            expected_online = device_dist['online'] * 100
            
            for row in cursor.fetchall():
                status, count, percentage = row
                self.add_info(f"Device status '{status}': {count} devices ({percentage}%)")
                
                if status == 'Online' and percentage < expected_online - 10:
                    self.add_warning(f"Low online device rate: {percentage}% (expected ~{expected_online}%)")
        
        # Check that each account has at least one user
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM raw.app_database_accounts a
                LEFT JOIN raw.app_database_users u ON a.id = u.customer_id
                WHERE u.id IS NULL
            """)
            accounts_without_users = cursor.fetchone()[0]
            
            if accounts_without_users > 0:
                self.add_error(f"Found {accounts_without_users} accounts without any users")
            else:
                self.add_info("✓ All accounts have at least one user")
        
        # Check subscription pricing matches tier limits
        with db_helper.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.plan_name,
                    s.monthly_price,
                    COUNT(*) as count
                FROM raw.app_database_subscriptions s
                WHERE s.status = 'active'
                GROUP BY s.plan_name, s.monthly_price
                ORDER BY s.plan_name
            """)
            
            tiers = self.config.get_subscription_tiers()
            
            for row in cursor.fetchall():
                plan, price, count = row
                if plan in tiers:
                    expected_price = tiers[plan]['monthly_price']
                    if price != expected_price:
                        self.add_error(f"Subscription tier '{plan}' has price ${price} (expected ${expected_price})")
                    else:
                        self.add_info(f"Subscription tier '{plan}': {count} active subscriptions at ${price}/mo")
    
    def validate_data_consistency(self):
        """Validate data consistency across tables"""
        print("\n🔍 Validating data consistency...")
        
        # Compare device counts
        with db_helper.config.get_cursor() as cursor:
            # Total devices in device table
            cursor.execute("SELECT COUNT(*) FROM raw.app_database_devices")
            total_devices = cursor.fetchone()[0]
            
            # Expected device count from location table
            cursor.execute("SELECT SUM(expected_device_count) FROM raw.app_database_locations")
            expected_devices = cursor.fetchone()[0]
            
            if expected_devices:
                variance = abs(total_devices - expected_devices) / expected_devices * 100
                if variance > 20:  # 20% tolerance
                    self.add_warning(f"Device count variance: {total_devices} actual vs {expected_devices} expected ({variance:.1f}% difference)")
                else:
                    self.add_info(f"Device count: {total_devices} actual vs {expected_devices} expected ({variance:.1f}% variance)")
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n✅ No errors found!")
        
        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.info:
            print(f"\nℹ️  Information ({len(self.info)} items):")
            for info in self.info:
                print(f"  {info}")
        
        print("\n" + "=" * 60)
        
        return len(self.errors) == 0

def main():
    """Main execution function"""
    print("=" * 60)
    print("Data Integrity Validation")
    print("=" * 60)
    
    validator = DataValidator()
    
    # Run all validations
    validator.validate_id_ranges()
    validator.validate_foreign_keys()
    validator.validate_business_rules()
    validator.validate_data_consistency()
    
    # Print summary and exit with appropriate code
    success = validator.print_summary()
    
    if success:
        print("\n✅ All validations passed!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed! Please review errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()