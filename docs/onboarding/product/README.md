# Product Analytics Guide

Welcome to the Product Analytics guide for the SaaS Analytics Platform. This guide will help you understand user behavior, track feature adoption, measure product-market fit, and drive data-informed product decisions.

## 🎯 Overview

As a Product Analyst, you have access to comprehensive product usage metrics across the entire user journey. Our platform provides insights into:

- User behavior and engagement patterns
- Feature adoption and retention
- Product usage trends
- Device performance and reliability
- User segmentation and cohorts
- Product-market fit indicators

## 📊 Key Tables & Metrics

### Primary Product Tables

1. **`metrics.product_analytics`** - Your main analytics table
   - User engagement metrics (DAU/WAU/MAU)
   - Platform usage patterns
   - Session analytics
   - Stickiness ratios
   - Updated daily

2. **`entity.entity_users`** - User-level analytics
   - Individual user profiles
   - Engagement scores
   - Feature usage tracking
   - Activity history

3. **`entity.entity_features`** - Feature performance
   - Feature adoption rates
   - Usage intensity metrics
   - Retention impact scores
   - Time to adoption

4. **`entity.entity_devices`** - IoT device analytics
   - Device health metrics
   - Usage volume data
   - Performance indicators
   - Maintenance patterns

### Essential Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `daily_active_users` | DAU count | Engagement tracking |
| `weekly_active_users` | WAU count | Weekly patterns |
| `monthly_active_users` | MAU count | Overall reach |
| `dau_mau_ratio` | DAU/MAU stickiness | Product stickiness |
| `avg_session_duration` | Session length | Engagement depth |
| `feature_adoption_rate` | % using feature | Feature success |
| `user_retention_d7` | 7-day retention | Early retention |
| `power_user_percentage` | % power users | Core user base |
| `device_uptime_percentage` | Device reliability | Product quality |
| `time_to_first_key_action` | Activation speed | Onboarding success |

## 🚀 Common Reports & Queries

### 1. Product Engagement Dashboard
```sql
-- Core product metrics overview
WITH engagement_metrics AS (
    SELECT 
        date,
        daily_active_users as dau,
        weekly_active_users as wau,
        monthly_active_users as mau,
        dau_mau_ratio,
        wau_mau_ratio,
        avg_session_duration_minutes,
        avg_sessions_per_user,
        total_sessions,
        unique_users,
        new_users,
        returning_users
    FROM metrics.product_analytics
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    date,
    dau,
    wau,
    mau,
    ROUND(dau_mau_ratio * 100, 1) as dau_mau_stickiness,
    ROUND(wau_mau_ratio * 100, 1) as wau_mau_stickiness,
    ROUND(avg_session_duration_minutes, 1) as avg_session_mins,
    ROUND(avg_sessions_per_user, 2) as sessions_per_user,
    new_users,
    returning_users,
    ROUND(100.0 * returning_users / NULLIF(dau, 0), 1) as returning_user_rate
FROM engagement_metrics
ORDER BY date DESC;
```

### 2. Feature Adoption Analysis
```sql
-- Feature adoption funnel and performance
WITH feature_metrics AS (
    SELECT 
        f.feature_name,
        f.feature_category,
        COUNT(DISTINCT f.customer_id) as customers_with_access,
        COUNT(DISTINCT CASE WHEN f.adoption_rate > 0 THEN f.customer_id END) as customers_using,
        AVG(f.adoption_rate) as avg_adoption_rate,
        AVG(f.usage_intensity_score) as avg_intensity,
        AVG(f.retention_impact_score) as avg_retention_impact,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.time_to_first_use_days) as median_time_to_adopt,
        COUNT(DISTINCT CASE WHEN f.usage_frequency = 'Daily' THEN f.customer_id END) as daily_users
    FROM entity.entity_features f
    WHERE f.is_active = true
    GROUP BY f.feature_name, f.feature_category
)
SELECT 
    feature_name,
    feature_category,
    customers_with_access,
    customers_using,
    ROUND(100.0 * customers_using / NULLIF(customers_with_access, 0), 1) as adoption_rate_pct,
    ROUND(avg_adoption_rate * 100, 1) as avg_user_adoption_pct,
    ROUND(avg_intensity, 1) as usage_intensity,
    ROUND(avg_retention_impact, 1) as retention_impact,
    ROUND(median_time_to_adopt, 1) as median_days_to_adopt,
    ROUND(100.0 * daily_users / NULLIF(customers_using, 0), 1) as daily_usage_rate
FROM feature_metrics
WHERE customers_with_access > 10
ORDER BY adoption_rate_pct DESC;
```

