#!/usr/bin/env python3
"""
Airflow Dashboard - API-based interface
Works around Web UI issues
"""

import requests
import json
from datetime import datetime
from requests.auth import HTTPBasicAuth
import sys

BASE_URL = "http://localhost:8080/api/v1"
AUTH = HTTPBasicAuth('admin', 'admin_password_2024')

def list_dags():
    """List all DAGs"""
    response = requests.get(f"{BASE_URL}/dags", auth=AUTH)
    if response.status_code == 200:
        dags = response.json()['dags']
        print("\n📋 Available DAGs:")
        print("-" * 80)
        for dag in dags:
            status = "⏸️ Paused" if dag['is_paused'] else "▶️ Active"
            print(f"{status} {dag['dag_id']:<30} | {dag['description'][:40]}...")
        return dags
    else:
        print(f"Error: {response.status_code}")
        return []

def list_dag_runs(dag_id, limit=5):
    """List recent DAG runs"""
    response = requests.get(f"{BASE_URL}/dags/{dag_id}/dagRuns?limit={limit}", auth=AUTH)
    if response.status_code == 200:
        runs = response.json()['dag_runs']
        print(f"\n🏃 Recent runs for {dag_id}:")
        print("-" * 80)
        for run in runs:
            state_icon = {
                'success': '✅',
                'failed': '❌',
                'running': '🏃',
                'queued': '⏳'
            }.get(run['state'], '❓')
            
            start = run['start_date'] or 'Not started'
            print(f"{state_icon} {run['dag_run_id']:<30} | {run['state']:<10} | {start}")
        return runs
    else:
        print(f"Error: {response.status_code}")
        return []

def trigger_dag(dag_id):
    """Trigger a DAG run"""
    run_id = f"api_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    response = requests.post(
        f"{BASE_URL}/dags/{dag_id}/dagRuns",
        auth=AUTH,
        json={"dag_run_id": run_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Triggered DAG: {dag_id}")
        print(f"   Run ID: {data['dag_run_id']}")
        print(f"   State: {data['state']}")
        return data
    else:
        print(f"\n❌ Failed to trigger DAG: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main dashboard interface"""
    print("🚀 Airflow API Dashboard")
    print("=" * 80)
    
    while True:
        print("\nOptions:")
        print("1. List all DAGs")
        print("2. Show DAG runs")
        print("3. Trigger analytics pipeline")
        print("4. Trigger specific DAG")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            list_dags()
        
        elif choice == '2':
            dags = list_dags()
            if dags:
                dag_id = input("\nEnter DAG ID (or press Enter for analytics_pipeline_hybrid): ").strip()
                dag_id = dag_id or "analytics_pipeline_hybrid"
                list_dag_runs(dag_id)
        
        elif choice == '3':
            trigger_dag("analytics_pipeline_hybrid")
            print("\n💡 Note: Since scheduler auto-pickup has issues, you may need to run tasks manually:")
            print("   docker exec saas_platform_airflow_scheduler airflow tasks run analytics_pipeline_hybrid start <run_id>")
        
        elif choice == '4':
            dag_id = input("\nEnter DAG ID: ").strip()
            if dag_id:
                trigger_dag(dag_id)
        
        elif choice == '5':
            print("\nGoodbye! 👋")
            sys.exit(0)
        
        else:
            print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
        sys.exit(0)