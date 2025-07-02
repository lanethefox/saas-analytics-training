# Remaining Data Platform Tasks

## Critical Issues to Fix

### 1. Customer Tier Distribution (Priority: HIGH)
**Issue**: All customers are tier 4 despite configuration having 4 tiers
**Root Cause**: In `stg_app_database__accounts.sql`, the tier calculation is based on business_type, not account size
```sql
-- Current (incorrect):
case 
    when business_type = 'enterprise' then 1
    when business_type = 'professional' then 2
    when business_type = 'business' then 3
    else 4
end as account_type_tier
```

**Tasks**:
- [ ] Modify `generate_accounts.py` to store account_size in a field
- [ ] Update staging model to use proper size-based tier calculation
- [ ] Ensure tier distribution follows config (70% starter, 20% professional, 8% business, 2% enterprise)

### 2. Tap Events Generation (Priority: HIGH)
**Issue**: No tap events generated, causing all device health scores to be 0.20
**Root Cause**: Generator likely failing silently or has dependency issues

**Tasks**:
- [ ] Debug `generate_tap_events.py` to find why it's not generating data
- [ ] Fix any import or dependency issues
- [ ] Ensure it reads from generated device/location JSON files
- [ ] Verify event distribution follows venue type patterns (restaurant: 50-200/day, bar: 100-400/day, etc.)

### 3. Campaign Data Generation (Priority: MEDIUM)
**Issue**: Campaign tables remain empty
**Root Cause**: Schema mismatch between generator expectations and actual table structure

**Tasks**:
- [ ] Map generator output to actual campaign table schemas:
  - `google_ads_campaigns`: id, name, status (not campaign_id)
  - `facebook_ads_campaigns`: Different schema
  - `linkedin_ads_campaigns`: Different schema
- [ ] Update generators to match actual schemas or create proper mapping
- [ ] Generate realistic campaign performance metrics

### 4. Device Health Score Calculation (Priority: HIGH)
**Issue**: All devices show 0.20 health score (no events = default score)
**Root Cause**: Health scores depend on tap_events which aren't being generated

**Tasks**:
- [ ] Once tap events are fixed, verify health score calculation works
- [ ] Add variation to device operational status distribution
- [ ] Ensure health scores correlate with:
  - Event frequency
  - Temperature/pressure anomalies
  - Maintenance status

### 5. Missing Generators (Priority: MEDIUM)
**Issue**: Several generators in pipeline don't exist or fail

**Tasks**:
- [ ] Create/fix `generate_device_telemetry.py` for temperature/pressure readings
- [ ] Fix `generate_marketing_qualified_leads.py` 
- [ ] Fix `generate_campaign_performance.py`
- [ ] Ensure all financial generators work (Stripe tables)

### 6. Data Relationships (Priority: LOW)
**Issue**: Missing connections between entities

**Tasks**:
- [ ] Link campaigns → leads → customers
- [ ] Connect subscriptions → invoices → payments
- [ ] Ensure devices → telemetry → events flow

## Implementation Order

1. **Fix Customer Tiers** (1 hour)
   - Most visible issue
   - Affects downstream analytics

2. **Fix Tap Events** (2-3 hours)
   - Critical for device health scores
   - Enables operational analytics

3. **Fix Campaign Generation** (2 hours)
   - Enables marketing analytics
   - Completes attribution story

4. **Verify Health Calculations** (30 min)
   - Should work once events exist
   - May need metric adjustments

5. **Complete Missing Generators** (3-4 hours)
   - Fill remaining data gaps
   - Enable full demo scenarios

## Validation Checklist

After fixes, run validation to ensure:
- [ ] Customer tiers: 4 distinct values with proper distribution
- [ ] Device health: Normal distribution, not all 0.20
- [ ] Campaigns: At least 20 campaigns across platforms
- [ ] Tap events: 1M+ events across all devices
- [ ] Trials: 10-15% of new subscriptions
- [ ] Geographic distribution: Customers across 25+ states
- [ ] Industry variety: 5 industries properly distributed
- [ ] Payment data: Invoices for all active subscriptions

## Quick Test Commands

```bash
# Check customer tier distribution
psql $DB_URL -c "SELECT customer_tier, COUNT(*) FROM entity.entity_customers GROUP BY customer_tier ORDER BY customer_tier;"

# Check device health variety  
psql $DB_URL -c "SELECT COUNT(DISTINCT overall_health_score) as unique_scores, MIN(overall_health_score), MAX(overall_health_score) FROM entity.entity_devices;"

# Check event generation
psql $DB_URL -c "SELECT COUNT(*) as events, COUNT(DISTINCT device_id) as devices FROM raw.app_database_tap_events;"

# Check campaigns
psql $DB_URL -c "SELECT COUNT(*) FROM raw.google_ads_campaigns UNION ALL SELECT COUNT(*) FROM raw.facebook_ads_campaigns;"
```