### 3. User Cohort Retention
```sql
-- Cohort retention analysis
WITH user_cohorts AS (
    SELECT 
        DATE_TRUNC('week', u.created_at) as cohort_week,
        u.user_id,
        u.customer_id
    FROM entity.entity_users u
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 weeks'
),
cohort_activity AS (
    SELECT 
        uc.cohort_week,
        EXTRACT(WEEK FROM AGE(DATE_TRUNC('week', s.session_date), uc.cohort_week)) as weeks_since_signup,
        COUNT(DISTINCT uc.user_id) as cohort_size,
        COUNT(DISTINCT s.user_id) as active_users
    FROM user_cohorts uc
    LEFT JOIN user_sessions s 
        ON uc.user_id = s.user_id
        AND s.session_date >= uc.cohort_week
    GROUP BY uc.cohort_week, weeks_since_signup
)
SELECT 
    cohort_week,
    MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END) as cohort_size,
    MAX(CASE WHEN weeks_since_signup = 0 THEN 100.0 END) as week_0,
    ROUND(100.0 * MAX(CASE WHEN weeks_since_signup = 1 THEN active_users END) / 
          NULLIF(MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END), 0), 1) as week_1,
    ROUND(100.0 * MAX(CASE WHEN weeks_since_signup = 2 THEN active_users END) / 
          NULLIF(MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END), 0), 1) as week_2,
    ROUND(100.0 * MAX(CASE WHEN weeks_since_signup = 4 THEN active_users END) / 
          NULLIF(MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END), 0), 1) as week_4,
    ROUND(100.0 * MAX(CASE WHEN weeks_since_signup = 8 THEN active_users END) / 
          NULLIF(MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END), 0), 1) as week_8,
    ROUND(100.0 * MAX(CASE WHEN weeks_since_signup = 12 THEN active_users END) / 
          NULLIF(MAX(CASE WHEN weeks_since_signup = 0 THEN cohort_size END), 0), 1) as week_12
FROM cohort_activity
GROUP BY cohort_week
ORDER BY cohort_week DESC;
```

### 4. User Segmentation Analysis
```sql
-- Segment users by behavior patterns
WITH user_segments AS (
    SELECT 
        u.user_id,
        u.customer_id,
        u.engagement_score,
        u.total_sessions_30d,
        u.features_used_30d,
        u.days_since_last_login,
        u.user_engagement_tier,
        CASE 
            WHEN u.total_sessions_30d >= 20 AND u.features_used_30d >= 5 THEN 'Power User'
            WHEN u.total_sessions_30d >= 10 AND u.features_used_30d >= 3 THEN 'Regular User'
            WHEN u.total_sessions_30d >= 1 THEN 'Casual User'
            WHEN u.days_since_last_login <= 30 THEN 'Dormant'
            ELSE 'Churned'
        END as user_segment,
        c.customer_tier,
        c.monthly_recurring_revenue
    FROM entity.entity_users u
    JOIN entity.entity_customers c ON u.customer_id = c.customer_id
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '180 days'
)
SELECT 
    user_segment,
    COUNT(DISTINCT user_id) as user_count,
    COUNT(DISTINCT customer_id) as customer_count,
    ROUND(AVG(engagement_score), 1) as avg_engagement_score,
    ROUND(AVG(total_sessions_30d), 1) as avg_sessions_30d,
    ROUND(AVG(features_used_30d), 1) as avg_features_used,
    ROUND(AVG(days_since_last_login), 1) as avg_days_since_login,
    SUM(monthly_recurring_revenue) as total_mrr,
    ROUND(100.0 * COUNT(DISTINCT user_id) / SUM(COUNT(DISTINCT user_id)) OVER (), 1) as pct_of_users
FROM user_segments
GROUP BY user_segment
ORDER BY 
    CASE user_segment
        WHEN 'Power User' THEN 1
        WHEN 'Regular User' THEN 2
        WHEN 'Casual User' THEN 3
        WHEN 'Dormant' THEN 4
        WHEN 'Churned' THEN 5
    END;
```

### 5. Device Performance Analytics
```sql
-- IoT device health and usage patterns
WITH device_metrics AS (
    SELECT 
        d.device_id,
        d.device_type,
        d.location_id,
        d.overall_health_score,
        d.uptime_percentage_30d,
        d.total_volume_liters_30d,
        d.maintenance_score,
        d.last_maintenance_days_ago,
        d.estimated_revenue_30d,
        l.location_name,
        c.company_name,
        c.customer_tier
    FROM entity.entity_devices d
    JOIN entity.entity_locations l ON d.location_id = l.location_id
    JOIN entity.entity_customers c ON d.customer_id = c.customer_id
    WHERE d.is_active = true
)
SELECT 
    device_type,
    COUNT(DISTINCT device_id) as device_count,
    COUNT(DISTINCT location_id) as location_count,
    ROUND(AVG(overall_health_score), 1) as avg_health_score,
    ROUND(AVG(uptime_percentage_30d), 1) as avg_uptime_pct,
    ROUND(AVG(total_volume_liters_30d), 0) as avg_volume_liters,
    ROUND(AVG(maintenance_score), 1) as avg_maintenance_score,
    COUNT(CASE WHEN last_maintenance_days_ago > 90 THEN 1 END) as devices_needing_maintenance,
    ROUND(SUM(estimated_revenue_30d), 0) as total_estimated_revenue,
    ROUND(AVG(estimated_revenue_30d), 0) as avg_revenue_per_device
FROM device_metrics
GROUP BY device_type
ORDER BY device_count DESC;
```

