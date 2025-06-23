# Troubleshooting Guide

## Common Deployment Issues

### 1. Data Generation Fails

**Symptoms:**
- Error: "relation raw.app_database_accounts does not exist"
- Data generation scripts fail
- dbt can't find source tables

**Solutions:**

1. **Check if raw schema exists:**
   ```bash
   docker-compose exec postgres psql -U saas_user -d saas_platform_dev -c "\dn"
   ```

2. **Manually create raw schema if missing:**
   ```bash
   docker-compose exec postgres psql -U saas_user -d saas_platform_dev -c "CREATE SCHEMA IF NOT EXISTS raw;"
   ```

3. **Check if initialization SQL ran:**
   ```bash
   docker-compose logs postgres | grep "docker-entrypoint-initdb.d"
   ```

4. **Run the educational data generator:**
   ```bash
   python3 scripts/generate_all_data.py --scale small
   ```

### 2. Database Connection Refused

**Symptoms:**
- psycopg2.OperationalError: could not connect to server
- Connection refused errors

**Solutions:**

1. **Ensure PostgreSQL is running:**
   ```bash
   docker-compose ps
   docker-compose up -d postgres
   ```

2. **Wait for PostgreSQL to be ready:**
   ```bash
   docker-compose exec postgres pg_isready -U saas_user
   ```

3. **Check PostgreSQL logs:**
   ```bash
   docker-compose logs postgres
   ```

### 3. Python Dependencies Missing

**Symptoms:**
- ImportError: No module named 'psycopg2'
- pip install fails

**Solutions:**

1. **Install psycopg2-binary:**
   ```bash
   pip3 install psycopg2-binary
   ```

2. **Use virtual environment:**
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   pip install psycopg2-binary
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   pip install psycopg2-binary
   ```

### 4. dbt Failures

**Symptoms:**
- dbt run fails with "relation does not exist"
- Source not found errors

**Solutions:**

1. **Ensure data is loaded first:**
   ```bash
   python3 scripts/generate_all_data.py --scale small
   ```

2. **Run dbt with debug info:**
   ```bash
   docker-compose exec dbt bash -c "cd /opt/dbt_project && dbt debug --profiles-dir ."
   ```

3. **Check dbt sources:**
   ```bash
   docker-compose exec dbt bash -c "cd /opt/dbt_project && dbt ls -m source:* --profiles-dir ."
   ```

### 5. Docker Memory Issues

**Symptoms:**
- Containers exit unexpectedly
- "Cannot allocate memory" errors
- Services become unresponsive

**Solutions:**

1. **Increase Docker memory (Docker Desktop):**
   - Open Docker Desktop settings
   - Resources → Advanced
   - Set Memory to at least 8GB

2. **Use lightweight mode:**
   ```bash
   # Stop heavy services
   docker-compose stop airflow grafana mlflow
   ```

3. **Run minimal setup:**
   ```bash
   # Only start core services
   docker-compose up -d postgres dbt superset
   ```

### 6. Port Conflicts

**Symptoms:**
- "bind: address already in use" errors
- Cannot access services

**Solutions:**

1. **Check what's using ports:**
   ```bash
   # macOS/Linux
   lsof -i :5432  # PostgreSQL
   lsof -i :8088  # Superset
   lsof -i :8888  # Jupyter
   
   # Windows
   netstat -ano | findstr :5432
   ```

2. **Change ports in docker-compose.yml:**
   ```yaml
   services:
     postgres:
       ports:
         - "5433:5432"  # Use 5433 instead
   ```

3. **Update connection strings:**
   ```bash
   python3 scripts/generate_all_data.py --port 5433
   ```

## Quick Fixes

### Reset Everything
```bash
# Complete reset (removes all data)
docker-compose down -v
rm -rf data logs
./setup.sh
```

### Reload Data Only
```bash
# Keep services running, just reload data
python3 scripts/generate_all_data.py --scale small
docker-compose exec dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ."
```

### Check Platform Health
```bash
# Run validation script
./validate_setup.sh
```

### View Container Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f dbt
docker-compose logs -f superset
```

### 8. Windows-Specific Issues

**Symptoms:**
- "setup.sh: command not found"
- Permission denied errors
- Line ending issues (CRLF vs LF)

**Solutions:**

1. **Use Windows setup scripts:**
   ```batch
   # Command Prompt
   setup.bat
   
   # PowerShell
   .\setup.ps1
   ```

2. **Enable script execution in PowerShell:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Fix line endings if using WSL:**
   ```bash
   dos2unix setup.sh
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Docker Desktop settings:**
   - Ensure WSL2 is enabled
   - Allocate at least 4GB RAM
   - Check "Use the WSL 2 based engine" in settings

## Schema Reference

The platform uses a **raw → transformed** architecture:

- **Source tables**: `raw.app_database_*` (e.g., `raw.app_database_accounts`)
- **dbt models**: Read from raw schema, write to public schema
- **Data generators**: Populate `raw.app_database_*` tables

See `database/SCHEMA_EXPLANATION.md` for detailed schema documentation.

## Getting Help

1. Check container logs: `docker-compose logs [service-name]`
2. Run validation: `./validate_setup.sh`
3. Review this guide
4. Create an issue on GitHub with:
   - Error messages
   - Output of `docker-compose ps`
   - Output of `./validate_setup.sh`
   - Your operating system