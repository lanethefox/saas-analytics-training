"""
Daily Analytics Refresh Pipeline
Simple and reliable daily refresh for the SaaS analytics platform
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator

# Default arguments
default_args = {
    'owner': 'analytics-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 20),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'daily_analytics_refresh',
    default_args=default_args,
    description='Daily refresh of analytics platform data models',
    schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['analytics', 'dbt', 'daily']
)

# Start task
start = DummyOperator(
    task_id='start',
    dag=dag
)

# Run all dbt models with full refresh
dbt_run_all = BashOperator(
    task_id='dbt_run_all',
    bash_command="""
    docker exec saas_platform_dbt_core bash -c '
        cd /opt/dbt_project && 
        echo "Starting dbt run at $(date)" &&
        dbt run --profiles-dir . --full-refresh &&
        echo "dbt run completed at $(date)"
    '
    """,
    execution_timeout=timedelta(minutes=30),
    dag=dag
)

# Run dbt tests
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command="""
    docker exec saas_platform_dbt_core bash -c '
        cd /opt/dbt_project && 
        echo "Starting dbt tests at $(date)" &&
        dbt test --profiles-dir . &&
        echo "dbt tests completed at $(date)"
    '
    """,
    execution_timeout=timedelta(minutes=10),
    dag=dag
)

# Generate dbt documentation
dbt_docs = BashOperator(
    task_id='dbt_docs',
    bash_command="""
    docker exec saas_platform_dbt_core bash -c '
        cd /opt/dbt_project && 
        dbt docs generate --profiles-dir . &&
        echo "Documentation updated at $(date)"
    '
    """,
    dag=dag
)

# Get summary statistics
get_summary = BashOperator(
    task_id='get_summary',
    bash_command="""
    docker exec saas_platform_postgres psql -U saas_user -d saas_platform_dev -c "
        SELECT 
            'Refresh completed: ' || NOW() as status
        UNION ALL
        SELECT 
            'Total Customers: ' || COUNT(*)::text 
        FROM entity.entity_customers
        UNION ALL
        SELECT 
            'Total MRR: $' || TO_CHAR(total_mrr, 'FM999,999,999.00')
        FROM public.metrics_unified 
        WHERE metric_date = CURRENT_DATE
        UNION ALL
        SELECT 
            'Active Users: ' || COUNT(*)::text
        FROM entity.entity_users
        WHERE user_status = 'active';
    "
    """,
    dag=dag
)

# End task
end = DummyOperator(
    task_id='end',
    dag=dag,
    trigger_rule='all_done'
)

# Define task dependencies
start >> dbt_run_all >> dbt_test >> dbt_docs >> get_summary >> end