# Synthetic Data Generation TODO

## Overview
This document outlines the complete process for generating synthetic data using MostlyAI to populate the raw layer of our dbt project. The synthetic data will have full referential integrity and create realistic metrics and dimensions for all entities in our bar management SaaS platform.

## Load Size Configurations

### DEV Environment (Small)
- **100** customer accounts
- **150** locations (~1.5 per account)
- **300** users (~3 per account)
- **450** IoT devices (~3 per location)
- **500K** tap events
- Proportional billing, CRM, and marketing data

### QA Environment (Medium)
- **10,000** customer accounts
- **15,000** locations (~1.5 per account)
- **30,000** users (~3 per account)
- **45,000** IoT devices (~3 per location)
- **50M** tap events
- Proportional billing, CRM, and marketing data

### PRODUCTION Environment (Large)
- **40,000** customer accounts
- **60,000** locations (~1.5 per account)
- **120,000** users (~3 per account)
- **180,000** IoT devices (~3 per location)
- **200M** tap events
- Complete billing, CRM, and marketing data
- Full referential integrity across all tables
- Realistic business metrics and patterns

---

## MILESTONE 1: Environment Setup & MostlyAI Configuration

### 1. Install MostlyAI Python SDK
- Execute: `pip install mostlyai`
- Verify installation with import test
- **TEST**: Successfully import mostlyai package

### 2. Configure MostlyAI Connection
- Set up API credentials
- Create MostlyAI client instance
- Configure synthetic data generation parameters
- **TEST**: Verify API connection works

### 3. Database Connection Setup
- Establish PostgreSQL connection to saas_platform_dev
- Verify raw schema exists
- Create helper functions for data insertion
- **TEST**: Successfully connect and query raw schema

### 4. Environment Size Configuration
- Create configuration module for load sizes (DEV/QA/PRODUCTION)
- Set environment variable: `DATAGEN_ENV` (defaults to DEV)
- Load appropriate scaling factors for all entities
- **TEST**: Configuration correctly loads for selected environment

---

## MILESTONE 2: Core Entity Generation (Hierarchical Order)

### 5. Generate Accounts (Scaled by Environment)
- **DEV**: 100 accounts | **QA**: 10,000 accounts | **PRODUCTION**: 40,000 accounts
- Create base customer accounts with:
  - Realistic company names across industries
  - Industry distribution (Restaurant 40%, Bar 30%, Hotel 20%, Other 10%)
  - Subscription tiers (Basic 50%, Pro 35%, Enterprise 15%)
  - MRR values correlated with tier ($299-$999 Basic, $999-$2999 Pro, $2999-$9999 Enterprise)
  - Employee counts (5-500 based on tier)
  - Created dates spanning 5 years with growth curve
- **TEST**: Verify account count matches environment configuration

### 6. Generate Locations (Scaled by Environment)
- **DEV**: 150 locations | **QA**: 15,000 locations | **PRODUCTION**: 60,000 locations
- Create 1-5 locations per account (weighted distribution)
- Geographic distribution across US states
- Location types (Main 40%, Branch 40%, Franchise 20%)
- Realistic addresses and zip codes
- **TEST**: Verify location count and correct account_id references

### 7. Generate Users (Scaled by Environment)
- **DEV**: 300 users | **QA**: 30,000 users | **PRODUCTION**: 120,000 users
- Create 2-10 users per account based on tier
- Role distribution (Admin 10%, Manager 30%, Staff 60%)
- Email patterns matching company domains
- Login frequency patterns by role
- Permissions JSON based on roles
- **TEST**: Verify user count with proper account associations

### 8. Generate Devices (Scaled by Environment)
- **DEV**: 450 devices | **QA**: 45,000 devices | **PRODUCTION**: 180,000 devices
- Create 2-5 devices per location
- Device models and firmware versions
- Installation dates after location creation
- Status distribution (online 85%, offline 10%, maintenance 5%)
- Last seen patterns based on status
- **TEST**: Verify device count with location/account references

### 9. Generate Subscriptions (Scaled by Environment)
- **DEV**: 125 subscriptions | **QA**: 12,500 subscriptions | **PRODUCTION**: 50,000 subscriptions
- Create subscription history for accounts
- Plan progression patterns (upgrades/downgrades)
- Churn patterns (10% annual churn rate)
- Trial conversions (70% trial-to-paid)
- MRR matching account records
- **TEST**: Verify subscription continuity and MRR consistency

---

## MILESTONE 3: Stripe Billing Data Generation

### 10. Generate Stripe Customers (Scaled by Environment)
- **DEV**: 100 customers | **QA**: 10,000 customers | **PRODUCTION**: 40,000 customers
- Map 1:1 with accounts
- Matching email patterns
- Metadata containing account_id mapping
- **TEST**: Verify all accounts have Stripe customers

### 11. Generate Stripe Prices (12 records - same for all environments)
- Create pricing tiers for all plans
- Monthly and annual variants
- Proper unit amounts in cents
- **TEST**: Verify all subscription tiers have prices

