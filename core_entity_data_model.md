# Core Entity-Centric Data Model

## Executive Summary
This document maps the primary entities in our SaaS data platform, focusing on a bar management/hospitality platform with integrated marketing, billing, and operational systems. The model supports both transactional operations and analytical workloads with clear dimensional modeling patterns.

## Primary Entities Overview

### 1. **Account** (Master Entity)
- **Table**: `accounts`
- **Primary Key**: `account_id` (UUID)
- **Grain**: One record per customer account
- **Type**: Slowly Changing Dimension (Type 2 candidate)
- **Purpose**: Top-level customer organization entity

**Key Attributes**:
- `account_name` - Business name
- `account_type` - Subscription tier (enterprise, professional, basic)
- `industry_vertical` - Business classification
- `status` - Account lifecycle status (active, trial, churned, suspended)
- `total_locations` - Denormalized count for quick access
- `employee_count` - Business size indicator
- Geographic attributes (city, state, country)

**Slowly Changing Dimension Patterns**:
- Status changes (active → trial → churned) - Track with effective dates
- Account type upgrades/downgrades - Historical significance for revenue analysis
- Contact information updates - Maintain current for operational use

### 2. **Location** 
- **Table**: `locations`
- **Primary Key**: `location_id` (UUID)
- **Foreign Key**: `account_id` → accounts
- **Grain**: One record per physical business location
- **Type**: Slowly Changing Dimension (Type 1/2 hybrid)

**Key Attributes**:
- Geographic data (address, lat/lng, timezone)
- Operational metadata (seating_capacity, total_taps, business_hours)
- `active_device_count` - Denormalized for performance
- Lifecycle dates (opened_date, closed_date)

**Relationships**:
- **1:N** with Devices (one location has many devices)
- **1:N** with Users (location-specific users)
- **N:1** with Account (many locations per account)

### 3. **User**
- **Table**: `users`
- **Primary Key**: `user_id` (UUID)
- **Foreign Keys**: `account_id`, `location_id` (optional)
- **Grain**: One record per individual user
- **Type**: Slowly Changing Dimension (Type 2 for role changes)

**Key Attributes**:
- Identity (email, first_name, last_name)
- `role_type` - Permission level (owner, admin, manager, operator, viewer)
- `status` - User lifecycle (active, inactive, suspended, pending_invitation)
- `last_login_at` - Engagement indicator

**SCD Considerations**:
- Role changes should be tracked historically for audit purposes
- Status changes important for user adoption analysis

### 4. **Device** (IoT/Hardware)
- **Table**: `devices`
- **Primary Key**: `device_id` (UUID)
- **Foreign Keys**: `location_id`, `account_id`
- **Grain**: One record per physical IoT device
- **Type**: Slowly Changing Dimension (Type 1 for most attributes)

**Key Attributes**:
- Hardware specs (device_type, model_number, serial_number, firmware_version)
- Maintenance tracking (installation_date, last_maintenance_date, next_maintenance_due)
- Operational status (active, offline, maintenance, decommissioned)
- `last_heartbeat_at` - Device health indicator

### 5. **Subscription** (Billing Core)
- **Table**: `subscriptions`
- **Primary Key**: `subscription_id` (UUID)
- **Foreign Key**: `account_id`
- **Grain**: One record per subscription period
- **Type**: Slowly Changing Dimension (Type 2 - critical for revenue tracking)

**Key Attributes**:
- Plan details (plan_type, plan_name, billing_cycle)
- Pricing (base_price_cents)
- Lifecycle tracking (trial dates, period boundaries, cancellation)
- Status progression (trialing → active → past_due → canceled)

**Critical for Revenue Analytics**:
- Current and historical MRR/ARR calculations
- Churn analysis and cohort studies
- Subscription lifecycle metrics

### 6. **Stripe Integration Entities** (Payment Processing)

