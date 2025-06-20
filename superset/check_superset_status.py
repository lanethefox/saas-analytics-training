#!/usr/bin/env python3
"""
Check Superset status and troubleshoot connection issues
"""

import requests
import subprocess
import time
import sys

SUPERSET_URL = "http://localhost:8088"

def check_docker_services():
    """Check if required Docker services are running"""
    print("=== Checking Docker Services ===\n")
    
    required_services = ["postgres", "superset"]
    all_running = True
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        print("Docker services status:")
        print("-" * 50)
        
        for service in required_services:
            if f"saas_platform_{service}" in output and "Up" in output:
                print(f"✓ {service}: Running")
            else:
                print(f"✗ {service}: Not running")
                all_running = False
                
    except Exception as e:
        print(f"Error checking Docker services: {e}")
        all_running = False
    
    return all_running

def check_superset_health():
    """Check if Superset is healthy"""
    print("\n=== Checking Superset Health ===\n")
    
    endpoints = [
        ("/health", "Health check"),
        ("/api/v1/", "API endpoint"),
        ("/login/", "Login page")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{SUPERSET_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 308, 302]:
                print(f"✓ {description}: OK ({response.status_code})")
            else:
                print(f"✗ {description}: Failed ({response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"✗ {description}: Connection refused")
        except requests.exceptions.Timeout:
            print(f"✗ {description}: Timeout")
        except Exception as e:
            print(f"✗ {description}: Error - {e}")

def check_database_in_superset():
    """Try to check database configuration via API"""
    print("\n=== Checking Database Configuration ===\n")
    
    # Try without authentication first (some endpoints might be public)
    try:
        response = requests.get(f"{SUPERSET_URL}/api/v1/database/")
        if response.status_code == 401:
            print("⚠ Database endpoint requires authentication")
            print("  This is normal - you'll need to login first")
        elif response.status_code == 200:
            databases = response.json()
            print(f"✓ Found {databases.get('count', 0)} database(s)")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"✗ Could not check databases: {e}")

def start_services():
    """Start Docker services if they're not running"""
    print("\n=== Starting Services ===\n")
    
    print("Starting all services...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Services started successfully")
        print("  Waiting 30 seconds for services to initialize...")
        time.sleep(30)
        return True
    else:
        print(f"✗ Failed to start services")
        print(f"  Error: {result.stderr}")
        return False

def print_access_info():
    """Print access information"""
    print("\n=== Access Information ===\n")
    print(f"Superset URL: {SUPERSET_URL}")
    print(f"Username: admin")
    print(f"Password: admin_password_2024")
    print(f"\nPostgreSQL Connection:")
    print(f"  Host: postgres (internal) / localhost (external)")
    print(f"  Port: 5432")
    print(f"  Database: saas_platform_dev")
    print(f"  Username: saas_user")
    print(f"  Password: saas_secure_password_2024")

def print_troubleshooting():
    """Print troubleshooting steps"""
    print("\n=== Troubleshooting Steps ===\n")
    print("1. Check Docker logs:")
    print("   docker-compose logs superset")
    print("\n2. Restart Superset:")
    print("   docker-compose restart superset")
    print("\n3. Rebuild Superset:")
    print("   docker-compose down superset")
    print("   docker-compose up -d superset")
    print("\n4. Check network:")
    print("   docker network ls")
    print("   docker network inspect saas_platform_default")
    print("\n5. Execute commands in Superset container:")
    print("   docker-compose exec superset superset db upgrade")
    print("   docker-compose exec superset superset init")

def main():
    print("=== Superset Status Check ===\n")
    
    # Check Docker services
    services_running = check_docker_services()
    
    if not services_running:
        print("\n⚠ Some services are not running")
        response = input("Would you like to start them? (y/n): ")
        if response.lower() == 'y':
            if start_services():
                services_running = True
            else:
                print("\n✗ Failed to start services")
                print_troubleshooting()
                return
    
    # Check Superset health
    check_superset_health()
    
    # Check database configuration
    check_database_in_superset()
    
    # Print access information
    print_access_info()
    
    print("\n\n=== Next Steps ===\n")
    print("1. Make sure all services show as 'Running'")
    print("2. Verify you can access Superset UI in browser")
    print("3. Run setup script: python3 superset/setup_superset_complete.py")
    print("4. Import dashboard configurations")

if __name__ == "__main__":
    main()