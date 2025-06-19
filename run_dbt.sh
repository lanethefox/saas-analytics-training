#!/bin/bash
echo "Starting dbt run..."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ."
echo "dbt run completed"