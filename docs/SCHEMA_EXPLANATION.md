# Database Schema Explanation

## Overview

This project uses a **raw → staging → transformed** data architecture:

1. **Raw Schema (`raw.*`)**: Contains source data from various systems
2. **Public Schema**: Contains cleaned/transformed data (created by dbt)

## Schema Structure

### Raw Schema Tables (Source Data)

The `raw` schema contains tables prefixed by their source system:

- **Application Database** (`app_database_*`):
  - `raw.app_database_accounts` - Customer accounts
  - `raw.app_database_locations` - Physical locations
  - `raw.app_database_users` - User accounts
  - `raw.app_database_devices` - IoT devices
  - `raw.app_database_subscriptions` - Subscription data

- **External Systems**:
  - `raw.stripe_*` - Stripe billing data
  - `raw.hubspot_*` - HubSpot CRM data
  - `raw.google_ads_*` - Google Ads data
  - etc.

### Important Notes

1. **Data Generation**: The data generation scripts populate the `raw.app_database_*` tables
2. **dbt Sources**: dbt reads from the `raw` schema tables
3. **Schema Creation**: The `01_main_schema.sql` file creates all necessary databases and tables
4. **Execution Order**: Database files run in alphabetical order on container initialization

## Database Initialization Files

- `00_README.md` - Explains the database file structure and execution order
- `01_main_schema.sql` - Creates main database, raw schema, and all application tables (PRIMARY)
- `02_superset_init.sql` - Initializes Superset database and users
- `99_optional_warp_memory.sql` - Optional vector database for memory/embedding features

## Data Flow

```
External Systems → Raw Schema → dbt Models → Analytics Tables → Dashboards
                    (raw.*)      (staging/intermediate/entity/mart)
```

## For New Deployments

1. Docker automatically runs SQL files in alphabetical order from `/docker-entrypoint-initdb.d`
2. The `01_main_schema.sql` creates databases and all necessary tables
3. The `02_superset_init.sql` sets up Superset database and permissions
4. Data generators populate `raw.app_database_*` tables
5. dbt transforms raw data into analytics-ready models