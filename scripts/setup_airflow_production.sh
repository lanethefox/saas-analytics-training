#!/bin/bash
set -e

echo "=== Setting up Airflow for Production ==="

# 1. Ensure containers are running
echo "1. Checking container status..."
docker-compose ps | grep -E "(postgres|airflow)" || {
    echo "Starting Airflow containers..."
    docker-compose up -d airflow-webserver airflow-scheduler
    sleep 10
}

# 2. Copy necessary scripts
echo "2. Copying scripts to containers..."
docker cp scripts/run_analytics_pipeline.py saas_platform_airflow_scheduler:/opt/airflow/dags/
docker cp scripts/run_analytics_pipeline.py saas_platform_airflow_webserver:/opt/airflow/dags/

# 3. Create logs directory in containers
echo "3. Setting up logs directory..."
docker exec saas_platform_airflow_scheduler mkdir -p /opt/airflow/logs
docker exec saas_platform_airflow_webserver mkdir -p /opt/airflow/logs

# 4. Test database connection
echo "4. Testing database connection..."
docker exec saas_platform_airflow_scheduler python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    port=5432,
    database='saas_platform_dev',
    user='saas_user',
    password='saas_secure_password_2024'
)
print('✅ Database connection successful')
conn.close()
"

# 5. List available DAGs
echo -e "\n5. Available DAGs:"
docker exec saas_platform_airflow_scheduler airflow dags list | grep -E "dag_id|analytics|test" | grep -v "===="

# 6. Unpause production DAGs
echo -e "\n6. Unpausing production DAGs..."
docker exec saas_platform_airflow_scheduler airflow dags unpause analytics_pipeline_hybrid || true
docker exec saas_platform_airflow_scheduler airflow dags unpause daily_analytics_refresh || true

echo -e "\n=== Airflow Production Setup Complete ==="
echo "Access Airflow UI at: http://localhost:8080"
echo "Username: admin"
echo "Password: admin_password_2024"
echo ""
echo "To trigger the analytics pipeline:"
echo "  ./scripts/run_analytics_pipeline.py"
echo ""
echo "To trigger via Airflow (if scheduler is working):"
echo "  docker exec saas_platform_airflow_scheduler airflow dags trigger analytics_pipeline_hybrid"