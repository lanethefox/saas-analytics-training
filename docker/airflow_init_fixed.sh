#!/bin/bash
set -e

echo "=== Airflow Initialization Script ==="

# Wait for the database to be ready
echo "Waiting for PostgreSQL database to be ready..."
while ! pg_isready -h postgres -p 5432 -U saas_user; do
    echo "Waiting for database connection..."
    sleep 2
done
echo "Database is ready!"

# Set Airflow home
export AIRFLOW_HOME=/opt/airflow

# Check if database has been initialized
echo "Checking if Airflow database needs initialization..."
INITIALIZED=$(python3 -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='saas_platform_dev',
        user='saas_user',
        password='saas_secure_password_2024'
    )
    cursor = conn.cursor()
    cursor.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'alembic_%'\")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(count > 0)
except Exception as e:
    print(False)
")

if [ "$INITIALIZED" = "False" ]; then
    echo "Airflow database not initialized. Running migrations..."
    # Use upgrade instead of init to avoid the serialized_dag issue
    airflow db upgrade
else
    echo "Airflow database already initialized."
fi

# Create admin user if it doesn't exist
echo "Creating Airflow admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin_password_2024 || echo "User already exists"

echo "=== Airflow initialization completed ==="

# Start the requested service
echo "Starting Airflow service: $1"
exec airflow "$@"