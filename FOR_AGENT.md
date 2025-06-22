# B2B SaaS Analytics Platform - Agent Guide

This document provides comprehensive context for AI agents working with the B2B SaaS Analytics Training Platform.

## 🎯 Platform Overview

This is an educational data platform simulating a B2B SaaS company that provides IoT tap sensors for bars and restaurants. The platform includes:
- Realistic data generation (accounts, locations, devices, users, subscriptions)
- Modern data stack (PostgreSQL, dbt, Superset, Jupyter)
- Pre-built analytics models and dashboards
- Educational exercises and projects

## 🏗️ Architecture

### Core Services (Default)
- **PostgreSQL + pgvector**: Primary database with vector extension
- **Redis**: Caching layer
- **dbt Core**: Data transformation framework
- **Apache Superset**: Business intelligence tool
- **Jupyter Lab**: Interactive notebooks

### Optional Services (--full flag)
- Apache Airflow: Workflow orchestration
- MLflow: Machine learning platform
- Grafana + Prometheus: Monitoring
- MinIO: Object storage

## 📁 Project Structure

```
data-platform/
├── database/                 # SQL schemas and initialization
│   ├── 01_main_schema.sql  # Enhanced schema with all tables
│   └── 02_superset_init.sql # Superset database setup
├── dbt_project/             # dbt transformations
│   ├── models/              # SQL models organized by layer
│   │   ├── staging/         # Source data cleaning
│   │   ├── intermediate/    # Business logic
│   │   ├── entity/          # Core business entities
│   │   └── metrics/         # KPI calculations
│   └── tests/               # Data quality tests
├── docker/                  # Container configurations
│   ├── dbt/                # dbt Dockerfile
│   ├── jupyter/            # Jupyter Dockerfile
│   └── superset/           # Superset Dockerfile
├── education/              # Learning materials
│   ├── exercises/          # Hands-on labs
│   ├── projects/           # Quarterly projects
│   └── workday_sims/       # Day-in-life simulations
├── scripts/                # Data generation and utilities
│   └── generate_educational_data.py  # Main data generator
├── docker-compose.yml      # Core services configuration
├── docker-compose.full.yml # Full stack configuration
└── setup.sh               # One-click setup script
```

## 🚀 Setup Instructions

### Prerequisites
- Docker Desktop installed and running
- 4GB RAM available (8GB for full stack)
- Python 3.8+ (for local development)
- Windows users: PowerShell or Command Prompt

### Quick Start

#### Linux/macOS
```bash
# Clone repository
git clone <repository-url>
cd data-platform

# Run setup (core services + small dataset)
./setup.sh

# Or with options:
./setup.sh --full              # All services
./setup.sh --size large        # More data
./setup.sh --skip-data         # No data generation
```

#### Windows (Command Prompt)
```batch
# Clone repository
git clone <repository-url>
cd data-platform

# Run setup (core services + small dataset)
setup.bat

# Or with options:
setup.bat --full              # All services
setup.bat --size large        # More data
setup.bat --skip-data         # No data generation
```

#### Windows (PowerShell)
```powershell
# Clone repository
git clone <repository-url>
cd data-platform

# Run setup (core services + small dataset)
.\setup.ps1

# Or with options:
.\setup.ps1 -Full              # All services
.\setup.ps1 -Size large        # More data
.\setup.ps1 -SkipData          # No data generation
```

### Manual Setup
```bash
# 1. Start services
docker-compose up -d

# 2. Wait for PostgreSQL
docker-compose exec postgres pg_isready

# 3. Generate data
python scripts/generate_educational_data.py --size small

# 4. Run dbt transformations
docker-compose exec dbt-core bash -c 'cd /opt/dbt_project && dbt run'
```

## 🔧 Common Tasks

### Data Generation
```bash
# Generate different dataset sizes
python scripts/generate_educational_data.py --size xs      # 100 accounts
python scripts/generate_educational_data.py --size small   # 1,000 accounts
python scripts/generate_educational_data.py --size medium  # 10,000 accounts
python scripts/generate_educational_data.py --size large   # 40,000 accounts
```

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it saas_platform_postgres psql -U saas_user -d saas_platform_dev

# Common queries
SELECT COUNT(*) FROM raw.app_database_accounts;
SELECT table_name, COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'raw' GROUP BY table_name;
```

### dbt Operations
```bash
# Run all models
docker-compose exec dbt-core dbt run

# Run specific models
docker-compose exec dbt-core dbt run --select staging.app_database+

# Run tests
docker-compose exec dbt-core dbt test

# Generate documentation
docker-compose exec dbt-core dbt docs generate
docker-compose exec dbt-core dbt docs serve --port 8081
```

### Service Management
```bash
# View logs
docker-compose logs -f postgres
docker-compose logs -f dbt-core

# Restart service
docker-compose restart superset

