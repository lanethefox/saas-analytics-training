#!/usr/bin/env python3
"""
Test Runner for Data Generator Test Suite
========================================

Provides easy commands to run different test categories with proper setup and reporting.
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_command(cmd, description, timeout=300):
    """Run a command with timeout and error handling"""
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd="/Users/lane/Development/Active/data-platform"
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration:.1f}s")
            if result.stdout:
                print("\n📋 Output:")
                print(result.stdout)
        else:
            print(f"❌ {description} failed after {duration:.1f}s")
            if result.stderr:
                print("\n🚨 Error:")
                print(result.stderr)
            if result.stdout:
                print("\n📋 Output:")
                print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"💥 {description} failed with exception: {e}")
        return False
    
    return True

def check_dependencies():
    """Check that required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    required_packages = ['pytest', 'psycopg2', 'faker', 'pandas', 'numpy', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check database connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='saas_platform_dev',
            user='saas_user',
            password='saas_secure_password_2024'
        )
        conn.close()
        print("  ✅ Database connection")
    except Exception as e:
        print(f"  ⚠️  Database connection failed: {e}")
        print("     (Database tests will be skipped)")
    
    return True

def run_smoke_tests():
    """Run quick smoke tests (5-10 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py::TestDataGenerator::test_config_creation',
        'scripts/test_data_generator.py::TestDataGenerator::test_hubspot_generation',
        'scripts/test_data_generator.py::TestDataGenerator::test_device_generation',
        'scripts/test_data_generator.py::TestDataQuality::test_timestamp_formats',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Smoke Tests", timeout=600)

def run_generation_tests():
    """Run data generation tests (10-15 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py::TestDataGenerator',
        'scripts/test_data_generator.py::TestDataQuality',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Data Generation Tests", timeout=900)

def run_scalability_tests():
    """Run scalability tests (15-20 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py::TestScalability',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Scalability Tests", timeout=1200)

def run_performance_tests():
    """Run performance tests (10-15 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py::TestPerformance',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Performance Tests", timeout=900)

def run_database_tests():
    """Run database integration tests (5-10 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py::TestDatabaseIntegration',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Database Integration Tests", timeout=600)

def run_loader_tests():
    """Run data loader tests (5-10 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_loader.py',
        '-v', '--tb=short'
    ]
    
    return run_command(cmd, "Data Loader Tests", timeout=600)

def run_full_test_suite():
    """Run complete test suite (30-45 minutes)"""
    cmd = [
        'python3', '-m', 'pytest', 
        'scripts/test_data_generator.py',
        '-v', '--tb=short', '--durations=10'
    ]
    
    return run_command(cmd, "Full Test Suite", timeout=2700)

def run_xs_generation_test():
    """Test actual XS data generation end-to-end"""
    print("\n🧪 Testing XS Data Generation End-to-End")
    print("=" * 60)
    
    # Create test output directory
    test_dir = "/tmp/data_gen_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cmd = [
        'python3', 'scripts/generate_synthetic_data.py',
        'xs', '--output', test_dir, '--months', '6'
    ]
    
    success = run_command(cmd, "XS Data Generation", timeout=600)
    
    if success:
        # Verify output files
        expected_files = [
            'hubspot/companies.json',
            'devices/feature_usage.json',
            'stripe/charges.json',
            'marketing/attribution_touchpoints.json'
        ]
        
        print("\n📁 Verifying output files...")
        all_files_exist = True
        
        for file_path in expected_files:
            full_path = f"{test_dir}/{file_path}"
            if os.path.exists(full_path):
                print(f"  ✅ {file_path}")
                
                # Check file size
                size = os.path.getsize(full_path) / 1024  # KB
                print(f"     Size: {size:.1f} KB")
            else:
                print(f"  ❌ {file_path}")
                all_files_exist = False
        
        if all_files_exist:
            print("✅ All expected files generated successfully")
        else:
            print("❌ Some files missing")
            success = False
        
        # Cleanup
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory: {test_dir}")
    
    return success

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Generator Test Runner')
    parser.add_argument('test_type', nargs='?', choices=[
        'smoke', 'generation', 'scalability', 'performance', 
        'database', 'loader', 'full', 'xs-generation', 'deps'
    ], default='smoke', help='Type of tests to run')
    
    args = parser.parse_args()
    
    print("🧪 Data Generator Test Suite")
    print("=" * 60)
    print(f"Test Type: {args.test_type}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.test_type == 'deps':
        success = check_dependencies()
    elif args.test_type == 'smoke':
        success = check_dependencies() and run_smoke_tests()
    elif args.test_type == 'generation':
        success = check_dependencies() and run_generation_tests()
    elif args.test_type == 'scalability':
        success = check_dependencies() and run_scalability_tests()
    elif args.test_type == 'performance':
        success = check_dependencies() and run_performance_tests()
    elif args.test_type == 'database':
        success = check_dependencies() and run_database_tests()
    elif args.test_type == 'loader':
        success = check_dependencies() and run_loader_tests()
    elif args.test_type == 'xs-generation':
        success = check_dependencies() and run_xs_generation_test()
    elif args.test_type == 'full':
        success = (check_dependencies() and 
                  run_smoke_tests() and
                  run_generation_tests() and
                  run_scalability_tests() and
                  run_performance_tests() and
                  run_database_tests() and
                  run_loader_tests() and
                  run_xs_generation_test())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
