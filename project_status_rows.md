# Data Platform Row Counts Report

Generated: 2025-06-24 20:17:34

## Summary by Schema

### STAGING Schema
- Total objects: 30
- Objects with data: 16

### INTERMEDIATE Schema
- Total objects: 15
- Objects with data: 15

### METRICS Schema
- Total objects: 16
- Objects with data: 16


## Detailed Row Counts

### STAGING Schema

| Table/View | Type | Row Count |
|------------|------|----------:|
| stg_app_database__accounts | View | 150 |
| stg_app_database__devices | View | 30,720 |
| stg_app_database__feature_usage | Table | 969,688 |
| stg_app_database__locations | View | 889 |
| stg_app_database__page_views | Table | 513,723 |
| stg_app_database__subscriptions | View | 155 |
| stg_app_database__tap_events | Table | 3,589,891 |
| stg_app_database__user_sessions | Table | 51,075 |
| stg_app_database__users | View | 2,433 |
| stg_hubspot__companies | View | 0 |
| stg_hubspot__contacts | View | 0 |
| stg_hubspot__deals | View | 0 |
| stg_hubspot__engagements | Table | 4,305 |
| stg_hubspot__owners | View | 0 |
| stg_hubspot__tickets | Table | 424 |
| stg_marketing__attribution_touchpoints | View | 0 |
| stg_marketing__facebook_ads_campaigns | Table | 16 |
| stg_marketing__google_ads_campaigns | Table | 18 |
| stg_marketing__google_analytics_sessions | Table | 721 |
| stg_marketing__iterable_campaigns | Table | 102 |
| stg_marketing__linkedin_ads_campaigns | Table | 0 |
| stg_marketing__marketing_qualified_leads | Table | 38,771 |
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
| fct_customer_history | Table | 117,964 |
| fct_device_history | Table | 490,826 |
| fct_subscription_history | Table | 107,593 |
| int_campaigns__attribution | Table | 146 |
| int_campaigns__core | Table | 136 |
| int_customers__core | Table | 1,000 |
| int_devices__performance_health | Table | 22,215 |
| int_features__adoption_patterns | Table | 24 |
| int_features__core | Table | 24 |
| int_locations__core | Table | 155 |
| int_locations__operational_metrics | Table | 155 |
| int_subscriptions__core | Table | 2,312 |
| int_subscriptions__revenue_metrics | Table | 2,312 |
| int_users__core | Table | 3,494 |
| int_users__engagement_metrics | Table | 3,494 |

### METRICS Schema

| Table/View | Type | Row Count |
|------------|------|----------:|
| metrics_api | View | 1 |
| metrics_company_overview | View | 9 |
| metrics_customer_historical | Table | 32 |
| metrics_customer_success | View | 1 |
| metrics_engagement | View | 1 |
| metrics_marketing | View | 1 |
| metrics_operations | View | 1 |
| metrics_operations_daily | Table | 1,825 |
| metrics_operations_summary | View | 1 |
| metrics_product_analytics | View | 1 |
| metrics_revenue | View | 1,000 |
| metrics_revenue_daily | Table | 1,827 |
| metrics_revenue_historical | Table | 24 |
| metrics_revenue_summary | View | 1 |
| metrics_sales | View | 1 |
| metrics_unified | Table | 1 |

## Metrics Schema Insights

### Summary Views (Aggregated KPIs)
- **metrics_operations_summary**: 1 rows ✓ (Single-row KPI summary)
- **metrics_revenue_summary**: 1 rows ✓ (Single-row KPI summary)

### Historical Views (Time Series)
- **metrics_customer_historical**: 32 rows
- **metrics_revenue_historical**: 24 rows

