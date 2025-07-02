# Data Platform Row Counts Report

Generated: 2025-06-25 15:26:15

## Summary by Schema

### STAGING Schema
- Total objects: 30
- Objects with data: 4

### INTERMEDIATE Schema
- Total objects: 15
- Objects with data: 8

### METRICS Schema
- Total objects: 16
- Objects with data: 15


## Detailed Row Counts

### STAGING Schema

| Table/View | Type | Row Count |
|------------|------|----------:|
| stg_app_database__accounts | View | 1,000 |
| stg_app_database__devices | View | 210,297 |
| stg_app_database__feature_usage | Table | 0 |
| stg_app_database__locations | View | 6,066 |
| stg_app_database__page_views | Table | 0 |
| stg_app_database__subscriptions | View | 0 |
| stg_app_database__tap_events | Table | 0 |
| stg_app_database__user_sessions | Table | 0 |
| stg_app_database__users | View | 14,363 |
| stg_hubspot__companies | View | 0 |
| stg_hubspot__contacts | View | 0 |
| stg_hubspot__deals | View | 0 |
| stg_hubspot__engagements | Table | 0 |
| stg_hubspot__owners | View | 0 |
| stg_hubspot__tickets | Table | 0 |
| stg_marketing__attribution_touchpoints | View | 0 |
| stg_marketing__facebook_ads_campaigns | Table | 0 |
| stg_marketing__google_ads_campaigns | Table | 0 |
| stg_marketing__google_analytics_sessions | Table | 0 |
| stg_marketing__iterable_campaigns | Table | 0 |
| stg_marketing__linkedin_ads_campaigns | Table | 0 |
| stg_marketing__marketing_qualified_leads | Table | 0 |
| stg_stripe__charges | View | 0 |
| stg_stripe__customers | View | 0 |
| stg_stripe__events | View | 0 |
| stg_stripe__invoices | View | 0 |
| stg_stripe__payment_intents | View | 0 |
| stg_stripe__prices | View | 0 |
| stg_stripe__subscription_items | View | 0 |
| stg_stripe__subscriptions | View | 0 |

### INTERMEDIATE Schema

| Table/View | Type | Row Count |
|------------|------|----------:|
| fct_customer_history | Table | 518,607 |
| fct_device_history | Table | 17,910,725 |
| fct_subscription_history | Table | 0 |
| int_campaigns__attribution | Table | 0 |
| int_campaigns__core | Table | 0 |
| int_customers__core | Table | 1,000 |
| int_devices__performance_health | Table | 210,297 |
| int_features__adoption_patterns | Table | 0 |
| int_features__core | Table | 0 |
| int_locations__core | Table | 6,066 |
| int_locations__operational_metrics | Table | 6,066 |
| int_subscriptions__core | Table | 0 |
| int_subscriptions__revenue_metrics | Table | 0 |
| int_users__core | Table | 14,459 |
| int_users__engagement_metrics | Table | 14,459 |

### METRICS Schema

| Table/View | Type | Row Count |
|------------|------|----------:|
| metrics_api | View | 1 |
| metrics_company_overview | View | 9 |
| metrics_customer_historical | Table | 31 |
| metrics_customer_success | View | 1 |
| metrics_engagement | View | 1 |
| metrics_marketing | View | 1 |
| metrics_operations | View | 1 |
| metrics_operations_daily | Table | 1,811 |
| metrics_operations_summary | View | 1 |
| metrics_product_analytics | View | 1 |
| metrics_revenue | View | 1,000 |
| metrics_revenue_daily | Table | 1,823 |
| metrics_revenue_historical | Table | 0 |
| metrics_revenue_summary | View | 1 |
| metrics_sales | View | 1 |
| metrics_unified | Table | 1 |

## Metrics Schema Insights

### Summary Views (Aggregated KPIs)
- **metrics_operations_summary**: 1 rows ✓ (Single-row KPI summary)
- **metrics_revenue_summary**: 1 rows ✓ (Single-row KPI summary)

### Historical Views (Time Series)
- **metrics_customer_historical**: 31 rows
- **metrics_revenue_historical**: 0 rows

