# Metrics Layer Guide

## Overview

The metrics layer provides pre-calculated business metrics organized by domain, ready for BI tool consumption. This abstraction layer eliminates the need for complex joins and business logic in dashboards.

## Architecture

```
Domain-Specific Metrics
├── metrics_customer_success   → CS team metrics
├── metrics_sales             → Sales performance
├── metrics_product_analytics → Product usage
└── metrics_marketing         → Marketing ROI

Unified Views
├── metrics_unified_domains   → All domains combined
├── metrics_api              → Time comparisons & growth
└── metrics_company_overview → Executive KPIs
```

## Domain Metrics

### 1. Customer Success (`metrics_customer_success`)

**Key Metrics:**
- **Health & Risk**: `customer_health_score`, `churn_risk_score`, `composite_success_score`
- **Engagement**: `monthly_active_users`, `user_activation_rate`, `avg_engagement_score`
- **Adoption**: `features_adopted`, `core_feature_adoption_rate`
- **Support**: `support_tickets_30d`, `ticket_resolution_rate`, `avg_ticket_resolution_hours`
- **Operations**: `active_device_count`, `avg_device_health_score`, `volume_processed_30d`

**Use Cases:**
- Customer health dashboards
- Churn prediction and prevention
- QBR preparation
- Support team performance

### 2. Sales (`metrics_sales`)

**Key Metrics:**
- **Pipeline**: `total_pipeline_value`, `open_opportunities`, `pipeline_coverage_ratio`
- **Performance**: `deals_won_mtd`, `revenue_closed_mtd`, `win_rate`
- **Efficiency**: `avg_deal_size`, `avg_sales_cycle_days`
- **Activity**: `calls_made_30d`, `emails_sent_30d`, `meetings_held_30d`
- **Leads**: `total_mqls`, `mql_conversion_rate`

**Use Cases:**
- Sales rep scorecards
- Pipeline reviews
- Forecasting
- Activity tracking

### 3. Product Analytics (`metrics_product_analytics`)

**Key Metrics:**
- **Usage**: `daily_active_users`, `weekly_active_users`, `monthly_active_users`
- **Stickiness**: `dau_mau_ratio`, `wau_mau_ratio`
- **Engagement**: `avg_session_duration`, `sessions_per_user`, `avg_features_used_per_user`
- **Segments**: `power_users`, `power_user_percentage`
- **Platform**: `desktop_usage_pct`, `mobile_usage_pct`
- **Retention**: `avg_30d_retention_rate`

**Use Cases:**
- Product health monitoring
- Feature adoption tracking
- User behavior analysis
- Platform usage insights

### 4. Marketing (`metrics_marketing`)

**Key Metrics:**
- **Spend**: `total_ad_spend_active`, platform-specific spend
- **ROI**: `overall_roi`, platform-specific ROI
- **Leads**: `total_mqls`, `lead_conversion_rate`, `cost_per_mql`
- **Attribution**: `avg_touchpoints_to_conversion`, top channels by attribution
- **Website**: `website_sessions`, `bounce_rate`, `website_conversion_rate`
- **Efficiency**: `customer_acquisition_cost`

**Use Cases:**
- Campaign performance dashboards
- Channel optimization
- Budget allocation
- Lead quality analysis

## Using the Metrics Layer

### 1. Basic Query (Single Metric)
```sql
SELECT 
    metric_date,
    customer_name,
    customer_health_score
FROM metrics_customer_success
WHERE metric_date = CURRENT_DATE
ORDER BY customer_health_score ASC
LIMIT 10;
```

### 2. Domain Overview
```sql
SELECT 
    domain,
    metric_name,
    AVG(metric_value) as avg_value,
    COUNT(DISTINCT entity_id) as entity_count
FROM metrics_unified_domains
WHERE metric_date = CURRENT_DATE
  AND importance_tier = 'tier_1'
GROUP BY domain, metric_name
ORDER BY domain, avg_value DESC;
```

### 3. Time Series Analysis
```sql
SELECT 
    metric_date,
    SUM(CASE WHEN metric_name = 'daily_active_users' THEN metric_value END) as dau,
    SUM(CASE WHEN metric_name = 'monthly_active_users' THEN metric_value END) as mau,
    SUM(CASE WHEN metric_name = 'dau_mau_ratio' THEN metric_value END) as stickiness
FROM metrics_unified_domains
WHERE domain = 'product'
  AND metric_date >= CURRENT_DATE - 30
GROUP BY metric_date
ORDER BY metric_date;
```

