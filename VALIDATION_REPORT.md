# dbt Model Validation Report

Generated: 2025-06-19 19:10:00

## Summary

Based on the initial validation run, here's what we found:

### ✅ RAW LAYER (Sources) - 100% PASSED
- **Total Tables**: 30
- **Total Rows**: 908,226
- **Status**: All raw source tables exist and contain data

Key tables:
- `app_database_*`: 9 tables, 869,047 rows
- `stripe_*`: 8 tables, 19,288 rows  
- `hubspot_*`: 6 tables, 3,509 rows
- `marketing_*`: 7 tables, 16,382 rows

### ✅ STAGING LAYER - IN PROGRESS
Running staging models shows they are being created successfully. The staging layer includes:
- 30 models total
- Mix of views and incremental models
- All app_database staging models created successfully

### 🔄 INTERMEDIATE LAYER - PENDING
- 12 models to validate
- Depends on staging layer completion

### 🔄 ENTITY LAYER - PENDING
- 21 models (7 entities × 3 types each)
- Depends on intermediate layer

### 🔄 MART LAYER - PENDING
- 8 models
- Depends on entity layer

### 🔄 METRICS LAYER - PENDING
- 11 models
- Depends on entity layer

## Next Steps

1. Complete staging layer validation
2. Fix any column mismatches in intermediate/entity layers
3. Run full validation of all layers
4. Generate comprehensive report with execution times and row counts

## Known Issues to Fix

1. **Stripe Models**: May have missing columns (e.g., `collection_method`)
2. **Entity Models**: References to history tables that don't exist
3. **Metrics Models**: Dependencies on entity columns that may not match

## Recommendation

Run a full dbt build to identify and fix all issues:
```bash
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt build --profiles-dir ."
```

Then re-run validation to get accurate metrics.