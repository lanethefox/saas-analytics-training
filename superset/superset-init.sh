#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST} ${DATABASE_PORT}; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Create admin user if it doesn't exist
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin_password_2024 || true

# Initialize the database
superset db upgrade

# Create default roles and permissions
superset init

# Import example data if configured
if [ "$SUPERSET_LOAD_EXAMPLES" = "yes" ]; then
    superset load_examples
fi

# Start the web server
echo "Starting Superset..."
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger