# Data Normalization Plan for ML Training Data
## Transforming SaaS Platform Data into Production-Ready Training Sets

**Version**: 1.0  
**Date**: June 18, 2025  
**Objective**: Transform the current problematic data into normalized, high-quality training data suitable for machine learning models

---

## Executive Summary

This plan outlines a systematic approach to normalize the SaaS platform data, addressing critical issues including account ID mismatches, synthetic values, and missing relationships. The normalized data will support three primary ML use cases:

1. **Churn Prediction** - Predict customer churn 30/60/90 days in advance
2. **Customer Lifetime Value (CLV)** - Estimate long-term customer revenue
3. **Device Health Scoring** - Predict device failures and maintenance needs

## Current State Assessment

### Critical Issues Identified:
- **Account ID Mismatch**: Customer IDs (0-99) don't match Subscription IDs (10000000+)
- **Zero MRR Values**: 100% of customers show $0 revenue despite active subscriptions
- **Synthetic Device Metrics**: Only 2 distinct health scores (0.20, 0.52)
- **Data Type Inconsistencies**: Mixed VARCHAR/INTEGER for account_id
- **Limited History**: Most entities have only 1-2 days of data
- **Missing Relationships**: Orphaned subscriptions, unlinked entities

### Data Volume:
- 100 Customers (all Tier 4, $0 MRR)
- 1,205 Devices (0.25 avg health score)
- 337 Users (0.33 avg engagement)
- 441 Subscriptions (241 with positive MRR)
- 241 Locations
- 310 Campaigns

## Normalization Strategy

### Phase 1: ID Reconciliation and Mapping (Week 1)

**Objective**: Create consistent ID relationships across all entities

**Approach**:
1. Create master mapping table for account IDs
2. Standardize all IDs to VARCHAR format
3. Implement deterministic ID generation rules
4. Build foreign key relationships

**Deliverables**:
- `01_id_mapping_tables.sql` - Create mapping infrastructure
- `02_id_reconciliation.sql` - Fix existing relationships
- `03_id_validation.sql` - Verify all joins work

### Phase 2: Synthetic Data Replacement (Week 1-2)

**Objective**: Replace unrealistic values with statistically valid distributions

**Approach**:
1. Generate realistic health scores (normal distribution, mean=75, std=15)
2. Create believable uptime percentages (beta distribution, α=9, β=1)
3. Distribute MRR across customer tiers (power law distribution)
4. Generate engagement scores based on user roles

**Deliverables**:
- `04_device_metrics_generation.sql` - Realistic device health
- `05_revenue_distribution.sql` - Proper MRR allocation
- `06_user_engagement_scores.sql` - Role-based engagement

### Phase 3: Historical Data Generation (Week 2)

**Objective**: Create 24 months of historical data for trend analysis

**Approach**:
1. Generate historical snapshots with realistic growth patterns
2. Simulate customer lifecycle events (upgrades, downgrades, churn)
3. Create device degradation patterns over time
4. Build user engagement trajectories

**Deliverables**:
- `07_historical_snapshot_generator.sql` - Time series data
- `08_lifecycle_event_simulator.sql` - Business events
- `09_temporal_patterns.sql` - Seasonal variations

### Phase 4: Feature Engineering (Week 3)

**Objective**: Create ML-ready features from normalized data

**Features to Engineer**:
1. **Customer Features**:
   - Revenue growth rate (3, 6, 12 month)
   - Product adoption velocity
   - Support ticket frequency
   - Payment reliability score

2. **Device Features**:
   - Health score trending
   - Maintenance interval patterns
   - Usage intensity metrics
   - Environmental factor impacts

3. **User Features**:
   - Engagement momentum
   - Feature adoption sequence
   - Session pattern clustering
   - Role-based activity index

**Deliverables**:
- `10_customer_feature_engineering.sql`
- `11_device_feature_engineering.sql`
- `12_user_feature_engineering.sql`

### Phase 5: Training Set Creation (Week 3-4)

**Objective**: Build labeled datasets for each ML use case

**Training Sets**:

1. **Churn Prediction Dataset**:
   - Features: 150+ customer/user/device metrics
   - Labels: Churned within 30/60/90 days
   - Split: 70% train, 15% validation, 15% test
   - Class balance: 20% churn, 80% retained

2. **CLV Prediction Dataset**:
   - Features: Customer demographics, usage, engagement
   - Labels: 12-month revenue (regression target)
   - Split: 70/15/15
   - Stratified by customer tier

3. **Device Health Dataset**:
   - Features: Performance metrics, environmental data
   - Labels: Failure within 7/14/30 days
   - Split: 70/15/15
   - Balanced by device type

**Deliverables**:
- `13_churn_training_set.sql`
- `14_clv_training_set.sql`
- `15_device_health_training_set.sql`

### Phase 6: Data Quality & Validation (Week 4)

**Objective**: Ensure training data meets ML quality standards

**Validation Checks**:
1. No missing values in critical features
2. Proper data type consistency
3. Statistical distribution validation
4. Temporal consistency checks
5. Label quality verification

**Deliverables**:
- `16_data_quality_framework.sql`
- `17_statistical_validation.sql`
- `18_ml_readiness_report.sql`

## Implementation Timeline

```
Week 1: ID Reconciliation & Initial Synthetic Data Replacement
Week 2: Complete Synthetic Replacement & Historical Generation
Week 3: Feature Engineering & Initial Training Sets
Week 4: Training Set Refinement & Quality Validation
```

## Success Metrics

1. **Data Completeness**: 100% of relationships properly linked
2. **Value Realism**: All metrics within expected business ranges
3. **Historical Coverage**: 24 months of consistent history
4. **Feature Coverage**: 150+ engineered features per entity
5. **Training Set Quality**: <1% missing values, proper class balance

## Risk Mitigation

1. **Data Loss**: Create backups before each transformation
2. **Business Logic**: Validate with domain experts
3. **Statistical Validity**: Use industry benchmarks
4. **Performance**: Implement incremental processing

## Next Steps

1. Review and approve normalization plan
2. Set up development environment with data copies
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews

## Appendix: Technical Specifications

### Expected Data Distributions

**Customer MRR by Tier**:
- Tier 1: $5,000-50,000 (Log-normal, μ=9.5, σ=0.8)
- Tier 2: $1,000-5,000 (Log-normal, μ=7.8, σ=0.6)
- Tier 3: $200-1,000 (Log-normal, μ=6.2, σ=0.5)
- Tier 4: $50-200 (Log-normal, μ=4.5, σ=0.4)

**Device Health Scores**:
- Operational: 60-95 (Beta, α=4, β=1.5)
- Maintenance: 40-60 (Normal, μ=50, σ=5)
- Critical: 10-40 (Exponential, λ=0.1)

**User Engagement**:
- Admin: 70-95 (Beta, α=4, β=1.2)
- Manager: 50-80 (Normal, μ=65, σ=10)
- Standard: 20-70 (Gamma, α=2, β=15)

**Churn Rates by Tier**:
- Tier 1: 5-10% annually
- Tier 2: 10-15% annually
- Tier 3: 15-25% annually
- Tier 4: 25-40% annually
