"""
Entity-Centric Data Platform Pipeline
Comprehensive implementation of three-table entity architecture:
- Atomic entity tables (current state)
- Entity history tables (complete change tracking)
- Strategic grain tables (business-relevant aggregations)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator

# Default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'entity_centric_pipeline',
    default_args=default_args,
    description='Entity-Centric Data Platform - Complete three-table architecture',
    schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['entity-centric', 'ecm', 'three-table']
)

# Start pipeline
start_pipeline = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

# dbt source freshness check
dbt_source_freshness = BashOperator(
    task_id='dbt_source_freshness',
    bash_command="""
    cd /opt/dbt_project && 
    dbt source freshness --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# dbt run staging models
dbt_run_staging = BashOperator(
    task_id='dbt_run_staging',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:staging --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# dbt run intermediate models
dbt_run_intermediate = BashOperator(
    task_id='dbt_run_intermediate',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:intermediate --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# Entity Atomic Tables (Current State)
dbt_run_entities_atomic = BashOperator(
    task_id='dbt_run_entities_atomic',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:atomic --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# Entity History Tables (Complete Change Tracking)
dbt_run_entities_history = BashOperator(
    task_id='dbt_run_entities_history',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:history --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# Entity Grain Tables (Strategic Aggregations)
dbt_run_entities_grain = BashOperator(
    task_id='dbt_run_entities_grain',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:grain --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# dbt run mart models (Domain-specific analytics)
dbt_run_marts = BashOperator(
    task_id='dbt_run_marts',
    bash_command="""
    cd /opt/dbt_project && 
    dbt run --select tag:mart --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# dbt test all models
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command="""
    cd /opt/dbt_project && 
    dbt test --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# Generate documentation
dbt_docs_generate = BashOperator(
    task_id='dbt_docs_generate',
    bash_command="""
    cd /opt/dbt_project && 
    dbt docs generate --profiles-dir /opt/dbt_project
    """,
    dag=dag
)

# End pipeline
end_pipeline = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Entity-Centric Pipeline Dependencies
# This implements the sophisticated three-table pattern for each entity:
# 1. Atomic tables for current-state operational analytics
# 2. History tables for temporal analytics and change tracking  
# 3. Grain tables for performance-optimized strategic analytics

start_pipeline >> dbt_source_freshness >> dbt_run_staging

dbt_run_staging >> dbt_run_intermediate
dbt_run_intermediate >> dbt_run_entities_atomic

# Atomic tables must complete before history and grain tables
# History tables track all changes over time
# Grain tables provide strategic aggregations
dbt_run_entities_atomic >> [dbt_run_entities_history, dbt_run_entities_grain]

# Both history and grain tables feed into marts
[dbt_run_entities_history, dbt_run_entities_grain] >> dbt_run_marts

# Final validation and documentation
dbt_run_marts >> dbt_test >> dbt_docs_generate >> end_pipeline
