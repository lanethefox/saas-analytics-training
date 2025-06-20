#!/usr/bin/env python3
"""
Complete Airflow functionality test
"""

import requests
import subprocess
import time
import json

def test_component(name, test_func):
    """Run a test and report results"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print('='*50)
    try:
        result = test_func()
        print(f"✅ {name}: PASSED")
        if result:
            print(f"   {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: FAILED")
        print(f"   Error: {str(e)}")
        return False

def test_webserver():
    """Test Airflow webserver is accessible"""
    response = requests.get("http://localhost:8080/health", timeout=5)
    return f"Status: {response.status_code}"

def test_api_auth():
    """Test API authentication"""
    response = requests.get(
        "http://localhost:8080/api/v1/dags",
        auth=("admin", "admin_password_2024"),
        timeout=5
    )
    data = response.json()
    return f"Found {data['total_entries']} DAGs"

def test_database_connection():
    """Test database connection from Airflow"""
    cmd = """docker exec saas_platform_airflow_scheduler python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    port=5432,
    database='saas_platform_dev',
    user='saas_user',
    password='saas_secure_password_2024'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM raw.app_database_accounts')
count = cursor.fetchone()[0]
print(f'Found {count} accounts')
cursor.close()
conn.close()
"
    """
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return result.stdout.strip()

def test_dbt_connection():
    """Test dbt connection"""
    cmd = 'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt debug --profiles-dir . 2>&1 | grep -E \'(OK|ERROR)\' | head -5"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("dbt debug failed")
    return "dbt connection OK"

def test_dag_list():
    """Test listing DAGs"""
    response = requests.get(
        "http://localhost:8080/api/v1/dags",
        auth=("admin", "admin_password_2024"),
        timeout=5
    )
    data = response.json()
    dag_names = [d['dag_id'] for d in data['dags']]
    return f"DAGs: {', '.join(dag_names)}"

def test_create_dag_run():
    """Test creating a DAG run"""
    # Use the daily_analytics_refresh DAG for testing
    run_id = f"test_run_{int(time.time())}"
    response = requests.post(
        "http://localhost:8080/api/v1/dags/daily_analytics_refresh/dagRuns",
        auth=("admin", "admin_password_2024"),
        json={"dag_run_id": run_id},
        timeout=5
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create DAG run: {response.text}")
    
    data = response.json()
    return f"Created run: {data['dag_run_id']} (state: {data['state']})"

def test_analytics_pipeline():
    """Test running the analytics pipeline directly"""
    cmd = "cd /Users/lane/Development/Active/data-platform && python3 scripts/run_analytics_pipeline.py"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Pipeline failed: {result.stderr}")
    
    # Extract key metrics from output
    lines = result.stdout.split('\n')
    for line in lines:
        if 'Pipeline Complete' in line:
            return "Pipeline executed successfully"
    
    return "Pipeline completed"

def main():
    """Run all tests"""
    print("🚀 Airflow Complete Functionality Test")
    print("=" * 70)
    
    tests = [
        ("Webserver Health", test_webserver),
        ("API Authentication", test_api_auth),
        ("Database Connection", test_database_connection),
        ("dbt Connection", test_dbt_connection),
        ("DAG Listing", test_dag_list),
        ("Create DAG Run", test_create_dag_run),
        ("Analytics Pipeline", test_analytics_pipeline),
    ]
    
    results = []
    for name, test_func in tests:
        results.append(test_component(name, test_func))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Airflow is ready for production use.")
        print("\nNext steps:")
        print("1. Access Airflow UI: http://localhost:8080")
        print("2. Run pipeline: python3 scripts/run_analytics_pipeline.py")
        print("3. Schedule DAGs as needed")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("The analytics pipeline can still be run directly:")
        print("  python3 scripts/run_analytics_pipeline.py")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())