### 4. Cross-Domain Analysis
```sql
WITH metrics AS (
    SELECT 
        entity_id as customer_id,
        MAX(CASE WHEN metric_name = 'customer_health_score' THEN metric_value END) as health_score,
        MAX(CASE WHEN metric_name = 'monthly_active_users' THEN metric_value END) as mau,
        MAX(CASE WHEN metric_name = 'current_mrr' THEN metric_value END) as mrr
    FROM metrics_unified_domains
    WHERE domain = 'customer_success'
      AND metric_date = CURRENT_DATE
    GROUP BY entity_id
)
SELECT 
    CASE 
        WHEN health_score >= 80 THEN 'Healthy'
        WHEN health_score >= 60 THEN 'Stable'
        ELSE 'At Risk'
    END as health_category,
    COUNT(*) as customer_count,
    SUM(mrr) as total_mrr,
    AVG(mau) as avg_mau
FROM metrics
GROUP BY health_category;
```

## Superset Integration

### 1. Add Data Sources
```sql
-- Add these as datasets in Superset:
- entity.metrics_customer_success
- entity.metrics_sales  
- entity.metrics_product_analytics
- entity.metrics_marketing
- entity.metrics_unified_domains
```

### 2. Create Calculated Fields
- **MRR Growth**: `(current_mrr - previous_month_mrr) / previous_month_mrr * 100`
- **Health Trend**: `customer_health_score - LAG(customer_health_score) OVER (ORDER BY metric_date)`
- **Pipeline Velocity**: `pipeline_value / avg_sales_cycle_days`

### 3. Dashboard Templates

#### Executive Dashboard
- Big Number: Total MRR, Active Customers, Overall Health Score
- Line Chart: MRR trend, DAU/MAU trend
- Heat Map: Customer health by segment
- Gauge: Pipeline coverage, Win rate

#### CS Dashboard
- Table: At-risk customers (sorted by MRR at risk)
- Bar Chart: Health score distribution
- Line Chart: Support ticket volume and resolution rate
- Scatter Plot: Health score vs engagement score

#### Sales Dashboard
- Funnel: Pipeline by stage
- Bar Chart: Rep performance ranking
- Time Series: Bookings vs quota
- Table: Top deals by value

#### Product Dashboard
- Line Chart: DAU, WAU, MAU trends
- Pie Chart: User segments
- Heat Map: Feature adoption matrix
- Bar Chart: Platform usage distribution

## Metrics Not Yet Implemented

The following metrics have placeholders (`NULL`) and need implementation:

### Customer Success
- `nps_score` - Requires survey integration
- `csat_score` - Requires survey integration  
- `time_to_value_days` - Requires milestone tracking
- `expansion_potential_score` - Requires predictive model

### Sales
- `quota_attainment_pct` - Requires quota data
- `forecast_amount` - Requires forecasting model
- `stalled_deal_count` - Requires stage duration analysis
- `renewal_rate` - Requires subscription tracking

### Product
- `feature_release_adoption_7d` - Requires release tracking
- `error_rate_pct` - Requires error monitoring
- `crash_free_session_rate` - Requires crash tracking
- `ab_test_results` - Requires experiment platform

### Marketing  
- `email_open_rate` - Requires email platform API
- `social_engagement_rate` - Requires social platform APIs
- `brand_awareness_score` - Requires survey data
- `lifetime_value_cac_ratio` - Requires LTV modeling

## Best Practices

1. **Use the unified view** (`metrics_unified_domains`) for cross-domain analysis
2. **Filter by importance_tier** to focus on key metrics
3. **Join with dimension tables** for additional context
4. **Cache frequently used queries** in Superset
5. **Set up alerts** on tier 1 metrics
6. **Document custom metrics** added to dashboards

## Performance Tips

1. The unified table is materialized for fast queries
2. Use date filters to limit data scanned
3. Aggregate at appropriate levels before visualization
4. Consider creating aggregate tables for exec dashboards
5. Monitor query performance and optimize as needed