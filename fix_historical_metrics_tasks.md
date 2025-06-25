# Fix Historical Metrics - Task List

## Problem Summary
Metrics tables only show 1 row (current snapshot) instead of years of historical data, despite raw data containing years of history (2018-2025).

## Root Causes
1. Metrics models use hardcoded `CURRENT_DATE` instead of historical dates
2. Entity models only show current state, not historical snapshots
3. Daily/monthly entity models create fake date spines with repeated current data
4. Historical raw data is not being properly utilized

## Task List

### Phase 1: Create Historical Fact Tables
1. **Create historical customer facts table**
   - Build `fct_customer_history` that tracks customer state changes over time
   - Include created_at, status changes, MRR changes
   - Use SCD Type 2 approach or daily snapshots

2. **Create historical subscription facts table**
   - Build `fct_subscription_history` with subscription lifecycle events
   - Track starts, cancellations, upgrades, downgrades
   - Include MRR at each point in time

3. **Create historical device facts table**
   - Build `fct_device_history` tracking device status over time
   - Include online/offline transitions, health scores

4. **Create historical user activity facts**
   - Build `fct_user_activity_history` with login patterns
   - Track DAU/MAU at historical points

### Phase 2: Rebuild Entity Models
1. **Refactor entity_customers_daily**
   - Use historical facts instead of repeating current state
   - Implement proper SCD logic or snapshot approach

2. **Refactor entity_subscriptions_monthly**
   - Ensure it properly aggregates historical subscription data
   - Validate against raw data date ranges

3. **Create entity_devices_daily with history**
   - Build from device telemetry and status changes
   - Include historical health metrics

### Phase 3: Rebuild Metrics Models
1. **Create metrics_revenue_daily**
   - Daily MRR/ARR trends
   - Customer counts by day
   - Churn metrics

2. **Create metrics_operations_daily**
   - Device availability trends
   - Location activity patterns
   - User engagement over time

3. **Create metrics_customer_success_daily**
   - Health score trends
   - Risk score evolution
   - Cohort analysis

4. **Update summary metrics to accept date parameter**
   - Allow filtering by date range
   - Default to current date if not specified
   - Support "as of" date queries

### Phase 4: Update Existing Metrics
1. **Refactor metrics_api**
   - Accept date parameter
   - Return historical data when requested
   - Keep current behavior as default

2. **Refactor all snapshot metrics**
   - Remove hardcoded CURRENT_DATE
   - Pull from historical fact tables
   - Support time-based filtering

### Phase 5: Testing & Validation
1. **Validate historical data completeness**
   - Ensure all date ranges are covered
   - Check for gaps in time series
   - Verify calculations at historical points

2. **Performance optimization**
   - Add proper indexes for time-based queries
   - Consider partitioning for large historical tables
   - Implement incremental refresh strategies

## Implementation Order
1. Start with Phase 1 - Create historical facts (foundation)
2. Phase 3 - Build new historical metrics (prove the concept)
3. Phase 2 - Refactor entity models (improve existing)
4. Phase 4 - Update existing metrics (backward compatibility)
5. Phase 5 - Testing and optimization

## Success Criteria
- All metrics tables should have multiple rows showing historical trends
- Date ranges should match raw data (2018-2025)
- Current state queries should still work (backward compatibility)
- Historical queries should be performant