#!/usr/bin/env python3
"""
Run the analytics pipeline via Airflow API
"""

import requests
import json
import time
import sys
from datetime import datetime

# Airflow API configuration
AIRFLOW_URL = "http://localhost:8080/api/v1"
AUTH = ("admin", "admin_password_2024")

def trigger_dag(dag_id):
    """Trigger a DAG run"""
    run_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    response = requests.post(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns",
        auth=AUTH,
        json={"dag_run_id": run_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Triggered DAG run: {data['dag_run_id']}")
        return data['dag_run_id']
    else:
        print(f"❌ Failed to trigger DAG: {response.text}")
        return None

def get_dag_run_status(dag_id, run_id):
    """Get status of a DAG run"""
    response = requests.get(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns/{run_id}",
        auth=AUTH
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_task_instances(dag_id, run_id):
    """Get task instances for a DAG run"""
    response = requests.get(
        f"{AIRFLOW_URL}/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
        auth=AUTH
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def monitor_dag_run(dag_id, run_id, timeout=300):
    """Monitor a DAG run until completion"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Get DAG run status
        dag_run = get_dag_run_status(dag_id, run_id)
        if not dag_run:
            print("Failed to get DAG run status")
            return False
        
        state = dag_run['state']
        print(f"\rDAG State: {state}", end='', flush=True)
        
        if state in ['success', 'failed']:
            print(f"\n{'✅' if state == 'success' else '❌'} DAG run completed with state: {state}")
            
            # Show task details
            tasks = get_task_instances(dag_id, run_id)
            if tasks:
                print("\nTask Summary:")
                for task in tasks['task_instances']:
                    task_state = task['state'] or 'pending'
                    icon = '✅' if task_state == 'success' else '❌' if task_state == 'failed' else '⏳'
                    print(f"  {icon} {task['task_id']}: {task_state}")
            
            return state == 'success'
        
        time.sleep(5)
    
    print(f"\n⏱️ Timeout reached after {timeout} seconds")
    return False

def main():
    # Parse arguments
    dag_id = sys.argv[1] if len(sys.argv) > 1 else "daily_analytics_refresh"
    
    print(f"=== Running Airflow Pipeline: {dag_id} ===")
    
    # Trigger the DAG
    run_id = trigger_dag(dag_id)
    if not run_id:
        sys.exit(1)
    
    # Monitor the run
    success = monitor_dag_run(dag_id, run_id)
    
    if success:
        print("\n✅ Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed or timed out")
        sys.exit(1)

if __name__ == "__main__":
    main()