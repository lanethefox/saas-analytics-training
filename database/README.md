# Database Schema and Sample Data Generation

This directory contains PostgreSQL schema definitions and sample data generation scripts for the SaaS data platform.

## Database Structure

### Core Tables
- `accounts`: Customer account records
- `locations`: Individual bar/restaurant locations
- `users`: User profiles with role-based access
- `subscriptions`: Subscription lifecycle management
- `devices`: IoT device registrations
- `tap_events`: Real-time sensor data (high-volume)
- `user_sessions`: Application usage tracking
- `page_views`: Web and mobile navigation events
- `feature_usage`: Premium feature interaction tracking

### External Integration Tables
- Stripe billing tables (customers, subscriptions, invoices, charges)
- HubSpot CRM tables (companies, contacts, deals)
- Marketing platform tables (Google Ads, Meta Ads, LinkedIn Ads, Iterable)

## Setup Instructions

1. **Start PostgreSQL container:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Schema initialization is automatic:**
   - Docker automatically runs all SQL files in alphabetical order
   - `01_main_schema.sql` creates the database and tables
   - `02_superset_init.sql` sets up Superset
   
3. **Generate sample data:**
   ```bash
   python3 scripts/generate_all_data.py --scale medium
   ```

4. **Verify setup:**
   ```bash
   docker-compose exec postgres psql -U saas_user -d saas_platform_dev -c "SELECT COUNT(*) FROM raw.app_database_accounts;"
   ```

## Data Volume

The sample data generation creates:
- 20,000 customer accounts
- 30,000+ locations
- 50,000+ devices
- 100,000+ users
- 10M+ tap events (IoT data)
- Complete Stripe billing data
- HubSpot sales pipeline data
- Marketing campaign performance data

This provides realistic data volumes for testing analytics performance and educational scenarios.
