#!/bin/bash
# Production Pipeline Runner
# Runs the analytics pipeline reliably

echo "=== Running Production Analytics Pipeline ==="
echo "Timestamp: $(date)"

# Option 1: Direct Python execution (most reliable)
echo -e "\n1. Running via Python script..."
cd /Users/lane/Development/Active/data-platform
python3 scripts/run_analytics_pipeline.py

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo -e "\n✅ Pipeline completed successfully!"
    echo "Results available in: logs/summary_$(date +%Y%m%d).txt"
else
    echo -e "\n❌ Pipeline failed. Check logs for details."
    exit 1
fi

# Option 2: Trigger via Airflow API (if scheduler is working)
echo -e "\n2. Creating Airflow DAG run for tracking..."
RUN_ID="production_$(date +%s)"
curl -X POST -u admin:admin_password_2024 \
    http://localhost:8080/api/v1/dags/analytics_pipeline_hybrid/dagRuns \
    -H "Content-Type: application/json" \
    -d "{\"dag_run_id\": \"$RUN_ID\"}" \
    -s -o /dev/null

echo -e "\nAirflow DAG run created: $RUN_ID"
echo "View in UI: http://localhost:8080/dags/analytics_pipeline_hybrid/grid?dag_run_id=$RUN_ID"

echo -e "\n=== Production Pipeline Complete ==="