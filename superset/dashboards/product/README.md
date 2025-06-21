# Product Analytics Dashboard Setup Guide

## Overview
Monitor product usage, feature adoption, user behavior, and engagement metrics to drive product decisions.

## Key Components

### 1. Usage Metrics
- **Daily Active Users (DAU)** - Unique users per day
- **Monthly Active Users (MAU)** - Unique users per month
- **DAU/MAU Ratio** - Stickiness metric
- **Average Session Duration** - User engagement depth

### 2. Feature Adoption
- **Feature Usage Funnel** - Discovery → Trial → Adoption → Retention
- **Adoption by Feature** - Percentage of users using each feature
- **Feature Retention** - Continued usage over time
- **Impact on Engagement** - Correlation with overall usage

### 3. User Journey Analytics
- **Onboarding Funnel** - Sign-up → Activation → First value
- **User Paths** - Most common navigation flows
- **Drop-off Points** - Where users abandon tasks
- **Time to Value** - How quickly users achieve goals

### 4. Device & Platform Analytics
- **Device Performance** - Uptime, errors, response time
- **Platform Distribution** - Web vs Mobile vs API usage
- **Version Adoption** - Users on latest version
- **Performance Metrics** - Load times, error rates

## Key Datasets
- `public.metrics_product_analytics` - Product usage metrics
- `entity.entity_users` - User activity and engagement
- `entity.entity_features` - Feature adoption metrics
- `entity.entity_devices` - Device performance data
- `staging.stg_app_database__page_views` - User behavior data

## Essential Charts

### 1. User Engagement Overview
```sql
SELECT 
    date,
    daily_active_users as dau,
    weekly_active_users as wau,
    monthly_active_users as mau,
    ROUND(daily_active_users::numeric / NULLIF(monthly_active_users, 0) * 100, 1) as stickiness,
    avg_sessions_per_user,
    avg_session_duration_minutes
FROM public.metrics_product_analytics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;
```

### 2. Feature Adoption Matrix
```sql
SELECT 
    feature_name,
    feature_category,
    user_adoption_rate * 100 as user_adoption_pct,
    account_adoption_rate * 100 as account_adoption_pct,
    avg_usage_frequency,
    retention_30d * 100 as retention_rate,
    impact_on_retention
FROM entity.entity_features
WHERE is_active = true
ORDER BY user_adoption_rate DESC;
```

### 3. User Cohort Retention
```sql
WITH cohorts AS (
    SELECT 
        DATE_TRUNC('month', created_at) as cohort_month,
        user_id,
        created_at
    FROM entity.entity_users
)
SELECT 
    cohort_month,
    EXTRACT(MONTH FROM AGE(activity_date, cohort_month)) as months_since_signup,
    COUNT(DISTINCT c.user_id) as active_users,
    COUNT(DISTINCT c.user_id)::numeric / 
        COUNT(DISTINCT CASE WHEN months_since_signup = 0 THEN c.user_id END) * 100 as retention_pct
FROM cohorts c
JOIN user_activity ua ON c.user_id = ua.user_id
GROUP BY cohort_month, months_since_signup
ORDER BY cohort_month DESC, months_since_signup;
```

### 4. Device Performance Metrics
```sql
SELECT 
    device_type,
    deployment_model,
    COUNT(*) as device_count,
    AVG(uptime_percentage) as avg_uptime,
    AVG(response_time_ms) as avg_response_time,
    SUM(error_count_24h) as total_errors,
    AVG(throughput_mbps) as avg_throughput
FROM entity.entity_devices
WHERE device_status = 'active'
GROUP BY device_type, deployment_model
ORDER BY device_count DESC;
```

## Filters to Include
- Date Range selector
- User Segment filter
- Feature Category dropdown
- Device Type selector
- Platform filter (Web/Mobile/API)

## Recommended Layout
```
[DAU KPI] [MAU KPI] [DAU/MAU KPI] [Avg Session KPI]
[----------User Activity Trend Line Chart----------]
[Feature Adoption Table] [Device Performance Gauges]
[----User Flow Sankey----] [--Retention Heatmap--]
```

## Key Insights to Surface
1. **Activation Rate**: % of new users who complete key action
2. **Feature Discovery**: How users find new features
3. **Power Users**: Top 10% most active users behavior
4. **Churn Indicators**: Actions correlating with churn

## Alerts to Configure
1. DAU drop >15% day-over-day
2. Feature adoption <10% after 30 days
3. Device error rate >1%
4. Page load time >3 seconds