### 12. Generate Stripe Subscriptions (Scaled by Environment)
- **DEV**: 125 subscriptions | **QA**: 12,500 subscriptions | **PRODUCTION**: 50,000 subscriptions
- Match app subscriptions
- Proper billing periods
- Status transitions over time
- Trial period handling
- **TEST**: Verify billing periods align with app subscriptions

### 13. Generate Stripe Subscription Items (Scaled by Environment)
- **DEV**: 175 items | **QA**: 17,500 items | **PRODUCTION**: 70,000 items
- Line items for subscriptions
- Multiple items for add-ons
- Quantity variations
- **TEST**: Verify all subscriptions have items

### 14. Generate Stripe Invoices (Scaled by Environment)
- **DEV**: 1,500 invoices | **QA**: 150,000 invoices | **PRODUCTION**: 600,000 invoices
- Monthly invoices for active subscriptions
- Payment success rate 95%
- Late payments patterns
- **TEST**: Verify invoice coverage for billing periods

### 15. Generate Stripe Charges (Scaled by Environment)
- **DEV**: 1,425 charges | **QA**: 142,500 charges | **PRODUCTION**: 570,000 charges
- Successful payments for invoices
- Payment method distributions
- Geographic patterns
- **TEST**: Verify charge totals match invoice amounts

### 16. Generate Stripe Events (Scaled by Environment)
- **DEV**: 10,000 events | **QA**: 1,000,000 events | **PRODUCTION**: 4,000,000 events
- Complete audit trail
- Event types for all entity changes
- Proper chronological ordering
- **TEST**: Verify event timeline consistency

---

## MILESTONE 4: HubSpot CRM Data Generation

### 17. Generate HubSpot Companies (Scaled by Environment)
- **DEV**: 125 companies | **QA**: 12,500 companies | **PRODUCTION**: 50,000 companies
- Include all accounts plus prospects
- Industry matching
- Domain generation
- **TEST**: Verify company coverage

### 18. Generate HubSpot Contacts (Scaled by Environment)
- **DEV**: 500 contacts | **QA**: 50,000 contacts | **PRODUCTION**: 200,000 contacts
- Multiple contacts per company
- Role-based email patterns
- Lead scoring distribution
- **TEST**: Verify contact-company associations

### 19. Generate HubSpot Deals (Scaled by Environment)
- **DEV**: 250 deals | **QA**: 25,000 deals | **PRODUCTION**: 100,000 deals
- Sales pipeline progression
- Win rate 25%
- Deal values correlated with company size
- Stage duration patterns
- **TEST**: Verify deal pipeline integrity

### 20. Generate HubSpot Engagements (Scaled by Environment)
- **DEV**: 2,500 engagements | **QA**: 250,000 engagements | **PRODUCTION**: 1,000,000 engagements
- Call, email, meeting patterns
- Engagement frequency by deal stage
- Rep activity patterns
- **TEST**: Verify engagement timeline logic

### 21. Generate HubSpot Tickets (Scaled by Environment)
- **DEV**: 400 tickets | **QA**: 40,000 tickets | **PRODUCTION**: 160,000 tickets
- Support ticket patterns
- Priority distribution
- Resolution time patterns
- **TEST**: Verify ticket lifecycle consistency

---

## MILESTONE 5: Marketing Data Generation

### 22. Generate Marketing Campaigns (Scaled by Environment)
- **DEV**: 25 campaigns | **QA**: 1,250 campaigns | **PRODUCTION**: 5,000 campaigns
- Google Ads campaigns (40%)
- Meta campaigns (30%)
- LinkedIn campaigns (20%)
- Email campaigns (10%)
- Proper date ranges and budgets
- **TEST**: Verify campaign continuity

### 23. Generate Campaign Performance Data (Scaled by Environment)
- **DEV**: 7,500 records | **QA**: 375,000 records | **PRODUCTION**: 1,500,000 records
- Daily performance metrics
- Realistic CTR/CPC by channel
- Budget pacing patterns
- Seasonal variations
- **TEST**: Verify performance KPIs are realistic

### 24. Generate Attribution Touchpoints (Scaled by Environment)
- **DEV**: 15,000 touchpoints | **QA**: 750,000 touchpoints | **PRODUCTION**: 3,000,000 touchpoints
- Multi-touch journeys
- Channel distribution
- Attribution weight calculations
- Conversion paths
- **TEST**: Verify attribution sums to 100%

### 25. Generate Marketing Qualified Leads (Scaled by Environment)
- **DEV**: 200 MQLs | **QA**: 20,000 MQLs | **PRODUCTION**: 80,000 MQLs
- Lead scoring progression
- Source attribution
- Conversion funnel metrics
- **TEST**: Verify MQL criteria consistency

### 26. Generate Google Analytics Sessions (Scaled by Environment)
- **DEV**: 30,000 sessions | **QA**: 1,500,000 sessions | **PRODUCTION**: 6,000,000 sessions
- Realistic traffic patterns
- Source/medium distributions
- Bounce rates by page type
- Session durations
- **TEST**: Verify session metrics align with industry benchmarks