# Clean restart
docker-compose down -v  # Removes all data!
./setup.sh
```

## 📊 Data Model

### Raw Schema Tables
The `raw` schema contains source data from various systems:

#### App Database (Core Business)
- `app_database_accounts`: Customer accounts with industry, size, revenue
- `app_database_locations`: Bar/restaurant locations with address, capacity
- `app_database_devices`: IoT tap sensors with status and metrics
- `app_database_users`: User accounts with roles and permissions
- `app_database_subscriptions`: Active subscriptions with billing details
- `app_database_tap_events`: High-volume sensor data (not generated by default)
- `app_database_user_sessions`: Application usage tracking
- `app_database_page_views`: Web analytics data
- `app_database_feature_usage`: Premium feature adoption

#### External Integrations
- **Stripe**: Billing data (customers, subscriptions, invoices, charges)
- **HubSpot**: CRM data (companies, contacts, deals, tickets)
- **Marketing**: Campaign data from various platforms

### Transformed Layers (dbt)
1. **Staging**: Type casting, renaming, basic cleaning
2. **Intermediate**: Joins, business logic, calculations
3. **Entity**: Clean dimensional models (accounts, users, devices)
4. **Metrics**: KPIs and aggregated metrics

## 🐛 Troubleshooting

### Common Issues

#### 1. Schema Mismatch Errors
**Symptom**: `column "industry" does not exist`
**Solution**: Clean volumes and restart
```bash
docker-compose down -v
./setup.sh
```

#### 2. PostgreSQL Won't Start
**Symptom**: Container unhealthy
**Check**: Database initialization logs
```bash
docker logs saas_platform_postgres
```
**Common Causes**:
- Invalid SQL syntax in schema files
- Port 5432 already in use
- Insufficient disk space

#### 3. Data Generation Fails
**Symptom**: `Missing tables` error
**Solution**: Ensure schema is created first
```bash
docker exec saas_platform_postgres psql -U saas_user -d saas_platform_dev -f /docker-entrypoint-initdb.d/01_main_schema.sql
```

#### 4. Superset Can't Connect
**Symptom**: Database connection errors
**Solution**: Check database is created
```bash
docker exec saas_platform_postgres psql -U postgres -c "CREATE DATABASE superset_db;"
```

### Health Checks
```bash
# Check all services
docker-compose ps

# Verify endpoints
curl http://localhost:8088/health  # Superset
curl http://localhost:8888         # Jupyter
redis-cli -h localhost ping        # Redis

# Database row counts
docker exec -e PGPASSWORD=saas_secure_password_2024 saas_platform_postgres \
  psql -U saas_user -d saas_platform_dev -c \
  "SELECT COUNT(*) FROM raw.app_database_accounts;"
```

## 🔐 Credentials

### Database
- Host: localhost (from host) / postgres (from containers)
- Port: 5432
- Database: saas_platform_dev
- Username: saas_user
- Password: saas_secure_password_2024

### Superset
- URL: http://localhost:8088
- Username: admin
- Password: admin

### Jupyter
- URL: http://localhost:8888
- Token: Check logs with `docker logs saas_platform_jupyter`

## 📈 Extending the Platform

### Adding New Data Sources
1. Create table in `database/01_main_schema.sql`
2. Add generation logic to `scripts/generate_educational_data.py`
3. Create staging model in `dbt_project/models/staging/`
4. Add source definition to `dbt_project/models/staging/schema.yml`

### Creating New dbt Models
```sql
-- dbt_project/models/intermediate/int_new_metric.sql
WITH base AS (
    SELECT * FROM {{ ref('stg_source_table') }}
)
SELECT 
    column1,
    column2,
    SUM(metric) as total_metric
FROM base
GROUP BY 1, 2
```

### Adding Superset Dashboards
1. Access Superset at http://localhost:8088
2. Add database connection (use container name: postgres)
3. Create datasets from dbt models
4. Build charts and dashboards

## 🚨 Important Notes

### Schema Files
- `01_main_schema.sql`: Contains all table definitions with enhanced columns
- PostgreSQL doesn't support `CREATE DATABASE IF NOT EXISTS` 
- The `99_optional_warp_memory.sql` is disabled by default (renamed to .disabled)

### Data Generation
- The generator expects specific columns that must exist in the schema
- Always check schema alignment if adding new fields
- Use `--months` parameter to control historical data depth

### Container Networking
- Services communicate using container names (e.g., `postgres`, not `localhost`)
- Ports exposed to host: 5432, 6379, 8088, 8888
- Use `saas_network` for inter-container communication

### Performance Considerations
- Large dataset generation can take hours and requires significant disk space
- The `app_database_tap_events` table is not populated by default (would be billions of rows)
- Use appropriate indexes for large tables

## 🎓 Educational Resources

### Learning Paths
1. **Basic Analytics**: Start with exercises/01_basic_queries
2. **dbt Fundamentals**: Work through exercises/02_dbt_models  
3. **Dashboard Creation**: Build in exercises/03_dashboards
4. **Advanced Projects**: Tackle quarterly projects

### Workday Simulations
- Junior Analyst: Basic reporting and data investigation
- Senior Analyst: Complex analysis and stakeholder management
- Analytics Engineer: Pipeline development and optimization

### Key Skills Developed
- SQL and data modeling
- dbt development and testing
- Business intelligence with Superset
- Python data analysis with Jupyter
- Docker and infrastructure basics

## 📝 Maintenance

### Regular Tasks
- Monitor disk usage (PostgreSQL data can grow)
- Update dbt packages: `dbt deps`
- Backup important work: `docker exec postgres pg_dump`
- Clean old logs: `docker-compose logs --tail=100`

### Upgrading Services
1. Update image versions in docker-compose.yml
2. Test in development environment
3. Run `docker-compose pull`
4. Restart with `docker-compose up -d`

## 🤝 Contributing

When modifying the platform:
1. Test all changes with clean deployment
2. Update documentation if adding features
3. Ensure educational materials stay aligned
4. Consider backwards compatibility

Remember: This is an educational platform designed to simulate real-world scenarios while remaining accessible to learners.