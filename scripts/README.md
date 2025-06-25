# Data Platform Scripts

This directory contains the core scripts for generating and managing synthetic data for the SaaS platform.

## Overview

The scripts in this directory handle:
- Synthetic data generation for all platform entities
- Data loading into the PostgreSQL database
- Database maintenance operations

## Quick Start

### 1. Generate All Data
```bash
# Generate data for a specific scale (xs, small, medium, large)
python generate_all_data.py --scale small

# Generate with resume capability (continues from where it left off)
python generate_all_data.py --scale medium --resume
```

### 2. Load Data into Database
```bash
# Load all generated synthetic data into the database
python load_synthetic_data.py
```

### 3. Database Maintenance
```bash
# Wipe all data from the raw schema
python wipe_data.py

# Reset data (wipe and regenerate)
./reset_data.sh
```

## Core Scripts

### Data Generation Scripts

#### Master Orchestrator
- `generate_all_data.py` - Orchestrates all data generation with support for multiple scales (xs, small, medium, large) and resume capability

#### Application Data Generators
- `generate_accounts.py` - Generates account/organization data
- `generate_locations.py` - Generates physical location data
- `generate_users.py` - Generates user profiles and authentication data
- `generate_devices.py` - Generates IoT device records
- `generate_subscriptions.py` - Generates subscription plans and assignments
- `generate_device_telemetry.py` - Generates device telemetry/sensor data
- `generate_user_sessions.py` - Generates user session tracking data
- `generate_tap_events.py` - Generates user interaction events
- `generate_page_views.py` - Generates page view analytics
- `generate_feature_usage.py` - Generates feature adoption metrics

#### Marketing Data Generators
- `generate_google_analytics_sessions.py` - Generates GA session data
- `generate_attribution_touchpoints.py` - Generates marketing attribution data
- `generate_campaign_performance.py` - Generates campaign performance metrics
- `generate_marketing_campaigns.py` - Generates marketing campaign definitions
- `generate_marketing_qualified_leads.py` - Generates MQL data
- `generate_facebook_ads_campaigns.py` - Generates Facebook Ads data
- `generate_google_ads_campaigns.py` - Generates Google Ads data
- `generate_linkedin_ads_campaigns.py` - Generates LinkedIn Ads data
- `generate_iterable_campaigns.py` - Generates Iterable email campaign data

#### CRM Data Generators (HubSpot)
- `generate_hubspot_companies.py` - Generates company records
- `generate_hubspot_contacts.py` - Generates contact records
- `generate_hubspot_deals.py` - Generates sales deal records
- `generate_hubspot_engagements.py` - Generates engagement activities
- `generate_hubspot_owners.py` - Generates HubSpot user/owner data
- `generate_hubspot_tickets.py` - Generates support ticket data

#### Billing Data Generators (Stripe)
- `generate_stripe_customers.py` - Generates Stripe customer records
- `generate_stripe_subscriptions.py` - Generates subscription records
- `generate_stripe_subscription_items.py` - Generates subscription line items
- `generate_stripe_prices.py` - Generates pricing/product data
- `generate_stripe_invoices.py` - Generates invoice records
- `generate_stripe_charges.py` - Generates payment charge records
- `generate_stripe_payment_intents.py` - Generates payment intent records
- `generate_stripe_events.py` - Generates Stripe webhook events

### Data Loading Scripts
- `load_synthetic_data.py` - Comprehensive loader for all synthetic data into PostgreSQL

### Database Maintenance Scripts
- `wipe_data.py` - Truncates all tables in the raw schema
- `reset_data.sh` - Shell script to wipe and regenerate data

### Utility/Helper Modules
- `database_config.py` - Database connection configuration and helpers
- `environment_config.py` - Environment size definitions (xs, small, medium, large)
- `chunked_generation.py` - Memory-efficient batch generation utilities
- `device_generator.py` - Device data generation classes
- `device_helpers.py` - Helper functions for device generation
- `hubspot_generator.py` - HubSpot data generation classes
- `hubspot_helpers.py` - Helper functions for HubSpot generation
- `marketing_generator.py` - Marketing data generation classes
- `marketing_helpers.py` - Helper functions for marketing generation

## Environment Scales

The data generation supports multiple environment scales:

- **xs** - Extra small dataset for quick testing (~100 accounts)
- **small** - Small dataset for development (~1,000 accounts)
- **medium** - Medium dataset for staging (~10,000 accounts)
- **large** - Large dataset for performance testing (~100,000 accounts)

## Database Configuration

Scripts use the following environment variables for database connection:
- `POSTGRES_HOST` (default: localhost)
- `POSTGRES_PORT` (default: 5432)
- `POSTGRES_DB` (default: saas_platform_dev)
- `POSTGRES_USER` (default: saas_user)
- `POSTGRES_PASSWORD` (default: saas_secure_password_2024)

## Data Dependencies

The data generators have dependencies that must be respected:

1. **Foundation Data** (generate first):
   - Accounts
   - Locations
   - Users
   - Stripe Prices

2. **Dependent Data** (generate after foundation):
   - Devices (depends on accounts, locations)
   - Subscriptions (depends on accounts, Stripe prices)
   - All session/event data (depends on users, devices)
   - HubSpot data (depends on accounts, users)
   - Stripe billing data (depends on accounts, subscriptions)

The `generate_all_data.py` script handles these dependencies automatically.

## Troubleshooting

### Memory Issues
If you encounter memory issues with large datasets:
1. Use the `--scale` parameter to generate smaller datasets
2. The scripts use chunked generation to handle large volumes efficiently
3. Consider running generators individually rather than all at once

### Resume Capability
If generation is interrupted:
```bash
python generate_all_data.py --scale medium --resume
```
This will check which tables already have data and continue from where it left off.

### Database Connection Issues
1. Ensure PostgreSQL is running
2. Verify connection parameters in environment variables
3. Check that the `raw` schema exists in the database
4. Ensure the user has appropriate permissions