---

## MILESTONE 6: Application Activity Data Generation

### 27. Generate User Sessions (Scaled by Environment)
- **DEV**: 50,000 sessions | **QA**: 2,500,000 sessions | **PRODUCTION**: 10,000,000 sessions
- Login patterns by role
- Session duration distributions
- Device type patterns
- Geographic IP distribution
- **TEST**: Verify session coverage for active users

### 28. Generate Page Views (Scaled by Environment)
- **DEV**: 250,000 page views | **QA**: 12,500,000 page views | **PRODUCTION**: 50,000,000 page views
- Page flow patterns
- Time on page distributions
- Exit page patterns
- Feature page correlations
- **TEST**: Verify page view totals match session counts

### 29. Generate Feature Usage (Scaled by Environment)
- **DEV**: 150,000 events | **QA**: 7,500,000 events | **PRODUCTION**: 30,000,000 events
- Feature adoption curves
- Usage frequency by tier
- Success/error patterns
- Feature category distribution
- **TEST**: Verify feature usage aligns with subscriptions

---

## MILESTONE 7: IoT Device Data Generation

### 30. Generate Tap Events (Scaled by Environment)
- **DEV**: 500,000 events | **QA**: 50,000,000 events | **PRODUCTION**: 200,000,000 events
- Hourly patterns (peak 6-10pm)
- Day of week variations
- Product distribution
- Volume patterns by product type
- Temperature readings
- Duration distributions
- **TEST**: Verify event volumes match device activity

### 31. Generate Device Health Metrics
- Uptime calculations from events
- Performance degradation patterns
- Maintenance correlations
- **TEST**: Verify device health aligns with status

---

## MILESTONE 8: Data Integrity & Relationships

### 32. Verify Referential Integrity
- Run foreign key constraint checks
- Verify all ID references exist
- Check for orphaned records
- **TEST**: Zero constraint violations

### 33. Validate Business Logic
- MRR calculations consistency
- Subscription lifecycle integrity
- Attribution model accuracy
- Device uptime calculations
- **TEST**: Business metrics within expected ranges

### 34. Generate Correlation Patterns
- High-value accounts have more users/devices
- Engaged users correlate with lower churn
- Device uptime affects satisfaction
- Marketing spend correlates with growth
- **TEST**: Statistical correlations are realistic

---

## MILESTONE 9: Time-Series Consistency

### 35. Ensure Temporal Integrity
- All timestamps follow logical order
- Growth patterns over 5 years
- Seasonal variations in metrics
- Business hour patterns
- **TEST**: No temporal paradoxes

### 36. Create Realistic Growth Curves
- Account growth 40% YoY
- MRR expansion patterns
- User adoption curves
- Feature rollout timelines
- **TEST**: Growth metrics match SaaS benchmarks

---

## MILESTONE 10: Final Validation & Loading

### 37. Run Complete Data Quality Checks
- Row count verification per environment
- Distribution analysis
- Outlier detection
- Missing value assessment
- **TEST**: All quality metrics pass

### 38. Execute Bulk Data Loading
- Disable constraints during load
- Use COPY commands for performance
- Load in dependency order
- Re-enable constraints
- **TEST**: All data loaded successfully

### 39. Verify dbt Model Compilation
- Run dbt compile
- Check for dependency errors
- Verify source freshness
- **TEST**: All models compile successfully

### 40. Generate Summary Statistics
- Total records per table by environment
- Key metric calculations
- Relationship cardinalities
- Data freshness report
- **TEST**: Summary matches expectations

### 41. Create Data Catalog Documentation
- Document synthetic data characteristics
- List key distributions used
- Note any simplifications made
- Provide metric baselines for each environment
- **TEST**: Documentation complete and accurate

---

## Success Criteria

### Data Volume Targets by Environment

#### DEV Environment
- 100 accounts with complete data ecosystem
- 500K+ total records across all tables
- Fast data generation for rapid testing

#### QA Environment  
- 10,000 accounts with complete data ecosystem
- 50M+ total records across all tables
- Representative data for integration testing

#### PRODUCTION Environment
- 40,000 accounts with complete data ecosystem
- 200M+ total records across all tables
- Full-scale data for performance testing

### Quality Metrics
- 100% referential integrity
- Zero constraint violations
- Realistic business metric ranges
- Proper temporal ordering

### Business Realism
- SaaS metrics align with industry benchmarks
- Customer behavior patterns are realistic
- IoT device data shows expected patterns
- Marketing attribution models are coherent

### Environment Scaling Rules
All entity counts scale proportionally based on the account count:
- Locations: ~1.5x accounts
- Users: ~3x accounts
- Devices: ~3x locations
- Subscriptions: ~1.25x accounts
- Tap Events: ~5K per device (DEV), ~1.1K per device (QA), ~1.1K per device (PROD)

This comprehensive plan ensures complete synthetic data generation with full referential integrity, realistic metrics, and proper testing at each milestone to verify data quality and consistency across all three environment sizes.