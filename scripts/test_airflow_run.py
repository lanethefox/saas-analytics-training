#!/usr/bin/env python3
"""
Test Airflow DAG execution directly
"""

import subprocess
import time
import json

def run_command(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("Testing Airflow DAG execution...")
    
    # 1. Check if scheduler is healthy
    print("\n1. Checking scheduler health...")
    code, out, err = run_command("docker-compose ps airflow-scheduler")
    print(out)
    
    # 2. List available DAGs
    print("\n2. Listing available DAGs...")
    code, out, err = run_command("docker exec saas_platform_airflow_scheduler airflow dags list")
    if code == 0:
        print("Available DAGs:")
        for line in out.split('\n')[1:]:  # Skip header
            if line.strip():
                dag_id = line.split('|')[0].strip()
                if dag_id:
                    print(f"  - {dag_id}")
    
    # 3. Run a simple task directly
    print("\n3. Running a simple task directly...")
    code, out, err = run_command("""
        docker exec saas_platform_airflow_scheduler python3 -c "
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
print(f'Database connection successful. Found {count} accounts.')
cursor.close()
conn.close()
"
    """)
    if code == 0:
        print(out)
    else:
        print(f"Error: {err}")
    
    # 4. Run dbt debug
    print("\n4. Running dbt debug...")
    code, out, err = run_command(
        'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt debug --profiles-dir ."'
    )
    if code == 0:
        print("dbt debug successful")
    else:
        print(f"dbt debug failed: {err}")
    
    # 5. Create and trigger a minimal DAG via API
    print("\n5. Creating minimal test DAG run via API...")
    code, out, err = run_command("""
        curl -X POST -u admin:admin_password_2024 \
          http://localhost:8080/api/v1/dags/test_simple_pipeline/dagRuns \
          -H "Content-Type: application/json" \
          -d '{"dag_run_id": "test_run_' + str(int(time.time())) + '"}'
    """)
    
    if code == 0:
        try:
            result = json.loads(out)
            dag_run_id = result.get('dag_run_id')
            print(f"Created DAG run: {dag_run_id}")
            
            # Wait and check status
            print("Waiting 10 seconds...")
            time.sleep(10)
            
            code, out, err = run_command(f"""
                curl -u admin:admin_password_2024 \
                  "http://localhost:8080/api/v1/dags/test_simple_pipeline/dagRuns/{dag_run_id}/taskInstances" \
                  | python3 -m json.tool
            """)
            
            if code == 0:
                tasks = json.loads(out)
                print("\nTask states:")
                for task in tasks.get('task_instances', []):
                    print(f"  - {task['task_id']}: {task['state']}")
        except:
            print("Could not parse API response")

if __name__ == "__main__":
    main()