## 📈 Advanced Analytics

### Product-Market Fit Analysis
```sql
-- Measure product-market fit indicators
WITH pmf_metrics AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        -- Growth metrics
        new_users,
        churned_users,
        new_users - churned_users as net_user_growth,
        -- Engagement metrics
        AVG(dau_mau_ratio) as avg_stickiness,
        AVG(avg_session_duration_minutes) as avg_session_duration,
        -- Retention metrics
        AVG(user_retention_d7) as avg_d7_retention,
        AVG(user_retention_d30) as avg_d30_retention,
        -- Usage depth
        AVG(features_adopted_per_user) as avg_features_adopted,
        AVG(power_user_percentage) as avg_power_user_pct
    FROM metrics.product_analytics
    WHERE date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', date)
)
SELECT 
    month,
    net_user_growth,
    ROUND(100.0 * net_user_growth / NULLIF(LAG(net_user_growth) OVER (ORDER BY month), 0), 1) as growth_rate,
    ROUND(avg_stickiness * 100, 1) as stickiness_pct,
    ROUND(avg_session_duration, 1) as avg_session_mins,
    ROUND(avg_d7_retention * 100, 1) as d7_retention_pct,
    ROUND(avg_d30_retention * 100, 1) as d30_retention_pct,
    ROUND(avg_features_adopted, 1) as features_per_user,
    ROUND(avg_power_user_pct * 100, 1) as power_user_pct,
    -- PMF Score (composite of key indicators)
    ROUND(
        (CASE WHEN net_user_growth > 0 THEN 20 ELSE 0 END) +
        (CASE WHEN avg_stickiness > 0.2 THEN 20 ELSE avg_stickiness * 100 END) +
        (CASE WHEN avg_d30_retention > 0.4 THEN 20 ELSE avg_d30_retention * 50 END) +
        (CASE WHEN avg_features_adopted > 3 THEN 20 ELSE avg_features_adopted * 6.67 END) +
        (CASE WHEN avg_power_user_pct > 0.15 THEN 20 ELSE avg_power_user_pct * 133.33 END)
    , 1) as pmf_score
FROM pmf_metrics
ORDER BY month DESC;
```

### User Journey Analysis
```sql
-- Analyze user paths to key actions
WITH user_journeys AS (
    SELECT 
        u.user_id,
        u.created_at as signup_date,
        MIN(CASE WHEN e.event_name = 'first_device_added' THEN e.event_time END) as first_device_added,
        MIN(CASE WHEN e.event_name = 'first_pour' THEN e.event_time END) as first_pour,
        MIN(CASE WHEN e.event_name = 'invite_sent' THEN e.event_time END) as first_invite,
        MIN(CASE WHEN e.event_name = 'report_viewed' THEN e.event_time END) as first_report,
        COUNT(DISTINCT e.event_date) as active_days,
        COUNT(DISTINCT e.event_name) as unique_events
    FROM entity.entity_users u
    LEFT JOIN user_events e ON u.user_id = e.user_id
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY u.user_id, u.created_at
)
SELECT 
    COUNT(DISTINCT user_id) as total_users,
    -- Conversion rates to key actions
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN first_device_added IS NOT NULL THEN user_id END) / 
          COUNT(DISTINCT user_id), 1) as pct_added_device,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN first_pour IS NOT NULL THEN user_id END) / 
          COUNT(DISTINCT user_id), 1) as pct_first_pour,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN first_invite IS NOT NULL THEN user_id END) / 
          COUNT(DISTINCT user_id), 1) as pct_invited_others,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN first_report IS NOT NULL THEN user_id END) / 
          COUNT(DISTINCT user_id), 1) as pct_viewed_report,
    -- Time to key actions
    ROUND(AVG(EXTRACT(EPOCH FROM (first_device_added - signup_date))/3600), 1) as avg_hours_to_device,
    ROUND(AVG(EXTRACT(EPOCH FROM (first_pour - signup_date))/86400), 1) as avg_days_to_pour,
    ROUND(AVG(EXTRACT(EPOCH FROM (first_invite - signup_date))/86400), 1) as avg_days_to_invite,
    ROUND(AVG(EXTRACT(EPOCH FROM (first_report - signup_date))/86400), 1) as avg_days_to_report,
    -- Engagement depth
    ROUND(AVG(active_days), 1) as avg_active_days,
    ROUND(AVG(unique_events), 1) as avg_unique_actions
FROM user_journeys;
```

