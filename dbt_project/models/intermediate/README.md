# Intermediate Layer Models - Aligned with Staging Layer

## Overview
The intermediate layer serves as a bridge between the staging layer (raw source data) and the entity layer (Entity-Centric Models). Each intermediate model combines data from multiple staging tables and applies business logic transformations to prepare data for the final entity models.

## Alignment with Staging Layer

The intermediate models are built exclusively from the following staging sources:

### App Database Sources
- `stg_app_database__accounts` - Customer account master data
- `stg_app_database__devices` - IoT device registry and status
- `stg_app_database__feature_usage` - Premium feature adoption tracking
- `stg_app_database__locations` - Physical location information
- `stg_app_database__page_views` - Web analytics data
- `stg_app_database__subscriptions` - Subscription status and plans
- `stg_app_database__tap_events` - Device usage events
- `stg_app_database__user_sessions` - User session tracking
- `stg_app_database__users` - User profiles and roles

### HubSpot CRM Sources
- `stg_hubspot__companies` - CRM company records
- `stg_hubspot__contacts` - CRM contact information
- `stg_hubspot__deals` - Sales pipeline data
- `stg_hubspot__engagements` - Customer interaction history
- `stg_hubspot__owners` - Sales rep assignments
- `stg_hubspot__tickets` - Support ticket data

### Marketing Sources
- `stg_marketing__attribution_touchpoints` - Multi-channel touchpoint data
- `stg_marketing__facebook_ads_campaigns` - Facebook campaign performance
- `stg_marketing__google_ads_campaigns` - Google Ads campaign data
- `stg_marketing__google_analytics_sessions` - Website session analytics
- `stg_marketing__iterable_campaigns` - Email campaign metrics
- `stg_marketing__linkedin_ads_campaigns` - LinkedIn campaign data
- `stg_marketing__marketing_qualified_leads` - MQL conversion tracking

### Stripe Billing Sources
- `stg_stripe__charges` - Payment transaction records
- `stg_stripe__customers` - Stripe customer profiles
- `stg_stripe__events` - Stripe webhook events
- `stg_stripe__invoices` - Invoice and payment history
- `stg_stripe__payment_intents` - Payment attempt tracking
- `stg_stripe__prices` - Product pricing information
- `stg_stripe__subscription_items` - Subscription line items
- `stg_stripe__subscriptions` - Subscription status and billing

## Entity-Based Organization

The intermediate layer is organized by the seven core entities in our Entity-Centric Model:

### 1. Campaigns (`/campaigns`)
- **int_campaigns__core**: Unified campaign view across all marketing platforms
- **int_campaigns__attribution**: Multi-touch attribution modeling and conversion tracking

### 2. Customers (`/customers`)
- **int_customers__core**: Customer 360 view combining accounts, subscriptions, and CRM data

### 3. Devices (`/devices`)
- **int_devices__performance_health**: Device operational metrics and health scoring

### 4. Features (`/features`)
- **int_features__core**: Feature usage analytics and adoption metrics
- **int_features__adoption_patterns**: Feature value analysis by customer segment

### 5. Locations (`/locations`)
- **int_locations__core**: Location master data with operational status
- **int_locations__operational_metrics**: Detailed performance and utilization metrics

### 6. Subscriptions (`/subscriptions`)
- **int_subscriptions__core**: Reconciled subscription data from app and Stripe
- **int_subscriptions__revenue_metrics**: Payment health and lifetime value calculations

### 7. Users (`/users`)
- **int_users__core**: User profiles with 30-day activity metrics
- **int_users__engagement_metrics**: Behavioral analysis and segmentation

## Key Design Principles

### 1. Data Source Reconciliation
Models that combine data from multiple sources (e.g., app subscriptions + Stripe subscriptions) include:
- Data quality flags to identify mismatches
- Source tracking to understand data lineage
- Reconciliation logic to handle conflicts

### 2. Metric Calculation Standards
All calculated metrics follow consistent patterns:
- **Scores**: 0-100 scale for health, risk, and value scores
- **Rates**: Expressed as percentages (0-100)
- **Time Windows**: 30-day for activity metrics, appropriate grains for other analyses
- **NULL Handling**: COALESCE with appropriate defaults

### 3. Business Logic Implementation
Each model implements domain-specific business logic:
- Customer health scoring incorporating multiple factors
- Multi-touch attribution models for marketing
- Device performance calculations
- Feature value correlation with revenue

### 4. Performance Optimization
All models are materialized as tables for:
- Fast query performance in downstream entity models
- Reduced complexity in final transformations
- Easier debugging and data quality checks

## Usage in Entity Layer

The intermediate models are designed to be the primary sources for entity models:

1. **Entity Atomic Tables** will select from intermediate models
2. **Entity History Tables** will track changes in intermediate model outputs
3. **Entity Grain Tables** will aggregate intermediate model metrics

## Maintenance Guidelines

1. **Never modify staging tables** - They are the source of truth
2. **Add new intermediate models** when new business logic is needed
3. **Update existing models** when business rules change
4. **Document all calculations** in model comments and schema.yml
5. **Test thoroughly** - Each model should have data quality tests

## Next Steps

With the intermediate layer complete and aligned with staging, the next phase is building the Entity-Centric Models (entity layer) with their three-table architecture:
- Atomic instance tables
- Change history tables  
- Strategic grain tables