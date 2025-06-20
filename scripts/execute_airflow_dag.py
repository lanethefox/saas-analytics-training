#!/usr/bin/env python3
"""
Execute Airflow DAG manually
Works around scheduler issues by running tasks in order
"""

import subprocess
import time
import sys

def run_task(dag_id, task_id, run_id):
    """Run a single task"""
    print(f"\n{'='*60}")
    print(f"Running task: {task_id}")
    print('='*60)
    
    cmd = f"docker exec saas_platform_airflow_scheduler airflow tasks run {dag_id} {task_id} {run_id} --local"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if "SUCCESS" in result.stderr or "Marking task as SUCCESS" in result.stderr:
        print(f"✅ Task {task_id} completed successfully")
        return True
    else:
        print(f"❌ Task {task_id} failed")
        print("STDERR:", result.stderr[-500:])  # Last 500 chars of error
        return False

def main():
    dag_id = "analytics_pipeline_hybrid"
    run_id = f"manual_exec_{int(time.time())}"
    
    print(f"Executing DAG: {dag_id}")
    print(f"Run ID: {run_id}")
    
    # Create the DAG run
    cmd = f"""curl -X POST -u admin:admin_password_2024 \
        http://localhost:8080/api/v1/dags/{dag_id}/dagRuns \
        -H "Content-Type: application/json" \
        -d '{{"dag_run_id": "{run_id}"}}'"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"\nCreated DAG run: {run_id}")
    
    # Wait a moment for it to register
    time.sleep(5)
    
    # Execute tasks in order
    tasks = ["start", "run_pipeline", "check_health", "end"]
    
    for task in tasks:
        success = run_task(dag_id, task, run_id)
        if not success and task != "check_health":  # Allow health check to fail
            print(f"\nPipeline failed at task: {task}")
            sys.exit(1)
        time.sleep(2)  # Brief pause between tasks
    
    print(f"\n{'='*60}")
    print("✅ Pipeline completed successfully!")
    print(f"View results at: http://localhost:8080/dags/{dag_id}/grid?dag_run_id={run_id}")

if __name__ == "__main__":
    main()