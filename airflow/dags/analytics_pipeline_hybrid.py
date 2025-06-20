"""
Analytics Pipeline Hybrid DAG
Uses PythonOperator to run our proven analytics pipeline script
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import subprocess
import json
import os

# Default arguments
default_args = {
    'owner': 'analytics-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Create DAG
dag = DAG(
    'analytics_pipeline_hybrid',
    default_args=default_args,
    description='Production analytics pipeline using proven Python script',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    max_active_runs=1,
    tags=['analytics', 'production', 'dbt']
)

def run_analytics_pipeline(**context):
    """Run the analytics pipeline script"""
    # Import and run the pipeline directly
    import sys
    sys.path.insert(0, '/opt/airflow/dags')
    
    # Import the container-aware pipeline
    try:
        from run_analytics_pipeline_container import AnalyticsPipeline
    except ImportError:
        # Fallback to subprocess if module not found
        result = subprocess.run(
            ['python3', '/opt/airflow/dags/run_analytics_pipeline.py'],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        if result.returncode != 0:
            raise Exception(f"Pipeline failed with return code {result.returncode}")
        return "Pipeline completed via subprocess"
    
    # Run the pipeline
    pipeline = AnalyticsPipeline()
    success = pipeline.run_pipeline()
    
    # Get results
    if hasattr(pipeline, 'results'):
        results = pipeline.results
        # Push metrics to XCom
        context['task_instance'].xcom_push(key='pipeline_results', value=results)
        context['task_instance'].xcom_push(key='total_customers', value=results.get('final_metrics', {}).get('total_customers', 0))
        context['task_instance'].xcom_push(key='total_mrr', value=results.get('final_metrics', {}).get('total_mrr', 0))
        
        print(f"\n✅ Pipeline completed!")
        print(f"   Total Customers: {results.get('final_metrics', {}).get('total_customers', 0)}")
        print(f"   Total MRR: ${results.get('final_metrics', {}).get('total_mrr', 0):,.2f}")
    
    if not success:
        raise Exception("Pipeline failed - no customers found")
    
    return "Pipeline completed successfully"

def check_pipeline_health(**context):
    """Check pipeline health metrics"""
    # Get metrics from previous task
    total_customers = context['task_instance'].xcom_pull(task_ids='run_pipeline', key='total_customers')
    total_mrr = context['task_instance'].xcom_pull(task_ids='run_pipeline', key='total_mrr')
    
    print(f"Checking pipeline health...")
    print(f"Total Customers: {total_customers}")
    print(f"Total MRR: ${total_mrr:,.2f}")
    
    # Health checks
    if total_customers < 1000:
        raise ValueError(f"Customer count too low: {total_customers}")
    
    if total_mrr < 1000000:
        raise ValueError(f"MRR too low: ${total_mrr:,.2f}")
    
    print("✅ All health checks passed!")
    return "Health checks passed"

# Define tasks
start = EmptyOperator(
    task_id='start',
    dag=dag
)

run_pipeline = PythonOperator(
    task_id='run_pipeline',
    python_callable=run_analytics_pipeline,
    dag=dag
)

check_health = PythonOperator(
    task_id='check_health',
    python_callable=check_pipeline_health,
    dag=dag
)

end = EmptyOperator(
    task_id='end',
    dag=dag
)

# Set dependencies
start >> run_pipeline >> check_health >> end