# Airflow Setup and Operations Guide

## Overview

This document describes the Apache Airflow setup for the SaaS Analytics Platform, including configuration, DAGs, and operational procedures.

## Architecture

- **Executor**: LocalExecutor (runs tasks on the same machine as the scheduler)
- **Database**: PostgreSQL (shared with main application database)
- **Containers**:
  - `airflow-webserver`: Web UI on port 8080
  - `airflow-scheduler`: Task scheduler and executor
  - `airflow-init`: One-time database initialization

## Available DAGs

### 1. `analytics_pipeline_hybrid` (Recommended)
- **Schedule**: Daily at 2 AM
- **Description**: Production analytics pipeline using proven Python script
- **Features**:
  - Runs complete dbt transformation pipeline
  - Performs health checks on results
  - Stores metrics in XCom for monitoring
  - Handles errors gracefully

### 2. `daily_analytics_refresh`
- **Schedule**: Daily at 6 AM
- **Description**: Simple daily refresh of all dbt models
- **Tasks**:
  - dbt run (all models)
  - dbt test
  - dbt docs generate

### 3. `saas_analytics_pipeline`
- **Schedule**: Daily at 2 AM
- **Description**: Comprehensive pipeline with data quality checks
- **Features**:
  - Pre-flight data quality checks
  - Staged dbt transformations
  - Post-processing and notifications

## Access and Authentication

- **Web UI**: http://localhost:8080
- **Username**: admin
- **Password**: admin_password_2024

## Operations

### Starting Airflow

```bash
docker-compose up -d airflow-webserver airflow-scheduler
```

### Checking Status

```bash
# Container status
docker-compose ps | grep airflow

# List DAGs
docker exec saas_platform_airflow_scheduler airflow dags list

# Check scheduler logs
docker logs saas_platform_airflow_scheduler --tail 50
```

### Running Pipelines

#### Option 1: Direct Python Script (Recommended)
```bash
python3 scripts/run_analytics_pipeline.py
```

#### Option 2: Via Airflow CLI
```bash
# Trigger a DAG
docker exec saas_platform_airflow_scheduler airflow dags trigger daily_analytics_refresh

# Check DAG state
docker exec saas_platform_airflow_scheduler airflow dags state daily_analytics_refresh 2025-06-20
```

#### Option 3: Via Web UI
1. Navigate to http://localhost:8080
2. Login with admin/admin_password_2024
3. Find your DAG and click the "play" button

#### Option 4: Via API
```bash
# Trigger DAG
curl -X POST -u admin:admin_password_2024 \
  http://localhost:8080/api/v1/dags/daily_analytics_refresh/dagRuns \
  -H "Content-Type: application/json" \
  -d '{"conf": {}}'

# Check status
curl -u admin:admin_password_2024 \
  http://localhost:8080/api/v1/dags/daily_analytics_refresh/dagRuns
```

### Scheduling

DAGs are scheduled using cron expressions:
- `0 2 * * *` - Daily at 2 AM
- `0 6 * * *` - Daily at 6 AM
- `0 */4 * * *` - Every 4 hours
- `None` - Manual trigger only

### Monitoring

1. **Web UI Dashboard**: Shows DAG runs, task status, and logs
2. **Logs**: Available in `/opt/airflow/logs` within containers
3. **Metrics**: Pipeline results stored in `logs/pipeline_results_*.json`

## Troubleshooting

### Common Issues

1. **Tasks not starting**
   - Check scheduler logs: `docker logs saas_platform_airflow_scheduler`
   - Verify database connection
   - Restart scheduler: `docker-compose restart airflow-scheduler`

2. **DAG not appearing**
   - Wait 30 seconds for DAG discovery
   - Check for syntax errors in DAG file
   - Restart scheduler

3. **Database connection errors**
   - Verify PostgreSQL is running: `docker-compose ps postgres`
   - Check connection string in airflow.cfg
   - Test connection manually

### Manual Pipeline Execution

If Airflow scheduler has issues, use the direct Python script:

```bash
# Run full pipeline
python3 scripts/run_analytics_pipeline.py

# Results will be in:
# - logs/pipeline_YYYYMMDD_HHMMSS.log
# - logs/summary_YYYYMMDD.txt
```

## Best Practices

1. **Use the hybrid DAG** (`analytics_pipeline_hybrid`) for production
2. **Monitor pipeline duration** - Should complete in <60 seconds
3. **Check data quality metrics** after each run
4. **Keep DAGs simple** - Complex logic belongs in scripts
5. **Use XCom** for passing data between tasks

## Maintenance

### Daily Tasks
- Monitor DAG runs via Web UI
- Check for failed tasks and investigate logs

### Weekly Tasks
- Review pipeline performance metrics
- Clean up old logs: `find logs/ -name "*.log" -mtime +7 -delete`

### Monthly Tasks
- Update DAG schedules based on business needs
- Review and optimize slow-running tasks

## Emergency Procedures

### Pipeline Failure
1. Check logs: `docker logs saas_platform_airflow_scheduler`
2. Run manually: `python3 scripts/run_analytics_pipeline.py`
3. Investigate specific model failures in dbt logs

### Complete Reset
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker-compose down -v

# Restart everything
./setup.sh
```

## Contact

For issues or questions:
- Check logs first
- Review this documentation
- Run manual pipeline as fallback