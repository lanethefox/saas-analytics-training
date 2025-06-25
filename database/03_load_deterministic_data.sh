#!/bin/bash

# =====================================================
# Deterministic Data Loading Script for Docker
# =====================================================
# This script loads deterministic data using the data generation pipeline
# It's designed to run inside the Docker container during initialization
# 
# Prerequisites:
# - PostgreSQL database must be running and accessible
# - Python environment with required packages installed
# - Schema must be created (01_main_schema.sql)
# 
# This script:
# 1. Waits for database to be ready
# 2. Sets up Python environment if needed
# 3. Runs the deterministic data generation pipeline
# 4. Validates the loaded data
# =====================================================

set -e  # Exit on error

echo "=========================================="
echo "Starting Deterministic Data Loading"
echo "=========================================="

# Database connection parameters (from Docker environment)
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-saas_user}"
DB_PASSWORD="${DB_PASSWORD:-saas_secure_password_2024}"
DB_NAME="${DB_NAME:-saas_platform_dev}"

# Export for Python scripts
export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME

# Function to check if database is ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; do
        echo "Database is not ready yet. Waiting..."
        sleep 2
    done
    echo "Database is ready!"
}

# Function to check if data already exists
check_existing_data() {
    local table=$1
    local count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
        "SELECT COUNT(*) FROM raw.$table" 2>/dev/null || echo "0")
    echo $count
}

# Function to run a Python script with error handling
run_python_script() {
    local script=$1
    local description=$2
    
    echo ""
    echo "Running: $description"
    echo "----------------------------------------"
    
    if python3 /app/scripts/$script; then
        echo "✓ $description completed successfully"
    else
        echo "✗ $description failed"
        return 1
    fi
}

# Main execution
main() {
    # Wait for database to be ready
    wait_for_db
    
    # Check if data already exists
    account_count=$(check_existing_data "app_database_accounts")
    
    if [ "$account_count" -gt "0" ]; then
        echo ""
        echo "⚠️  WARNING: Data already exists in the database"
        echo "   Accounts found: $account_count"
        echo ""
        echo "To reload data, first truncate the tables or drop the database."
        echo "Skipping data generation to preserve existing data."
        exit 0
    fi
    
    # Install Python dependencies if needed
    if [ -f "/app/requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r /app/requirements.txt > /dev/null 2>&1
    fi
    
    # Run the deterministic data generation pipeline
    echo ""
    echo "=========================================="
    echo "Running Deterministic Data Generation"
    echo "=========================================="
    
    # Change to the app directory
    cd /app
    
    # Run the main generation script
    # The script will automatically answer 'y' to prompts in Docker environment
    export DOCKER_ENV=true
    export PYTHONUNBUFFERED=1
    
    if python3 scripts/generate_all_deterministic.py; then
        echo ""
        echo "✅ Data generation completed successfully!"
        
        # Show summary statistics
        echo ""
        echo "=========================================="
        echo "Data Loading Summary"
        echo "=========================================="
        
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<EOF
SELECT 'Accounts' as entity, COUNT(*) as count FROM raw.app_database_accounts
UNION ALL
SELECT 'Locations' as entity, COUNT(*) as count FROM raw.app_database_locations
UNION ALL
SELECT 'Devices' as entity, COUNT(*) as count FROM raw.app_database_devices
UNION ALL
SELECT 'Users' as entity, COUNT(*) as count FROM raw.app_database_users
UNION ALL
SELECT 'Subscriptions' as entity, COUNT(*) as count FROM raw.app_database_subscriptions
ORDER BY entity;
EOF
        
    else
        echo ""
        echo "❌ Data generation failed!"
        echo "Please check the logs above for error details."
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ Deterministic data loading complete!"
    echo "=========================================="
}

# Run main function
main