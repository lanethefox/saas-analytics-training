#!/bin/bash

# Script to verify that deterministic data was loaded correctly in Docker
echo "=========================================="
echo "Verifying Deterministic Data in Docker"
echo "=========================================="

# Function to run SQL query
run_query() {
    local query=$1
    docker exec -it saas_platform_postgres psql -U saas_user -d saas_platform_dev -t -c "$query" 2>/dev/null
}

# Check if Docker container is running
if ! docker ps | grep -q saas_platform_postgres; then
    echo "❌ Error: PostgreSQL container is not running"
    echo "Run 'docker-compose up -d postgres' first"
    exit 1
fi

echo ""
echo "📊 Data Summary:"
echo "------------------"

# Check each table
tables=("app_database_accounts" "app_database_locations" "app_database_devices" "app_database_users" "app_database_subscriptions")

for table in "${tables[@]}"; do
    count=$(run_query "SELECT COUNT(*) FROM raw.$table" | tr -d ' ')
    printf "%-30s: %s records\n" "$table" "$count"
done

echo ""
echo "🔍 Sample Data Verification:"
echo "-----------------------------"

# Check account 1
echo "Account 1 (The Lambert House):"
account_info=$(run_query "SELECT name, industry, employee_count FROM raw.app_database_accounts WHERE id = '1'")
echo "$account_info"

# Check location count for account 1
location_count=$(run_query "SELECT COUNT(*) FROM raw.app_database_locations WHERE customer_id = '1'" | tr -d ' ')
echo "Locations for Account 1: $location_count"

# Check device count for first location
first_location=$(run_query "SELECT id FROM raw.app_database_locations WHERE customer_id = '1' ORDER BY id LIMIT 1" | tr -d ' ')
if [ ! -z "$first_location" ]; then
    device_count=$(run_query "SELECT COUNT(*) FROM raw.app_database_devices WHERE location_id = '$first_location'" | tr -d ' ')
    echo "Devices at Location $first_location: $device_count"
fi

echo ""
echo "✅ Verification complete!"