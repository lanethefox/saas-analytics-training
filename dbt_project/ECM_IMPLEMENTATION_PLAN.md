# Entity-Centric Modeling (ECM) Implementation Plan

## Project Overview
Building a comprehensive ECM dbt project for a SaaS data platform with sophisticated analytical modeling patterns for educational purposes.

## Architecture Overview

### Five-Layer Architecture

1. **Sources Layer** (✓ Already Defined)
   - app_database: Core application tables
   - stripe: Billing and payment data
   - hubspot: CRM and sales data

2. **Staging Layer** (To Build)
   - Clean and standardize raw data
   - Type casting and naming conventions
   - Basic business logic and filters
   - Data quality checks

3. **Intermediate Layer** (To Build)
   - Cross-source joins
   - Complex business logic
   - Calculated metrics
   - Pre-aggregations for performance

4. **Entity Layer** (To Build - Core Focus)
   - Seven core entities with three-table pattern:
     - Atomic: Current state snapshot
     - History: Change tracking with temporal validity
     - Grain: Time-based aggregations (daily/hourly)

5. **Mart Layer** (To Build)
   - Domain-specific analytics models
   - Executive dashboards
   - Operational reporting
   - Customer success metrics

## Core Entities Design

### 1. Customers Entity
- **Atomic**: Current customer state with health scores, MRR, usage metrics
- **History**: Customer lifecycle changes, subscription transitions
- **Grain**: Daily snapshots for trend analysis

### 2. Locations Entity
- **Atomic**: Bar/restaurant locations with operational metrics
- **History**: Location status changes, expansions/contractions
- **Grain**: Daily operational summaries

### 3. Users Entity
- **Atomic**: User profiles with engagement metrics
- **History**: Role changes, activity patterns
- **Grain**: Daily active user counts and engagement

### 4. Subscriptions Entity
- **Atomic**: Current subscription state with revenue metrics
- **History**: Plan changes, upgrades/downgrades
- **Grain**: Daily MRR movements and cohort tracking

### 5. Campaigns Entity
- **Atomic**: Active campaign performance with attribution
- **History**: Campaign lifecycle and performance changes
- **Grain**: Daily spend and conversion metrics

### 6. Devices Entity
- **Atomic**: IoT device status and health metrics
- **History**: Maintenance events, connectivity issues
- **Grain**: Hourly performance aggregations

### 7. Features Entity
- **Atomic**: Feature adoption and usage patterns
- **History**: Feature rollout and adoption curves
- **Grain**: Daily feature engagement metrics

## Key SaaS Metrics to Implement

### Revenue Metrics
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- Revenue expansion/contraction
- Net Revenue Retention
- Average Revenue Per Account (ARPA)

### Customer Health Metrics
- Customer Health Score (composite)
- Churn Risk Score
- Engagement Score
- Product Adoption Score
- Support Ticket Velocity

### Operational Metrics
- Device uptime and reliability
- Location activity levels
- Feature usage intensity
- API call patterns

### Marketing Attribution
- Multi-touch attribution
- Channel performance
- CAC (Customer Acquisition Cost)
- LTV:CAC ratio
- Marketing ROI

## Advanced SQL Patterns to Demonstrate

1. **Slowly Changing Dimensions (SCD Type 2)**
   - Temporal validity windows
   - Change detection and tracking
   - Point-in-time queries

2. **Window Functions**
   - Running totals and averages
   - Lag/lead for period comparisons
   - Dense rank for cohort analysis

3. **Recursive CTEs**
   - Organizational hierarchies
   - Attribution pathways
   - Feature dependency graphs

4. **Advanced Aggregations**
   - Rollup and cube operations
   - Pivoting for cross-tab analysis
   - Statistical aggregates

5. **Performance Optimizations**
   - Incremental models
   - Pre-aggregations
   - Partitioning strategies
   - Index hints

## Implementation Phases

### Phase 1: Staging Layer (Current Focus)
1. Complete app_database staging models
2. Add Stripe staging models
3. Add HubSpot staging models
4. Implement data quality tests

### Phase 2: Intermediate Layer
1. Customer core logic
2. Subscription revenue calculations
3. Device performance aggregations
4. Marketing attribution logic

### Phase 3: Entity Layer - Atomic Tables
1. Build all 7 atomic entity tables
2. Implement health scoring algorithms
3. Add comprehensive testing

### Phase 4: Entity Layer - History Tables
1. Implement SCD Type 2 for all entities
2. Change detection logic
3. Temporal query patterns

### Phase 5: Entity Layer - Grain Tables
1. Daily grain for business entities
2. Hourly grain for operational entities
3. Performance optimizations

### Phase 6: Mart Layer
1. Executive dashboards
2. Customer success views
3. Operations monitoring
4. Marketing analytics

### Phase 7: Testing & Documentation
1. Data quality tests
2. Business logic validation
3. Performance benchmarks
4. Educational documentation

## Success Criteria
- Comprehensive coverage of SaaS metrics
- Demonstrable advanced SQL patterns
- Clear educational value
- Production-ready performance
- Extensive test coverage
- Well-documented business logic