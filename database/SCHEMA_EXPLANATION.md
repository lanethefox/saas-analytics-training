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
3. **Schema Creation**: The `00_complete_raw_schema.sql` file creates all necessary raw tables
4. **Legacy File**: The `01_schema.sql` file is legacy and not used in the current setup

## File Purposes

- `00_complete_raw_schema.sql` - Creates the raw schema and all source tables (ACTIVE)
- `00_complete_raw_schema_fixed.sql` - Fixed version with proper constraints (ACTIVE)
- `01_schema.sql` - Legacy schema file, kept for reference only (NOT USED)
- `00_init_superset.sql` - Initializes Superset metadata database
- `02-init-warp-memory.sql` - Initializes memory database for caching

## Data Flow

```
External Systems → Raw Schema → dbt Models → Analytics Tables → Dashboards
                    (raw.*)      (staging/intermediate/entity/mart)
```

## For New Deployments

1. Docker automatically runs SQL files in alphabetical order from `/docker-entrypoint-initdb.d`
2. The `00_complete_raw_schema.sql` creates all necessary tables
3. Data generators populate `raw.app_database_*` tables
4. dbt transforms raw data into analytics-ready models