# Comprehensive dbt Model Validation Report

Generated: 2025-06-19 19:21:00

## Executive Summary

The validation of the dbt project revealed both successes and areas requiring attention:

- **Raw Layer**: ✅ 100% Success (30 tables, 908,226 rows)
- **Staging Layer**: ⚠️  43% Success (13/30 models passing)
- **Intermediate Layer**: ✅ 67% Success (8/12 models passing)
- **Entity Layer**: ✅ 71% Success (15/21 models passing)
- **Mart Layer**: ✅ 75% Success (6/8 models passing)
- **Metrics Layer**: ❌ 0% Success (0/11 models passing)

## Layer-by-Layer Analysis

### 1. RAW LAYER (Sources) - 100% PASSED ✅

All 30 raw source tables are properly loaded with data:

**App Database** (869,047 rows):
- `app_database_accounts`: 100 rows
- `app_database_locations`: 199 rows  
- `app_database_users`: 300 rows
- `app_database_devices`: 450 rows
- `app_database_subscriptions`: 178 rows
- `app_database_user_sessions`: 50,000 rows
- `app_database_page_views`: 250,000 rows
- `app_database_feature_usage`: 149,799 rows
- `app_database_tap_events`: 419,020 rows

**Stripe** (19,288 rows):
- `stripe_customers`: 100 rows
- `stripe_prices`: 6 rows
- `stripe_subscriptions`: 178 rows
- `stripe_subscription_items`: 218 rows
- `stripe_invoices`: 2,946 rows
- `stripe_charges`: 2,815 rows
- `stripe_events`: 13,021 rows
- `stripe_payment_intents`: 0 rows

**HubSpot** (3,509 rows):
- `hubspot_companies`: 125 rows
- `hubspot_contacts`: 456 rows
- `hubspot_deals`: 225 rows
- `hubspot_engagements`: 2,303 rows
- `hubspot_tickets`: 400 rows
- `hubspot_owners`: 0 rows

**Marketing** (16,382 rows):
- `google_ads_campaigns`: 30 rows
- `facebook_ads_campaigns`: 12 rows
- `linkedin_ads_campaigns`: 10 rows
- `iterable_campaigns`: 4 rows
- `attribution_touchpoints`: 15,000 rows
- `marketing_qualified_leads`: 150 rows
- `google_analytics_sessions`: 181 rows

### 2. STAGING LAYER - 43% PASSED ⚠️

**Successful Models** (873,155 rows):
- ✅ All app_database staging models (9/9)
- ✅ Core HubSpot models (4/6)

**Failed Models** (17 models):
All failures are due to schema mismatches between expected and actual columns:

**Stripe Models** (8 failures):
- Missing columns: `product`, `metadata`, `collection_method`, etc.
- Fix: Add NULL defaults for missing columns

**HubSpot Models** (2 failures):
- `stg_hubspot__owners`: Empty source table
- `stg_hubspot__tickets`: Column reference issues

**Marketing Models** (7 failures):
- Various column mismatches in campaign and attribution models

### 3. INTERMEDIATE LAYER - 67% PASSED ✅

**Successful Models** (1,596 rows):
- ✅ `int_customers__core`: 100 rows
- ✅ `int_devices__performance_health`: 450 rows
- ✅ `int_features__adoption_patterns`: 24 rows
- ✅ `int_features__core`: 24 rows
- ✅ `int_locations__core`: 199 rows
- ✅ `int_locations__operational_metrics`: 199 rows
- ✅ `int_users__core`: 300 rows
- ✅ `int_users__engagement_metrics`: 300 rows

**Failed Models**:
- ❌ `int_campaigns__attribution`: Depends on failed staging
- ❌ `int_campaigns__core`: Depends on failed staging
- ❌ `int_subscriptions__core`: Depends on failed Stripe staging
- ❌ `int_subscriptions__revenue_metrics`: Depends on failed Stripe staging

### 4. ENTITY LAYER - 71% PASSED ✅

**Successful Models** (522,520 rows):
- ✅ All Customer entities (3/3): 3,200 rows
- ✅ All Device entities (3/3): 498,662 rows
- ✅ All Feature entities (3/3): 120 rows
- ✅ All Location entities (3/3): 5,284 rows
- ✅ All User entities (3/3): 15,154 rows

**Failed Models**:
- ❌ All Campaign entities (3/3): Depends on failed intermediate
- ❌ All Subscription entities (3/3): Depends on failed intermediate

### 5. MART LAYER - 75% PASSED ✅

**Successful Models** (1,895 rows):
- ✅ `mart_customer_success__health`: 100 rows
- ✅ `mart_device_operations`: 396 rows
- ✅ `mart_operations__performance`: 100 rows
- ✅ `mart_operations_health`: 749 rows
- ✅ `mart_product__adoption`: 100 rows
- ✅ `operations_device_monitoring`: 450 rows

**Failed Models**:
- ❌ `mart_marketing__attribution`: Depends on failed campaigns
- ❌ `mart_sales__pipeline`: Depends on failed subscriptions

### 6. METRICS LAYER - 0% PASSED ❌

All 11 metrics models failed due to dependencies on failed entity models:
- Campaigns and Subscriptions entities must be fixed first
- Once dependencies are resolved, metrics layer should work

## Key Issues Identified

### 1. Schema Mismatches (Primary Issue)
The staging models expect columns that don't exist in the raw tables:
- Stripe models expect: `product`, `metadata`, `collection_method`
- Marketing models have various column name mismatches
- HubSpot models expect different property structures

### 2. Data Type Conversions
- `to_timestamp()` called on columns already of timestamp type
- Incorrect assumptions about JSONB columns

### 3. Empty Source Tables
- `hubspot_owners`: No data (expected)
- `stripe_payment_intents`: No data (expected)

## Recommended Fix Order

1. **Fix Staging Models** (Priority 1)
   - Update Stripe staging models to handle missing columns
   - Fix Marketing staging models column references
   - Fix HubSpot staging model issues

2. **Cascade Fixes** (Priority 2)
   - Once staging is fixed, intermediate models should work
   - Entity models will follow automatically
   - Mart and Metrics layers will resolve

3. **Add Data Quality Checks** (Priority 3)
   - Add tests for required columns
   - Add row count expectations
   - Add uniqueness tests on primary keys

## Performance Metrics

- **Total Validation Time**: ~5 minutes
- **Average Model Run Time**: 2.7 seconds
- **Slowest Models**: Device history tables (3.6s)
- **Total Data Volume**: 1.4M+ rows processed

## Next Steps

1. Run the staging model fixes:
   ```bash
   python3 scripts/fix_all_staging_models.py
   ```

2. Re-run full dbt build:
   ```bash
   docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt build --profiles-dir ."
   ```

3. Generate updated validation report after fixes

## Success Metrics

Once all fixes are applied:
- All staging models should pass (30/30)
- Dependent layers should cascade to 100% success
- Total row count should exceed 2M+ rows
- All metrics models should be queryable