### Feature Impact Analysis
```sql
-- Measure feature impact on retention and revenue
WITH feature_impact AS (
    SELECT 
        f.feature_name,
        f.feature_category,
        -- Users
        COUNT(DISTINCT CASE WHEN f.is_feature_user THEN u.user_id END) as feature_users,
        COUNT(DISTINCT u.user_id) as total_users,
        -- Retention
        AVG(CASE WHEN f.is_feature_user THEN u.retention_30d ELSE NULL END) as feature_user_retention,
        AVG(CASE WHEN NOT f.is_feature_user THEN u.retention_30d ELSE NULL END) as non_feature_retention,
        -- Revenue
        SUM(CASE WHEN f.is_feature_user THEN c.monthly_recurring_revenue ELSE 0 END) as feature_user_mrr,
        SUM(CASE WHEN NOT f.is_feature_user THEN c.monthly_recurring_revenue ELSE 0 END) as non_feature_mrr,
        -- Engagement
        AVG(CASE WHEN f.is_feature_user THEN u.engagement_score ELSE NULL END) as feature_user_engagement,
        AVG(CASE WHEN NOT f.is_feature_user THEN u.engagement_score ELSE NULL END) as non_feature_engagement
    FROM entity.entity_features f
    JOIN entity.entity_users u ON f.user_id = u.user_id
    JOIN entity.entity_customers c ON u.customer_id = c.customer_id
    WHERE u.created_at <= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY f.feature_name, f.feature_category
)
SELECT 
    feature_name,
    feature_category,
    feature_users,
    ROUND(100.0 * feature_users / total_users, 1) as adoption_rate,
    ROUND(feature_user_retention * 100, 1) as feature_user_retention_pct,
    ROUND(non_feature_retention * 100, 1) as non_feature_retention_pct,
    ROUND((feature_user_retention - non_feature_retention) * 100, 1) as retention_lift,
    ROUND(feature_user_mrr / NULLIF(feature_users, 0), 0) as mrr_per_feature_user,
    ROUND(non_feature_mrr / NULLIF(total_users - feature_users, 0), 0) as mrr_per_non_user,
    ROUND(feature_user_engagement, 1) as feature_user_engagement_score,
    ROUND(non_feature_engagement, 1) as non_feature_engagement_score
FROM feature_impact
WHERE feature_users > 100
ORDER BY retention_lift DESC;
```

## 🎯 Best Practices

### 1. **Engagement Metrics Hierarchy**
- **Primary**: DAU, WAU, MAU, Stickiness
- **Secondary**: Session duration, frequency
- **Tertiary**: Feature adoption, depth of use
- **Leading indicators**: Time to value, activation rate

### 2. **Cohort Analysis Standards**
- Always use consistent time windows
- Compare like-for-like cohorts
- Account for seasonality
- Track both retention and resurrection

### 3. **Feature Success Criteria**
Define success metrics before launch:
- Target adoption rate
- Expected retention impact
- Usage frequency goals
- Revenue contribution

### 4. **User Segmentation Strategy**
Segment by:
- Engagement level (power/regular/casual)
- Lifecycle stage (new/active/at-risk)
- Use case/persona
- Customer tier

## 🔗 Integration Points

### Product Data Sources
- **User Sessions** → Engagement tracking
- **Feature Usage** → Adoption metrics
- **Page Views** → User journey mapping
- **Tap Events** → Device interaction data

### Engineering Systems
- **Application logs** → Error tracking
- **Performance monitoring** → Load times
- **A/B test results** → Feature validation

### Business Intelligence
- **Customer data** → Segmentation
- **Revenue data** → Impact analysis
- **Support tickets** → Quality metrics

## 📚 Additional Resources

- [Metrics Catalog](../common/metrics-catalog.md) - All available metrics
- [Query Patterns](../common/query-patterns.md) - SQL templates
- [Feature Launch Guide](./feature-launch-guide.md) - Launch process
- [A/B Testing Framework](./ab-testing-framework.md) - Experimentation guide
- [Quarterly Goals](./quarterly-goals.md) - 2025 SMART goals and roadmap

## 🚦 Getting Started Checklist

- [ ] Explore product_analytics metrics
- [ ] Run DAU/MAU query
- [ ] Analyze a recent feature launch
- [ ] Create user segment analysis
- [ ] Join #product-analytics Slack
- [ ] Schedule 1:1 with Product team

Welcome to Product Analytics! 🚀