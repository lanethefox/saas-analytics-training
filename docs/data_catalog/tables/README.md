[🏠 Home](../../../) > [📚 Technical Docs](../../) > [📊 Data Catalog](../) > 📋 Tables

# 📋 Table Documentation

Complete reference for all tables in the TapFlow Analytics data warehouse.

**Last Updated:** 2024-12-16 | **Est. Reading Time:** 5 min | **Difficulty:** All Levels

## 🎯 Overview

This section contains detailed documentation for every table across all schemas. Each table page includes:
- 📝 Business description
- 📊 Column definitions
- 🔑 Primary and foreign keys
- 📈 Row counts and statistics
- 💡 Sample queries
- ✅ Data quality metrics

## 🔍 Finding Tables

### Quick Search by Category

#### 🏢 Core Business Entities
**Customer & Account Management**
- [accounts](./raw_app_database_accounts.md) - Customer master records
- [users](./raw_app_database_users.md) - Individual user accounts
- [account_users](./raw_app_database_account_users.md) - User-account relationships

**Subscription & Billing**
- [subscriptions](./raw_app_database_subscriptions.md) - Active subscriptions
- [subscription_events](./raw_app_database_subscription_events.md) - Subscription changes
- [invoices](./raw_app_database_invoices.md) - Billing records

#### 📍 Physical Infrastructure
**Locations**
- [locations](./raw_app_database_locations.md) - Bar/restaurant locations
- [location_types](./raw_app_database_location_types.md) - Venue categories
- [location_attributes](./raw_app_database_location_attributes.md) - Additional details

**Devices & IoT**
- [devices](./raw_app_database_devices.md) - Tap device inventory
- [device_types](./raw_app_database_device_types.md) - Device models
- [device_events](./raw_app_database_device_events.md) - Status changes

#### 📊 Usage & Analytics
**Tap Events**
- [tap_events](./raw_app_database_tap_events.md) - Pour transactions
- [tap_event_aggregates](./staging_tap_event_aggregates.md) - Hourly summaries

**Web Analytics**
- [ga_sessions](./raw_ga_session_analytics.md) - Google Analytics data
- [feature_usage](./raw_app_database_feature_usage.md) - Platform usage

#### 💰 Financial Data
**Revenue**
- [daily_mrr](./metrics_daily_mrr.md) - Daily MRR snapshots
- [revenue_by_segment](./metrics_revenue_by_segment.md) - Segmented revenue

**Costs & Margins**
- [device_costs](./raw_app_database_device_costs.md) - Hardware costs
- [support_costs](./raw_app_database_support_costs.md) - Service costs

### Alphabetical Index

[A](#a) | [B](#b) | [C](#c) | [D](#d) | [E](#e) | [F](#f) | [G](#g) | [H](#h) | [I](#i) | [J](#j) | [K](#k) | [L](#l) | [M](#m) | [N](#n) | [O](#o) | [P](#p) | [Q](#q) | [R](#r) | [S](#s) | [T](#t) | [U](#u) | [V](#v) | [W](#w) | [X](#x) | [Y](#y) | [Z](#z)

#### A
- [account_attributes](./raw_app_database_account_attributes.md)
- [account_users](./raw_app_database_account_users.md)
- [accounts](./raw_app_database_accounts.md)
- [alert_configurations](./raw_app_database_alert_configurations.md)
- [alerts](./raw_app_database_alerts.md)

#### B
- [billing_addresses](./raw_app_database_billing_addresses.md)
- [billing_events](./raw_app_database_billing_events.md)

#### C
- [campaigns](./raw_marketing_campaigns.md)
- [churn_predictions](./ml_churn_predictions.md)
- [customer_health_scores](./metrics_customer_health_scores.md)

#### D
- [daily_active_users](./metrics_daily_active_users.md)
- [device_diagnostics](./raw_app_database_device_diagnostics.md)
- [device_events](./raw_app_database_device_events.md)
- [devices](./raw_app_database_devices.md)

*(Continue for all letters...)*

## 📊 Table Statistics Summary

### Largest Tables by Row Count
| Table | Schema | Row Count | Growth Rate |
|-------|--------|-----------|-------------|
| tap_events | raw | 25M | +50K/day |
| device_events | raw | 10M | +20K/day |
| ga_sessions | raw | 5M | +10K/day |
| feature_usage | raw | 3M | +5K/day |
| subscriptions | raw | 100K | +100/day |

### Most Queried Tables
1. 🥇 subscriptions - Revenue analysis
2. 🥈 tap_events - Usage patterns
3. 🥉 devices - Operational metrics
4. accounts - Customer analysis
5. locations - Geographic insights

### Critical Tables for Each Role
**Sales Analysts**
- subscriptions, subscription_events
- accounts, opportunities
- revenue metrics tables

**Marketing Analysts**
- campaigns, campaign_responses
- ga_sessions, attribution
- lead sources, conversions

**Product Analysts**
- feature_usage, user_sessions
- tap_events, device_events
- adoption metrics

**Customer Success**
- customer_health_scores
- support_tickets, churn_predictions
- usage_trends, satisfaction_scores

## 🛠️ Using Table Documentation

### Table Page Structure
Each table documentation page follows this format:

```markdown
# Table: schema.table_name

## Overview
- Purpose and business context
- Update frequency
- Data sources

## Columns
- Complete list with descriptions
- Data types and constraints
- Business rules

## Keys & Relationships
- Primary key definition
- Foreign key relationships
- Indexes for performance

## Sample Data
- Example rows
- Common values
- Edge cases

## Common Queries
- Copy-paste SQL examples
- Best practices
- Performance tips

## Data Quality
- Completeness metrics
- Validation rules
- Known issues
```

### Best Practices
1. **Always check update frequency** before using for real-time analysis
2. **Review relationships** before writing JOINs
3. **Check data quality metrics** for reliability
4. **Use indexed columns** in WHERE clauses
5. **Copy sample queries** as starting templates

## 🔄 Table Lifecycle

### Table Creation Process
1. **Identified Need** - Business requirement
2. **Design Review** - Schema and naming
3. **Implementation** - DDL and documentation
4. **Testing** - Data quality checks
5. **Production** - Available for use

### Deprecation Process
1. **Marked Deprecated** - Warning added
2. **Migration Period** - Alternative provided
3. **Read-Only** - No new data
4. **Archived** - Moved to archive schema
5. **Removed** - After notification period

## 📈 Performance Tips

### For Large Tables
- Use date filters to limit data
- Include partition keys in queries
- Avoid SELECT *
- Use appropriate aggregation levels

### For Joins
- Join on indexed columns
- Filter before joining
- Use staging/intermediate tables
- Consider materialized views

---

<div class="nav-footer">

[← Data Catalog](../) | [Browse Tables →](#quick-search-by-category)

</div>

**Need help?** See [query patterns](../../api_reference/query_patterns.md) or [performance guide](../../api_reference/performance_tips.md)