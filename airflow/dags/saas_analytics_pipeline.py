"""
SaaS Analytics Platform Daily Pipeline
Orchestrates the complete data refresh for the bar management analytics platform
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.utils.task_group import TaskGroup

# Default arguments
default_args = {
    'owner': 'analytics-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data-team@company.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'saas_analytics_pipeline',
    default_args=default_args,
    description='Daily analytics refresh for bar management SaaS platform',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['analytics', 'dbt', 'entity-centric', 'production']
)

# Start pipeline
start_pipeline = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

# Data quality checks on source data
with TaskGroup("data_quality_checks", dag=dag) as data_quality_checks:
    
    check_account_completeness = PostgresOperator(
        task_id='check_account_completeness',
        postgres_conn_id='postgres_default',
        sql="""
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 'FAIL: No accounts found'
                WHEN COUNT(*) < 1000 THEN 'WARN: Low account count (' || COUNT(*) || ')'
                ELSE 'PASS: ' || COUNT(*) || ' accounts found'
            END as status
        FROM raw.app_database_accounts;
        """,
        dag=dag
    )
    
    check_data_freshness = PostgresOperator(
        task_id='check_data_freshness',
        postgres_conn_id='postgres_default',
        sql="""
        SELECT 
            CASE 
                WHEN MAX(created_at) < CURRENT_DATE - INTERVAL '2 days' 
                THEN 'FAIL: Data is stale'
                ELSE 'PASS: Data is fresh'
            END as status
        FROM raw.app_database_accounts;
        """,
        dag=dag
    )

# dbt tasks using Docker exec
dbt_command_prefix = "docker exec saas_platform_dbt_core bash -c 'cd /opt/dbt_project && "

# Source freshness check
dbt_source_freshness = BashOperator(
    task_id='dbt_source_freshness',
    bash_command=dbt_command_prefix + "dbt source freshness --profiles-dir . --output target/sources.json'",
    dag=dag
)

# Run dbt models by layer
with TaskGroup("dbt_transformations", dag=dag) as dbt_transformations:
    
    # Staging layer - clean and type raw data
    dbt_run_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command=dbt_command_prefix + "dbt run --select staging.* --profiles-dir .'",
        dag=dag
    )
    
    # Intermediate layer - apply business logic
    dbt_run_intermediate = BashOperator(
        task_id='dbt_run_intermediate',
        bash_command=dbt_command_prefix + "dbt run --select intermediate.* --profiles-dir .'",
        dag=dag
    )
    
    # Entity layer - build entity-centric models
    with TaskGroup("entity_models", dag=dag) as entity_models:
        
        # Core entities (atomic tables)
        dbt_run_entity_customers = BashOperator(
            task_id='dbt_run_entity_customers',
            bash_command=dbt_command_prefix + "dbt run --select entity.entity_customers --profiles-dir .'",
            dag=dag
        )
        
        dbt_run_entity_users = BashOperator(
            task_id='dbt_run_entity_users',
            bash_command=dbt_command_prefix + "dbt run --select entity.entity_users --profiles-dir .'",
            dag=dag
        )
        
        dbt_run_entity_devices = BashOperator(
            task_id='dbt_run_entity_devices',
            bash_command=dbt_command_prefix + "dbt run --select entity.entity_devices --profiles-dir .'",
            dag=dag
        )
        
        dbt_run_entity_locations = BashOperator(
            task_id='dbt_run_entity_locations',
            bash_command=dbt_command_prefix + "dbt run --select entity.entity_locations --profiles-dir .'",
            dag=dag
        )
        
        # History and grain tables
        dbt_run_entity_history = BashOperator(
            task_id='dbt_run_entity_history',
            bash_command=dbt_command_prefix + "dbt run --select entity.*_history --profiles-dir .'",
            dag=dag
        )
        
        dbt_run_entity_grain = BashOperator(
            task_id='dbt_run_entity_grain',
            bash_command=dbt_command_prefix + "dbt run --select entity.*_daily entity.*_weekly entity.*_monthly --profiles-dir .'",
            dag=dag
        )
    
    # Mart layer - domain-specific views
    dbt_run_marts = BashOperator(
        task_id='dbt_run_marts',
        bash_command=dbt_command_prefix + "dbt run --select mart.* --profiles-dir .'",
        dag=dag
    )
    
    # Metrics layer - pre-calculated KPIs
    dbt_run_metrics = BashOperator(
        task_id='dbt_run_metrics',
        bash_command=dbt_command_prefix + "dbt run --select metrics.* --profiles-dir .'",
        dag=dag
    )
    
    # Define dependencies within dbt transformations
    dbt_run_staging >> dbt_run_intermediate
    dbt_run_intermediate >> entity_models
    entity_models >> dbt_run_marts
    dbt_run_marts >> dbt_run_metrics

# dbt tests
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command=dbt_command_prefix + "dbt test --profiles-dir . --store-failures'",
    dag=dag,
    trigger_rule='all_done'  # Run tests even if some models fail
)

# Generate documentation
dbt_docs_generate = BashOperator(
    task_id='dbt_docs_generate',
    bash_command=dbt_command_prefix + "dbt docs generate --profiles-dir .'",
    dag=dag
)

# Post-processing tasks
with TaskGroup("post_processing", dag=dag) as post_processing:
    
    # Refresh Superset datasets
    refresh_superset_cache = BashOperator(
        task_id='refresh_superset_cache',
        bash_command="""
        echo "Refreshing Superset cache..."
        # Add Superset cache refresh commands here
        """,
        dag=dag
    )
    
    # Calculate data quality metrics
    calculate_data_quality = PostgresOperator(
        task_id='calculate_data_quality',
        postgres_conn_id='postgres_default',
        sql="""
        INSERT INTO analytics.data_quality_metrics (
            run_date,
            total_customers,
            active_customers,
            data_freshness_hours,
            test_failures
        )
        SELECT 
            CURRENT_DATE,
            COUNT(*) as total_customers,
            COUNT(*) FILTER (WHERE customer_status = 'active') as active_customers,
            EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 as data_freshness_hours,
            0 as test_failures  -- Will be updated by separate process
        FROM entity.entity_customers;
        """,
        dag=dag
    )

# Notifications
send_completion_notification = BashOperator(
    task_id='send_completion_notification',
    bash_command="""
    echo "Pipeline completed successfully!"
    echo "Total MRR: $(psql -h postgres -U saas_user -d saas_platform_dev -t -c 'SELECT total_mrr FROM public.metrics_unified WHERE metric_date = CURRENT_DATE;')"
    """,
    dag=dag,
    trigger_rule='all_success'
)

# End pipeline
end_pipeline = DummyOperator(
    task_id='end_pipeline',
    dag=dag,
    trigger_rule='all_done'
)

# Define pipeline dependencies
start_pipeline >> data_quality_checks >> dbt_source_freshness
dbt_source_freshness >> dbt_transformations
dbt_transformations >> dbt_test
dbt_transformations >> dbt_docs_generate
[dbt_test, dbt_docs_generate] >> post_processing
post_processing >> send_completion_notification
send_completion_notification >> end_pipeline

# Add cleanup task that always runs
cleanup_temp_tables = PostgresOperator(
    task_id='cleanup_temp_tables',
    postgres_conn_id='postgres_default',
    sql="""
    -- Clean up any temporary tables older than 7 days
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN 
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'staging' 
            AND tablename LIKE 'tmp_%'
            AND tablename < 'tmp_' || TO_CHAR(CURRENT_DATE - INTERVAL '7 days', 'YYYYMMDD')
        LOOP
            EXECUTE 'DROP TABLE IF EXISTS staging.' || quote_ident(r.tablename);
        END LOOP;
    END $$;
    """,
    dag=dag,
    trigger_rule='all_done'
)

end_pipeline >> cleanup_temp_tables