"""
Most basic test DAG
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'test',
    'start_date': datetime(2025, 6, 19),
    'retries': 0
}

dag = DAG(
    'test_basic',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
)

test_task = BashOperator(
    task_id='test_echo',
    bash_command='echo "Hello from Airflow!"',
    dag=dag
)