#### Stripe Customer
- **Table**: `stripe_customers`
- **Primary Key**: `id` (Stripe's customer ID)
- **Grain**: One record per Stripe customer (maps to Account)

#### Stripe Subscription
- **Table**: `stripe_subscriptions`  
- **Primary Key**: `id` (Stripe's subscription ID)
- **Foreign Key**: `customer` → stripe_customers
- **Grain**: One record per Stripe subscription instance

#### Stripe Invoice
- **Table**: `stripe_invoices`
- **Primary Key**: `id` (Stripe's invoice ID)
- **Grain**: One record per billing invoice
- **Type**: Fact Table (transactional billing events)

#### Stripe Charge
- **Table**: `stripe_charges`
- **Primary Key**: `id` (Stripe's charge ID)
- **Grain**: One record per payment attempt
- **Type**: Fact Table (payment transactions)

### 7. **Event/Telemetry Entities** (High-Volume Fact Tables)

#### Tap Events (IoT Data)
- **Table**: `tap_events`
- **Primary Key**: `tap_event_id` (UUID)
- **Foreign Keys**: `device_id`, `location_id`, `account_id`
- **Grain**: One record per tap/pour event
- **Type**: Fact Table (high-volume operational events)

**Measures**:
- `flow_rate_ml_per_sec`, `total_volume_ml` - Volumetric measures
- `temperature_celsius`, `pressure_psi` - Environmental measures
- `event_timestamp` - Time dimension key

**Partitioning Strategy**: Partition by event_timestamp (monthly/weekly)

#### User Sessions (Web Analytics)
- **Table**: `user_sessions`
- **Primary Key**: `session_id` (UUID)
- **Foreign Keys**: `user_id`, `account_id`
- **Grain**: One record per user session
- **Type**: Fact Table (user engagement events)

#### Page Views
- **Table**: `page_views`
- **Primary Key**: `page_view_id` (UUID)
- **Foreign Key**: `session_id` → user_sessions
- **Grain**: One record per page view
- **Type**: Fact Table (detailed web analytics)

#### Feature Usage
- **Table**: `feature_usage`
- **Primary Key**: `usage_id` (UUID)
- **Foreign Keys**: `user_id`, `account_id`
- **Grain**: One record per feature interaction
- **Type**: Fact Table (product analytics)

### 8. **Marketing Entities**

#### Marketing Qualified Leads
- **Table**: `marketing_qualified_leads`
- **Primary Key**: `lead_id` (UUID)
- **Grain**: One record per qualified lead
- **Type**: Slowly Changing Dimension (Type 2 for status progression)

#### Attribution Touchpoints
- **Table**: `attribution_touchpoints`
- **Primary Key**: `touchpoint_id` (UUID)
- **Foreign Keys**: `user_id`, `account_id`, `session_id`
- **Grain**: One record per marketing touchpoint
- **Type**: Fact Table (marketing attribution events)

#### Campaign Performance Tables
- **Tables**: `google_ads_campaign_performance`, `meta_ads_campaign_insights`, `linkedin_ads_campaign_analytics`
- **Grain**: One record per campaign per day
- **Type**: Fact Tables (aggregated marketing metrics)

### 9. **HubSpot CRM Integration**
- **Tables**: `hubspot_companies`, `hubspot_contacts`, `hubspot_deals`, `hubspot_engagements`
- **Type**: Operational data store (JSON-heavy, semi-structured)
- **Integration Pattern**: Raw data ingestion with property extraction

### 10. **Email Marketing** (Iterable)
- **Table**: `iterable_email_events`
- **Primary Key**: Composite (`message_id`, `email`, `event_name`, `created_at`)
- **Grain**: One record per email event (sent, opened, clicked, etc.)
- **Type**: Fact Table (email engagement events)

## Entity Relationship Diagram (Narrative)

### Core Hierarchy:
```
Account (1) ←→ (N) Location (1) ←→ (N) Device
    ↓                    ↓
    (N)                  (N)
    User                Tap Events
    ↓
    (N)
User Sessions → Page Views
    ↓
    (N)
Feature Usage
```

### Billing Flow:
```
Account → Subscription → Stripe Customer → Stripe Subscription → Stripe Invoice → Stripe Charge
```

### Marketing Attribution:
```
MQL → Attribution Touchpoints → User Sessions → Account Conversion
     ↑
Campaign Performance (Google/Meta/LinkedIn) → Email Events (Iterable)
```

## Dimensional Modeling Classifications

### Dimension Tables (SCD Types):
1. **Account** - SCD Type 2 (track status/tier changes)
2. **Location** - SCD Type 1/2 hybrid (operational changes vs. closure events)
3. **User** - SCD Type 2 (role and status changes)
4. **Device** - SCD Type 1 (status updates overwrite)
5. **Subscription** - SCD Type 2 (critical for revenue analysis)
6. **MQL** - SCD Type 2 (qualification progression)

### Fact Tables (High Volume):
1. **Tap Events** - IoT sensor data (highest volume)
2. **User Sessions** - Web analytics
3. **Page Views** - Detailed clickstream
4. **Feature Usage** - Product engagement
5. **Attribution Touchpoints** - Marketing attribution
6. **Stripe Charges** - Payment transactions
7. **Stripe Invoices** - Billing events
8. **Email Events** - Campaign engagement
9. **Campaign Performance** - Marketing metrics (pre-aggregated)

### Bridge/Junction Tables:
- **Stripe Integration**: Links internal entities to external payment system
- **HubSpot Integration**: Links internal entities to CRM system
- **Attribution Touchpoints**: Links marketing activities to conversions

## Key Business Metrics Foundation

### Revenue Metrics:
- **MRR/ARR**: Calculated from `subscriptions` table with SCD Type 2 tracking
- **Churn Rate**: Account status transitions in `accounts`
- **ARPU**: Revenue per account from `stripe_invoices` / active accounts

### Product Metrics:
- **Feature Adoption**: Aggregations from `feature_usage`
- **User Engagement**: Session analysis from `user_sessions` and `page_views`
- **Device Health**: Operational metrics from `devices` and `tap_events`

### Marketing Metrics:
- **Lead Conversion**: MQL progression through `marketing_qualified_leads`
- **Attribution**: Multi-touch attribution via `attribution_touchpoints`
- **Campaign ROI**: Performance data linked to conversion outcomes

### Operational Metrics:
- **Location Performance**: Aggregated tap events by location
- **Device Utilization**: Usage patterns from IoT data
- **Support Efficiency**: Through integrated ticketing (if implemented)

## Data Quality Considerations

### Primary Key Integrity:
- All entities use UUIDs for global uniqueness
- Foreign key constraints enforced at database level
- Composite keys used for event tables where appropriate

### Temporal Consistency:
- Consistent timestamp fields (`created_at`, `updated_at`)
- Automated triggers for timestamp maintenance
- Event tables include both event time and ingestion time

### Referential Integrity:
- Cascading relationship rules defined
- Soft deletes preferred over hard deletes for audit trails
- Status-based logical deletion patterns

This model provides a solid foundation for both operational workloads and analytical reporting, with clear patterns for dimensional modeling and metric calculation.

