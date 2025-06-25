# DBT Model Coverage Report

Generated: 2025-06-24

## Summary
- **Total Models**: 81 defined, 48 tables/views created
- **Build Status**: ✅ All models built successfully
- **Test Status**: ⚠️ 30 test failures (column name mismatches)
- **Data Coverage**: 100% of raw tables have staging models

## Model Distribution by Layer

### Raw Data Sources (30 tables)
- ✅ All raw tables populated with data
- ✅ All sources defined in DBT

### Staging Layer (11 tables)
- app_database sources: 9 models
- stripe sources: 6 models  
- hubspot sources: 6 models
- marketing sources: 8 models

### Intermediate Layer (12 tables)
- Customer analytics
- Subscription metrics
- User engagement
- Device performance
- Location operations
- Feature adoption
- Campaign attribution

### Entity Layer (19 tables)
- entity_customers (+ history, daily, weekly)
- entity_users (+ history, weekly)
- entity_devices (+ history, hourly)
- entity_locations (+ history, weekly)
- entity_subscriptions (+ history, monthly)
- entity_features
- entity_campaigns (+ history, daily)

### Mart Layer (5 tables)
- mart_customer_success__health
- mart_marketing__attribution
- mart_operations__performance
- mart_sales__pipeline
- mart_device_operations

### Metrics Layer (11 views)
- metrics_revenue
- metrics_engagement
- metrics_product_analytics
- metrics_customer_success
- metrics_operations
- metrics_marketing
- metrics_sales
- metrics_api
- metrics_unified
- metrics_company_overview

## Key Analytics Capabilities

### Revenue Analytics
- MRR tracking and trends
- Churn analysis
- Customer lifetime value
- Subscription metrics

### Product Analytics
- Feature adoption rates
- User engagement scores
- Device utilization
- Pour volume tracking

### Marketing Analytics
- Multi-touch attribution
- Campaign ROI
- Customer acquisition cost
- Channel effectiveness

### Operations Analytics
- Location performance
- Device health monitoring
- Inventory insights
- Staff utilization

## Test Coverage
- **Total Tests**: 168 defined
- **Test Types**: Uniqueness, not null, relationships, custom business logic
- **Known Issues**: 30 tests failing due to column name evolution

## Recommendations
1. Fix failing tests by updating column references
2. Add data freshness tests for real-time monitoring
3. Implement incremental refresh for large fact tables
4. Add documentation for business users

## Next Steps
- Integration with BI tools (Tableau, Looker, etc.)
- Automated alerting on key metrics
- Performance optimization for large datasets