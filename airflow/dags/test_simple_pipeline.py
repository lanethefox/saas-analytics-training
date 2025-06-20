"""
Test Simple Pipeline DAG
Tests basic Airflow functionality with our setup
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

# Default arguments
default_args = {
    'owner': 'test-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Create DAG
dag = DAG(
    'test_simple_pipeline',
    default_args=default_args,
    description='Simple test DAG',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['test']
)

# Start task
start = EmptyOperator(
    task_id='start',
    dag=dag
)

# Test database connection
def test_db_connection():
    """Test database connection"""
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            database='saas_platform_dev',
            user='saas_user',
            password='saas_secure_password_2024'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw.app_database_accounts")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"Successfully connected to database. Found {count} accounts.")
        return count
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        raise

test_db = PythonOperator(
    task_id='test_db_connection',
    python_callable=test_db_connection,
    dag=dag
)

# Run simple dbt command
run_dbt_debug = BashOperator(
    task_id='run_dbt_debug',
    bash_command='echo "Testing dbt connection..." && docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt debug --profiles-dir ."',
    dag=dag
)

# End task
end = EmptyOperator(
    task_id='end',
    dag=dag
)

# Set dependencies
start >> test_db >> run_dbt_debug >> end