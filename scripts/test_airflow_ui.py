#!/usr/bin/env python3
"""
Test Airflow UI Access
"""

import requests
from requests.auth import HTTPBasicAuth

def test_ui_access():
    """Test various UI endpoints"""
    base_url = "http://localhost:8080"
    auth = HTTPBasicAuth('admin', 'admin_password_2024')
    
    tests = [
        ("Health Check", "/health", None, 200),
        ("Login Page", "/login/", None, 200),
        ("API DAGs", "/api/v1/dags", auth, 200),
        ("Home (redirect)", "/home", None, 302),
        ("DAGs Page", "/dags", auth, 200),
    ]
    
    print("Testing Airflow UI Access")
    print("=" * 50)
    
    all_passed = True
    
    for name, endpoint, use_auth, expected_code in tests:
        url = base_url + endpoint
        try:
            if use_auth:
                response = requests.get(url, auth=use_auth, allow_redirects=False)
            else:
                response = requests.get(url, allow_redirects=False)
            
            if response.status_code == expected_code:
                print(f"✅ {name}: {response.status_code} (Expected: {expected_code})")
            else:
                print(f"❌ {name}: {response.status_code} (Expected: {expected_code})")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ All tests passed!")
        print("\nAirflow UI is working properly.")
        print("Access it at: http://localhost:8080")
        print("Login with: admin / admin_password_2024")
    else:
        print("❌ Some tests failed.")
        print("\nTroubleshooting steps:")
        print("1. Clear browser cache and cookies")
        print("2. Try incognito/private browsing mode")
        print("3. Use a different browser")
        print("4. Check docker logs: docker logs saas_platform_airflow_webserver")

if __name__ == "__main__":
    test_ui_access()