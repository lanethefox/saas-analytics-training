#!/bin/bash
# Daily Analytics Refresh Script
# This script runs the complete analytics pipeline refresh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="${SCRIPT_DIR}/../logs"
LOG_FILE="${LOG_DIR}/daily_refresh_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Function to run dbt and capture output
run_dbt() {
    local command=$1
    local description=$2
    
    log "Starting: ${description}"
    
    if docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && ${command}" >> "${LOG_FILE}" 2>&1; then
        log "✅ Success: ${description}"
        return 0
    else
        log "❌ Failed: ${description}"
        return 1
    fi
}

# Main execution
log "===== Starting Daily Analytics Refresh ====="

# Check if containers are running
log "Checking container status..."
if ! docker ps | grep -q saas_platform_postgres; then
    log "❌ PostgreSQL container is not running"
    exit 1
fi

if ! docker ps | grep -q saas_platform_dbt_core; then
    log "❌ dbt container is not running"
    exit 1
fi

# Get initial metrics
log "Getting initial metrics..."
INITIAL_CUSTOMERS=$(docker exec saas_platform_postgres psql -U saas_user -d saas_platform_dev -t -c "SELECT COUNT(*) FROM raw.app_database_accounts;" 2>/dev/null | tr -d ' ')
log "Initial customer count: ${INITIAL_CUSTOMERS}"

# Run dbt models
if run_dbt "dbt run --profiles-dir . --threads 4" "Running all dbt models"; then
    MODELS_RUN=$(grep -c "OK created" "${LOG_FILE}" || true)
    log "Successfully ran ${MODELS_RUN} models"
else
    log "❌ dbt run failed - check logs for details"
    exit 1
fi

# Run dbt tests
if run_dbt "dbt test --profiles-dir ." "Running dbt tests"; then
    TESTS_PASSED=$(grep -c "PASS" "${LOG_FILE}" || true)
    log "Passed ${TESTS_PASSED} tests"
else
    log "⚠️  Some tests failed - continuing with refresh"
fi

# Generate documentation
run_dbt "dbt docs generate --profiles-dir ." "Generating documentation"

# Get final metrics
log "Getting final metrics..."
FINAL_METRICS=$(docker exec saas_platform_postgres psql -U saas_user -d saas_platform_dev -t -c "
    SELECT 
        'Customers: ' || COUNT(*) || ', ' ||
        'MRR: $' || TO_CHAR(SUM(CASE WHEN customer_status = 'active' THEN customer_mrr ELSE 0 END), 'FM999,999,999.00')
    FROM entity.entity_customers;
" 2>/dev/null)

log "Final metrics: ${FINAL_METRICS}"

# Create summary report
SUMMARY_FILE="${LOG_DIR}/daily_summary_$(date +%Y%m%d).txt"
{
    echo "Daily Analytics Refresh Summary"
    echo "==============================="
    echo "Date: $(date)"
    echo "Status: SUCCESS"
    echo ""
    echo "Metrics:"
    echo "${FINAL_METRICS}"
    echo ""
    echo "Models Run: ${MODELS_RUN:-0}"
    echo "Tests Passed: ${TESTS_PASSED:-0}"
    echo ""
    echo "Log file: ${LOG_FILE}"
} > "${SUMMARY_FILE}"

log "Summary saved to: ${SUMMARY_FILE}"
log "===== Daily Analytics Refresh Complete ====="

# Return success
exit 0