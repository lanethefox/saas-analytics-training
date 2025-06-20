# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Data Generation and Testing
```bash
# Install test dependencies
make install-test-deps

# Quick tests (recommended for development)
make test-smoke       # Run smoke tests (5-10 min)
make test-xs         # Test XS generation end-to-end (5-10 min)

# Comprehensive tests
make test-generation  # Test all data generators (10-15 min)
make test-database   # Test database integration (5-10 min)
make test-full       # Run complete test suite (30-45 min)

# Development workflow shortcuts
make dev-test        # Quick development tests
make pre-commit      # Pre-commit checks
make clean           # Clean up test artifacts

# Run specific test
python3 scripts/run_tests.py <test-name>
```

### dbt Commands
```bash
# Run dbt transformations in Docker
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt test --profiles-dir ."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt build --profiles-dir ."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt compile --profiles-dir ."

# Run specific models
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --select entity.entity_customers --profiles-dir ."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --select +entity.entity_customers+ --profiles-dir ."

# Use convenience script
./run_dbt.sh
```

### Database Access
```bash
# Connect to PostgreSQL
psql -h localhost -U saas_user -d saas_platform_dev
# Password: saas_secure_password_2024

# Docker connection
docker-compose exec postgres psql -U saas_user -d saas_platform_dev

# Run SQL file
docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev < your_script.sql
```

### Platform Management
```bash
# Initial setup (creates all services and loads data)
./setup.sh

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]  # e.g., postgres, dbt, superset

# Stop services
docker-compose down

# Full reset (removes all data)
docker-compose down -v && ./setup.sh
```

### Data Generation Scripts
```bash
# Generate synthetic data
python3 scripts/generate_users.py
python3 scripts/generate_accounts.py
python3 scripts/generate_locations.py
python3 scripts/generate_devices.py
python3 scripts/generate_subscriptions.py
```

## Architecture

This is a **B2B SaaS Analytics Platform** for a bar management system implementing Entity-Centric Modeling (ECM). It serves 20,000+ accounts across 30,000+ locations with IoT-enabled tap devices.

### Entity-Centric Model Structure
The platform implements 7 core entities, each following a 3-table pattern:

1. **Atomic Tables** (`entity_customers`) - Current state with pre-calculated metrics
2. **History Tables** (`entity_customers_history`) - Complete audit trail of changes
3. **Grain Tables** (`entity_customers_daily`) - Time-series aggregations

### dbt Model Layers
```
dbt_project/models/
├── sources/      # Raw data source definitions (~20 sources)
├── staging/      # Clean, typed, deduplicated data
├── intermediate/ # Business logic, derived metrics
├── entity/       # Core ECM entities (7 × 3 = 21 tables)
└── mart/         # Domain-specific views for analytics teams
```

### Core Entities and Key Metrics

| Entity | Purpose | Key Metrics |
|--------|---------|-------------|
| **Customers** | Account-level analytics | MRR, health_score, churn_risk_score, lifetime_value |
| **Devices** | IoT tap monitoring | uptime_percentage, maintenance_score, event_volume |
| **Locations** | Venue operations | revenue_impact, device_health, operational_efficiency |
| **Users** | User engagement | activity_score, feature_adoption_rate, last_active |
| **Subscriptions** | Revenue tracking | mrr_change, expansion_revenue, contraction_amount |
| **Campaigns** | Marketing ROI | customer_acquisition_cost, conversion_rate, roi |
| **Features** | Product analytics | adoption_rate, usage_intensity, retention_impact |

### Data Flow
1. **Raw Data** → PostgreSQL schemas (accounts, devices, events, etc.)
2. **Staging** → Standardized and typed data
3. **Intermediate** → Business logic applied
4. **Entity** → Pre-aggregated metrics in wide tables
5. **Mart** → Department-specific views

### Key Design Principles
- **Single-Table Analytics**: 90% of queries require no joins
- **Pre-Calculated Metrics**: Health scores, risk indicators ready to use
- **Temporal Support**: History tables track all changes over time
- **Performance**: Optimized for sub-3 second dashboard queries
- **Self-Service**: Business users can write SQL without complex joins

### Service Ports
- PostgreSQL: 5432
- Apache Superset: 8088 (admin/admin_password_2024)
- Apache Airflow: 8080 (admin/admin_password_2024)
- Jupyter Lab: 8888 (token: saas_ml_token_2024)
- MLflow: 5001
- ML API: 8000
- Grafana: 3000 (admin/grafana_admin_2024)

### Common Query Patterns
```sql
-- Current state analysis (atomic tables)
SELECT * FROM entity.entity_customers 
WHERE churn_risk_score > 60 AND customer_tier = 3;

-- Time-series analysis (grain tables)
SELECT * FROM entity.entity_customers_daily 
WHERE date >= CURRENT_DATE - 30;

-- Change tracking (history tables)
SELECT * FROM entity.entity_customers_history 
WHERE customer_id = 'xyz' ORDER BY valid_from;
```