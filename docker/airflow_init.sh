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

# Initialize the Airflow database
echo "Initializing Airflow database..."
airflow db init

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