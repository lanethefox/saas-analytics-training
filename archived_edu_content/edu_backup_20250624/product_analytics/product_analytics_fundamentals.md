# Product Analytics Fundamentals

## Module Overview

This module covers essential product analytics techniques for B2B SaaS companies. You'll learn to measure feature adoption, analyze user behavior, design and interpret A/B tests, and use data to drive product decisions that improve user experience and business outcomes.

## Learning Objectives

By completing this module, you will be able to:
1. Design and implement product metrics frameworks
2. Analyze feature adoption and user engagement patterns
3. Conduct cohort analysis for retention insights
4. Design and analyze A/B tests with statistical rigor
5. Build usage-based pricing models
6. Present product insights to drive roadmap decisions

## 1. Introduction to Product Analytics

### The Role of Product Analytics in B2B SaaS

Product analytics bridges the gap between:
- **User Behavior** → **Product Decisions**
- **Feature Development** → **Business Impact**
- **Usage Data** → **Revenue Growth**
- **Customer Feedback** → **Quantified Insights**

### Key Stakeholders

**Primary Users:**
- Chief Product Officer
- Product Managers
- UX Researchers
- Product Engineers

**Cross-functional Partners:**
- Customer Success (usage insights)
- Sales (feature value props)
- Marketing (product positioning)
- Engineering (performance metrics)

## 2. Product Metrics Framework

### The HEART Framework (Google)

**Happiness**: User satisfaction and sentiment
**Engagement**: Level of user involvement
**Adoption**: New users or features
**Retention**: User continuity over time
**Task Success**: Efficiency and effectiveness

### Core Product Metrics

**Activation Metrics**
```sql
-- User activation funnel
WITH activation_steps AS (
    SELECT 
        u.user_id,
        u.created_at as signup_date,
        MIN(CASE WHEN e.event_name = 'account_connected' THEN e.timestamp END) as first_integration,
        MIN(CASE WHEN e.event_name = 'first_report_created' THEN e.timestamp END) as first_value,
        MIN(CASE WHEN e.event_name = 'team_member_invited' THEN e.timestamp END) as team_expansion,
        MIN(CASE WHEN e.event_name = 'api_key_created' THEN e.timestamp END) as api_setup
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY u.user_id, u.created_at
),
activation_metrics AS (
    SELECT 
        DATE_TRUNC('week', signup_date) as cohort_week,
        COUNT(*) as signups,
        COUNT(first_integration) as integrated,
        COUNT(first_value) as activated,
        COUNT(team_expansion) as expanded,
        COUNT(api_setup) as api_users,
        -- Time to activation
        AVG(EXTRACT(EPOCH FROM (first_value - signup_date))/3600) as avg_hours_to_activation
    FROM activation_steps
    GROUP BY DATE_TRUNC('week', signup_date)
)
SELECT 
    cohort_week,
    signups,
    integrated,
    activated,
    ROUND(integrated * 100.0 / signups, 2) as integration_rate,
    ROUND(activated * 100.0 / signups, 2) as activation_rate,
    ROUND(expanded * 100.0 / activated, 2) as expansion_rate,
    ROUND(avg_hours_to_activation, 2) as avg_hours_to_activation
FROM activation_metrics
ORDER BY cohort_week DESC;
```

**Engagement Metrics**
```sql
-- DAU/MAU/WAU calculation with stickiness
WITH user_activity AS (
    SELECT 
        DATE(timestamp) as activity_date,
        user_id,
        account_id
    FROM events
    WHERE timestamp >= CURRENT_DATE - INTERVAL '35 days'
      AND event_name != 'page_view'  -- Focus on meaningful actions
    GROUP BY DATE(timestamp), user_id, account_id
),
engagement_metrics AS (
    SELECT 
        activity_date,
        -- Daily metrics
        COUNT(DISTINCT user_id) as dau,
        COUNT(DISTINCT account_id) as accounts_active,
        -- Rolling windows
        COUNT(DISTINCT user_id) FILTER (
            WHERE activity_date >= CURRENT_DATE - INTERVAL '7 days'
        ) OVER (ORDER BY activity_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as wau_rolling,
        COUNT(DISTINCT user_id) FILTER (
            WHERE activity_date >= CURRENT_DATE - INTERVAL '30 days'
        ) OVER (ORDER BY activity_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as mau_rolling
    FROM user_activity
    WHERE activity_date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    activity_date,
    dau,
    wau_rolling as wau,
    mau_rolling as mau,
    ROUND(dau * 100.0 / NULLIF(mau_rolling, 0), 2) as daily_stickiness,
    ROUND(wau_rolling * 100.0 / NULLIF(mau_rolling, 0), 2) as weekly_stickiness,
    accounts_active
FROM engagement_metrics
ORDER BY activity_date DESC;
```

## 3. Feature Adoption Analysis

### Feature Adoption Lifecycle

```sql
-- Feature adoption funnel and lifecycle
WITH feature_events AS (
    SELECT 
        f.feature_name,
        f.launch_date,
        e.user_id,
        e.account_id,
        MIN(e.timestamp) as first_use_date,
        COUNT(DISTINCT DATE(e.timestamp)) as days_used,
        COUNT(*) as total_uses,
        MAX(e.timestamp) as last_use_date
    FROM features f
    LEFT JOIN events e ON f.feature_name = e.feature_name
    WHERE f.launch_date <= CURRENT_DATE - INTERVAL '30 days'
      AND e.timestamp >= f.launch_date
    GROUP BY f.feature_name, f.launch_date, e.user_id, e.account_id
),
adoption_metrics AS (
    SELECT 
        feature_name,
        launch_date,
        COUNT(DISTINCT user_id) as users_tried,
        COUNT(DISTINCT CASE WHEN days_used >= 3 THEN user_id END) as users_adopted,
        COUNT(DISTINCT CASE WHEN last_use_date >= CURRENT_DATE - INTERVAL '7 days' THEN user_id END) as users_active_7d,
        COUNT(DISTINCT account_id) as accounts_tried,
        AVG(total_uses) as avg_uses_per_user,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_used) as median_days_used,
        AVG(EXTRACT(EPOCH FROM (first_use_date - launch_date))/86400) as avg_days_to_first_use
    FROM feature_events
    GROUP BY feature_name, launch_date
)
SELECT 
    feature_name,
    launch_date,
    CURRENT_DATE - launch_date::date as days_since_launch,
    users_tried,
    users_adopted,
    ROUND(users_adopted * 100.0 / NULLIF(users_tried, 0), 2) as adoption_rate,
    ROUND(users_active_7d * 100.0 / NULLIF(users_adopted, 0), 2) as retention_rate_7d,
    accounts_tried,
    ROUND(avg_uses_per_user, 2) as avg_uses_per_user,
    ROUND(median_days_used, 1) as median_days_used,
    ROUND(avg_days_to_first_use, 1) as avg_days_to_discovery
FROM adoption_metrics
ORDER BY adoption_rate DESC;
```

### Feature Adoption Cohorts

```sql
-- Cohort analysis for feature adoption
WITH user_cohorts AS (
    SELECT 
        u.user_id,
        DATE_TRUNC('month', u.created_at) as cohort_month,
        f.feature_name,
        MIN(CASE WHEN e.feature_name = f.feature_name THEN DATE(e.timestamp) END) as adoption_date
    FROM users u
    CROSS JOIN features f
    LEFT JOIN events e ON u.user_id = e.user_id AND e.feature_name = f.feature_name
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 months'
      AND f.feature_name IN ('advanced_reporting', 'api_access', 'team_collaboration')
    GROUP BY u.user_id, DATE_TRUNC('month', u.created_at), f.feature_name
),
cohort_adoption AS (
    SELECT 
        cohort_month,
        feature_name,
        COUNT(DISTINCT user_id) as cohort_size,
        COUNT(DISTINCT CASE WHEN adoption_date IS NOT NULL THEN user_id END) as adopted_users,
        COUNT(DISTINCT CASE 
            WHEN adoption_date <= cohort_month + INTERVAL '30 days' THEN user_id 
        END) as adopted_month_1,
        COUNT(DISTINCT CASE 
            WHEN adoption_date <= cohort_month + INTERVAL '60 days' THEN user_id 
        END) as adopted_month_2,
        COUNT(DISTINCT CASE 
            WHEN adoption_date <= cohort_month + INTERVAL '90 days' THEN user_id 
        END) as adopted_month_3
    FROM user_cohorts
    GROUP BY cohort_month, feature_name
)
SELECT 
    cohort_month,
    feature_name,
    cohort_size,
    ROUND(adopted_month_1 * 100.0 / cohort_size, 2) as month_1_adoption,
    ROUND(adopted_month_2 * 100.0 / cohort_size, 2) as month_2_adoption,
    ROUND(adopted_month_3 * 100.0 / cohort_size, 2) as month_3_adoption,
    ROUND(adopted_users * 100.0 / cohort_size, 2) as total_adoption
FROM cohort_adoption
WHERE cohort_size > 10
ORDER BY cohort_month DESC, feature_name;
```

## 4. User Behavior Analysis

### User Segmentation

```sql
-- Behavioral user segmentation
WITH user_behavior AS (
    SELECT 
        u.user_id,
        u.account_id,
        u.created_at,
        COUNT(DISTINCT DATE(e.timestamp)) as active_days,
        COUNT(DISTINCT e.feature_name) as features_used,
        COUNT(e.event_id) as total_events,
        MAX(e.timestamp) as last_active,
        SUM(CASE WHEN e.event_name = 'report_exported' THEN 1 ELSE 0 END) as reports_exported,
        SUM(CASE WHEN e.event_name = 'api_call' THEN 1 ELSE 0 END) as api_calls,
        SUM(CASE WHEN e.event_name = 'team_member_invited' THEN 1 ELSE 0 END) as invites_sent
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY u.user_id, u.account_id, u.created_at
),
user_segments AS (
    SELECT 
        user_id,
        account_id,
        active_days,
        features_used,
        total_events,
        CURRENT_DATE - last_active::date as days_since_active,
        CASE 
            WHEN active_days >= 20 AND features_used >= 5 THEN 'Power User'
            WHEN active_days >= 10 AND features_used >= 3 THEN 'Regular User'
            WHEN active_days >= 5 THEN 'Casual User'
            WHEN active_days > 0 THEN 'Low Engagement'
            ELSE 'Inactive'
        END as user_segment,
        CASE 
            WHEN api_calls > 100 THEN 'API Heavy'
            WHEN reports_exported > 10 THEN 'Report Heavy'
            WHEN invites_sent > 3 THEN 'Collaborative'
            ELSE 'Standard'
        END as usage_pattern
    FROM user_behavior
)
SELECT 
    user_segment,
    usage_pattern,
    COUNT(*) as user_count,
    AVG(active_days) as avg_active_days,
    AVG(features_used) as avg_features,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_events) as median_events,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as pct_of_users
FROM user_segments
GROUP BY user_segment, usage_pattern
ORDER BY user_count DESC;
```

### User Journey Analysis

```sql
-- Common user paths through the product
WITH user_events AS (
    SELECT 
        user_id,
        event_name,
        timestamp,
        LAG(event_name) OVER (PARTITION BY user_id ORDER BY timestamp) as prev_event,
        LEAD(event_name) OVER (PARTITION BY user_id ORDER BY timestamp) as next_event
    FROM events
    WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
      AND event_name IN ('login', 'dashboard_view', 'report_create', 'report_export', 'settings_update', 'logout')
),
event_transitions AS (
    SELECT 
        prev_event || ' → ' || event_name as transition,
        COUNT(*) as transition_count,
        COUNT(DISTINCT user_id) as unique_users
    FROM user_events
    WHERE prev_event IS NOT NULL
    GROUP BY prev_event, event_name
),
common_paths AS (
    SELECT 
        transition,
        transition_count,
        unique_users,
        ROUND(transition_count * 100.0 / SUM(transition_count) OVER (), 2) as pct_of_transitions
    FROM event_transitions
    WHERE transition_count > 10
)
SELECT * FROM common_paths
ORDER BY transition_count DESC
LIMIT 20;
```

## 5. Retention Analysis

### Cohort Retention

```sql
-- Classic cohort retention analysis
WITH user_cohorts AS (
    SELECT 
        u.user_id,
        DATE_TRUNC('month', u.created_at) as cohort_month,
        DATE_TRUNC('month', e.timestamp) as activity_month,
        EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', e.timestamp), DATE_TRUNC('month', u.created_at))) * 12 +
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', e.timestamp), DATE_TRUNC('month', u.created_at))) as months_since_signup
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 months'
      AND e.timestamp >= u.created_at
),
retention_matrix AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT CASE WHEN months_since_signup = 0 THEN user_id END) as month_0,
        COUNT(DISTINCT CASE WHEN months_since_signup = 1 THEN user_id END) as month_1,
        COUNT(DISTINCT CASE WHEN months_since_signup = 2 THEN user_id END) as month_2,
        COUNT(DISTINCT CASE WHEN months_since_signup = 3 THEN user_id END) as month_3,
        COUNT(DISTINCT CASE WHEN months_since_signup = 4 THEN user_id END) as month_4,
        COUNT(DISTINCT CASE WHEN months_since_signup = 5 THEN user_id END) as month_5,
        COUNT(DISTINCT CASE WHEN months_since_signup = 6 THEN user_id END) as month_6
    FROM user_cohorts
    GROUP BY cohort_month
)
SELECT 
    cohort_month,
    month_0 as cohort_size,
    ROUND(month_1 * 100.0 / month_0, 2) as month_1_retention,
    ROUND(month_2 * 100.0 / month_0, 2) as month_2_retention,
    ROUND(month_3 * 100.0 / month_0, 2) as month_3_retention,
    ROUND(month_4 * 100.0 / month_0, 2) as month_4_retention,
    ROUND(month_5 * 100.0 / month_0, 2) as month_5_retention,
    ROUND(month_6 * 100.0 / month_0, 2) as month_6_retention
FROM retention_matrix
WHERE month_0 > 10
ORDER BY cohort_month;
```

### Feature-Based Retention

```sql
-- Impact of feature usage on retention
WITH feature_usage AS (
    SELECT 
        u.user_id,
        u.created_at,
        MAX(CASE WHEN e.feature_name = 'advanced_reporting' THEN 1 ELSE 0 END) as used_reporting,
        MAX(CASE WHEN e.feature_name = 'api_access' THEN 1 ELSE 0 END) as used_api,
        MAX(CASE WHEN e.feature_name = 'team_collaboration' THEN 1 ELSE 0 END) as used_collaboration,
        MAX(CASE WHEN e.timestamp >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END) as retained_30d,
        MAX(CASE WHEN e.timestamp >= CURRENT_DATE - INTERVAL '90 days' THEN 1 ELSE 0 END) as retained_90d
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    WHERE u.created_at <= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY u.user_id, u.created_at
),
retention_by_feature AS (
    SELECT 
        'Used Advanced Reporting' as feature,
        COUNT(CASE WHEN used_reporting = 1 THEN 1 END) as users_with_feature,
        COUNT(CASE WHEN used_reporting = 1 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_reporting = 1 THEN 1 END), 0) as retention_30d_with,
        COUNT(CASE WHEN used_reporting = 0 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_reporting = 0 THEN 1 END), 0) as retention_30d_without
    FROM feature_usage
    
    UNION ALL
    
    SELECT 
        'Used API Access' as feature,
        COUNT(CASE WHEN used_api = 1 THEN 1 END) as users_with_feature,
        COUNT(CASE WHEN used_api = 1 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_api = 1 THEN 1 END), 0) as retention_30d_with,
        COUNT(CASE WHEN used_api = 0 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_api = 0 THEN 1 END), 0) as retention_30d_without
    FROM feature_usage
    
    UNION ALL
    
    SELECT 
        'Used Team Collaboration' as feature,
        COUNT(CASE WHEN used_collaboration = 1 THEN 1 END) as users_with_feature,
        COUNT(CASE WHEN used_collaboration = 1 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_collaboration = 1 THEN 1 END), 0) as retention_30d_with,
        COUNT(CASE WHEN used_collaboration = 0 AND retained_30d = 1 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN used_collaboration = 0 THEN 1 END), 0) as retention_30d_without
    FROM feature_usage
)
SELECT 
    feature,
    users_with_feature,
    ROUND(retention_30d_with, 2) as retention_with_feature,
    ROUND(retention_30d_without, 2) as retention_without_feature,
    ROUND(retention_30d_with - retention_30d_without, 2) as retention_lift
FROM retention_by_feature
ORDER BY retention_lift DESC;
```

## 6. A/B Testing and Experimentation

### Experiment Design Framework

```sql
-- A/B test setup and monitoring
WITH experiment_assignment AS (
    SELECT 
        user_id,
        experiment_id,
        variant,
        assignment_date,
        -- Stratification variables for balance check
        user_segment,
        account_size,
        days_since_signup
    FROM experiments
    WHERE experiment_id = 'new_onboarding_flow_v2'
),
balance_check AS (
    SELECT 
        variant,
        COUNT(*) as users,
        AVG(days_since_signup) as avg_tenure,
        COUNT(CASE WHEN user_segment = 'Power User' THEN 1 END) * 100.0 / COUNT(*) as pct_power_users,
        COUNT(CASE WHEN account_size = 'Enterprise' THEN 1 END) * 100.0 / COUNT(*) as pct_enterprise
    FROM experiment_assignment
    GROUP BY variant
)
SELECT * FROM balance_check;
```

### Experiment Analysis

```sql
-- Comprehensive A/B test analysis
WITH experiment_data AS (
    SELECT 
        e.user_id,
        e.variant,
        e.assignment_date,
        -- Primary metric: 7-day activation
        MAX(CASE WHEN ev.event_name = 'activation_complete' 
            AND ev.timestamp <= e.assignment_date + INTERVAL '7 days' 
            THEN 1 ELSE 0 END) as activated_7d,
        -- Secondary metrics
        COUNT(DISTINCT CASE WHEN ev.timestamp <= e.assignment_date + INTERVAL '7 days' 
            THEN DATE(ev.timestamp) END) as active_days_7d,
        COUNT(DISTINCT ev.feature_name) FILTER (
            WHERE ev.timestamp <= e.assignment_date + INTERVAL '7 days'
        ) as features_tried_7d,
        -- Guardrail metrics
        MIN(ev.timestamp) FILTER (WHERE ev.event_name = 'error_occurred') as first_error_time
    FROM experiments e
    LEFT JOIN events ev ON e.user_id = ev.user_id 
        AND ev.timestamp >= e.assignment_date
        AND ev.timestamp <= e.assignment_date + INTERVAL '30 days'
    WHERE e.experiment_id = 'new_onboarding_flow_v2'
    GROUP BY e.user_id, e.variant, e.assignment_date
),
results_summary AS (
    SELECT 
        variant,
        COUNT(*) as sample_size,
        -- Primary metric
        AVG(activated_7d) as activation_rate,
        STDDEV(activated_7d) as activation_stddev,
        -- Secondary metrics  
        AVG(active_days_7d) as avg_active_days,
        AVG(features_tried_7d) as avg_features_tried,
        -- Guardrail
        COUNT(first_error_time) * 100.0 / COUNT(*) as error_rate
    FROM experiment_data
    GROUP BY variant
),
statistical_test AS (
    SELECT 
        'Control' as control_variant,
        'Treatment' as treatment_variant,
        -- Get metrics for each variant
        MAX(CASE WHEN variant = 'Control' THEN activation_rate END) as control_rate,
        MAX(CASE WHEN variant = 'Treatment' THEN activation_rate END) as treatment_rate,
        MAX(CASE WHEN variant = 'Control' THEN sample_size END) as control_n,
        MAX(CASE WHEN variant = 'Treatment' THEN sample_size END) as treatment_n,
        -- Calculate lift
        (MAX(CASE WHEN variant = 'Treatment' THEN activation_rate END) - 
         MAX(CASE WHEN variant = 'Control' THEN activation_rate END)) / 
         MAX(CASE WHEN variant = 'Control' THEN activation_rate END) * 100 as relative_lift,
        -- Pooled standard error for two-sample proportion test
        SQRT(
            (MAX(CASE WHEN variant = 'Control' THEN activation_rate * (1 - activation_rate) / sample_size END) +
             MAX(CASE WHEN variant = 'Treatment' THEN activation_rate * (1 - activation_rate) / sample_size END))
        ) as standard_error
    FROM results_summary
)
SELECT 
    control_variant,
    treatment_variant,
    ROUND(control_rate * 100, 2) as control_activation_pct,
    ROUND(treatment_rate * 100, 2) as treatment_activation_pct,
    ROUND(relative_lift, 2) as lift_pct,
    control_n,
    treatment_n,
    -- Z-score
    (treatment_rate - control_rate) / standard_error as z_score,
    -- 95% confidence interval for the difference
    ROUND((treatment_rate - control_rate - 1.96 * standard_error) * 100, 2) as ci_lower,
    ROUND((treatment_rate - control_rate + 1.96 * standard_error) * 100, 2) as ci_upper,
    -- Statistical significance
    CASE 
        WHEN ABS((treatment_rate - control_rate) / standard_error) > 1.96 THEN 'Significant'
        ELSE 'Not Significant'
    END as statistical_significance
FROM statistical_test;
```

### Sequential Testing and Early Stopping

```sql
-- Monitor experiment with sequential testing
WITH daily_results AS (
    SELECT 
        DATE(e.assignment_date) as experiment_day,
        e.variant,
        COUNT(*) as daily_users,
        SUM(activated_7d) as daily_conversions,
        AVG(activated_7d) as daily_conversion_rate
    FROM experiments e
    JOIN (
        SELECT 
            user_id,
            MAX(CASE WHEN event_name = 'activation_complete' THEN 1 ELSE 0 END) as activated_7d
        FROM events
        WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY user_id
    ) a ON e.user_id = a.user_id
    WHERE e.experiment_id = 'new_onboarding_flow_v2'
    GROUP BY DATE(e.assignment_date), e.variant
),
cumulative_results AS (
    SELECT 
        experiment_day,
        variant,
        SUM(daily_users) OVER (PARTITION BY variant ORDER BY experiment_day) as cumulative_users,
        SUM(daily_conversions) OVER (PARTITION BY variant ORDER BY experiment_day) as cumulative_conversions,
        SUM(daily_conversions) OVER (PARTITION BY variant ORDER BY experiment_day) * 1.0 / 
            SUM(daily_users) OVER (PARTITION BY variant ORDER BY experiment_day) as cumulative_rate
    FROM daily_results
)
SELECT 
    c.experiment_day,
    MAX(CASE WHEN variant = 'Control' THEN cumulative_users END) as control_n,
    MAX(CASE WHEN variant = 'Treatment' THEN cumulative_users END) as treatment_n,
    ROUND(MAX(CASE WHEN variant = 'Control' THEN cumulative_rate END) * 100, 2) as control_rate,
    ROUND(MAX(CASE WHEN variant = 'Treatment' THEN cumulative_rate END) * 100, 2) as treatment_rate,
    ROUND((MAX(CASE WHEN variant = 'Treatment' THEN cumulative_rate END) - 
           MAX(CASE WHEN variant = 'Control' THEN cumulative_rate END)) * 100, 2) as absolute_diff,
    -- Sequential probability ratio test boundary
    CASE 
        WHEN MAX(CASE WHEN variant = 'Treatment' THEN cumulative_conversions END) - 
             MAX(CASE WHEN variant = 'Control' THEN cumulative_conversions END) > 
             2.9 * SQRT(MAX(CASE WHEN variant = 'Control' THEN cumulative_users END)) THEN 'Stop - Treatment Wins'
        WHEN MAX(CASE WHEN variant = 'Control' THEN cumulative_conversions END) - 
             MAX(CASE WHEN variant = 'Treatment' THEN cumulative_conversions END) > 
             2.9 * SQRT(MAX(CASE WHEN variant = 'Treatment' THEN cumulative_users END)) THEN 'Stop - Control Wins'
        ELSE 'Continue'
    END as recommendation
FROM cumulative_results c
GROUP BY c.experiment_day
ORDER BY c.experiment_day;
```

## 7. Usage-Based Pricing Analysis

### Usage Patterns by Pricing Tier

```sql
-- Analyze usage patterns to inform pricing
WITH account_usage AS (
    SELECT 
        a.account_id,
        a.pricing_tier,
        a.mrr,
        COUNT(DISTINCT u.user_id) as total_users,
        COUNT(DISTINCT CASE WHEN e.timestamp >= CURRENT_DATE - INTERVAL '30 days' THEN u.user_id END) as mau,
        COUNT(DISTINCT e.event_id) FILTER (WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days') as monthly_events,
        COUNT(DISTINCT e.feature_name) FILTER (WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days') as features_used,
        SUM(CASE WHEN e.event_name = 'api_call' THEN 1 ELSE 0 END) FILTER (WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days') as api_calls,
        SUM(CASE WHEN e.event_name = 'report_generated' THEN 1 ELSE 0 END) FILTER (WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days') as reports_generated,
        SUM(e.data_processed_gb) FILTER (WHERE e.timestamp >= CURRENT_DATE - INTERVAL '30 days') as data_processed_gb
    FROM accounts a
    LEFT JOIN users u ON a.account_id = u.account_id
    LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY a.account_id, a.pricing_tier, a.mrr
),
usage_by_tier AS (
    SELECT 
        pricing_tier,
        COUNT(*) as accounts,
        AVG(mrr) as avg_mrr,
        -- Usage metrics
        AVG(total_users) as avg_users,
        AVG(mau) as avg_mau,
        AVG(monthly_events) as avg_events,
        AVG(api_calls) as avg_api_calls,
        AVG(data_processed_gb) as avg_data_gb,
        -- Usage intensity
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_events) as median_events,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY monthly_events) as p90_events,
        -- Find accounts exceeding typical usage
        COUNT(CASE WHEN monthly_events > 10000 THEN 1 END) as high_usage_accounts
    FROM account_usage
    GROUP BY pricing_tier
)
SELECT 
    pricing_tier,
    accounts,
    ROUND(avg_mrr, 2) as avg_mrr,
    ROUND(avg_users, 1) as avg_users,
    ROUND(avg_mau, 1) as avg_mau,
    ROUND(avg_events, 0) as avg_monthly_events,
    ROUND(avg_api_calls, 0) as avg_api_calls,
    ROUND(avg_data_gb, 2) as avg_data_gb,
    median_events,
    p90_events,
    high_usage_accounts,
    ROUND(high_usage_accounts * 100.0 / accounts, 2) as pct_high_usage
FROM usage_by_tier
ORDER BY 
    CASE pricing_tier
        WHEN 'Free' THEN 1
        WHEN 'Starter' THEN 2
        WHEN 'Professional' THEN 3
        WHEN 'Enterprise' THEN 4
    END;
```

### Value Metric Analysis

```sql
-- Identify the best value metric for pricing
WITH value_metrics AS (
    SELECT 
        a.account_id,
        a.mrr,
        au.total_users,
        au.mau,
        au.monthly_events,
        au.api_calls,
        au.data_processed_gb,
        au.reports_generated,
        -- Calculate correlations with MRR
        CORR(au.total_users, a.mrr) OVER () as users_mrr_corr,
        CORR(au.monthly_events, a.mrr) OVER () as events_mrr_corr,
        CORR(au.api_calls, a.mrr) OVER () as api_mrr_corr,
        CORR(au.data_processed_gb, a.mrr) OVER () as data_mrr_corr
    FROM accounts a
    JOIN account_usage au ON a.account_id = au.account_id
    WHERE a.mrr > 0
),
correlation_summary AS (
    SELECT DISTINCT
        ROUND(users_mrr_corr, 3) as users_correlation,
        ROUND(events_mrr_corr, 3) as events_correlation,
        ROUND(api_mrr_corr, 3) as api_correlation,
        ROUND(data_mrr_corr, 3) as data_correlation
    FROM value_metrics
)
SELECT * FROM correlation_summary;

-- Price elasticity analysis
WITH pricing_changes AS (
    SELECT 
        account_id,
        old_mrr,
        new_mrr,
        change_date,
        (new_mrr - old_mrr) / old_mrr * 100 as price_change_pct,
        churned_within_90d
    FROM account_pricing_history
    WHERE change_date >= CURRENT_DATE - INTERVAL '12 months'
      AND old_mrr > 0
),
elasticity_analysis AS (
    SELECT 
        CASE 
            WHEN price_change_pct < -10 THEN 'Decrease >10%'
            WHEN price_change_pct < 0 THEN 'Decrease 0-10%'
            WHEN price_change_pct <= 10 THEN 'Increase 0-10%'
            WHEN price_change_pct <= 25 THEN 'Increase 10-25%'
            ELSE 'Increase >25%'
        END as price_change_bucket,
        COUNT(*) as accounts_affected,
        AVG(CASE WHEN churned_within_90d THEN 1 ELSE 0 END) * 100 as churn_rate,
        AVG(price_change_pct) as avg_price_change
    FROM pricing_changes
    GROUP BY 
        CASE 
            WHEN price_change_pct < -10 THEN 'Decrease >10%'
            WHEN price_change_pct < 0 THEN 'Decrease 0-10%'
            WHEN price_change_pct <= 10 THEN 'Increase 0-10%'
            WHEN price_change_pct <= 25 THEN 'Increase 10-25%'
            ELSE 'Increase >25%'
        END
)
SELECT 
    price_change_bucket,
    accounts_affected,
    ROUND(avg_price_change, 1) as avg_price_change_pct,
    ROUND(churn_rate, 2) as churn_rate_pct
FROM elasticity_analysis
ORDER BY avg_price_change;
```

## 8. Product-Led Growth Metrics

### Viral Coefficient and Growth Loops

```sql
-- Calculate viral coefficient and referral metrics
WITH invitations AS (
    SELECT 
        inviter_user_id,
        invited_email,
        invitation_date,
        accepted_date,
        CASE WHEN accepted_date IS NOT NULL THEN 1 ELSE 0 END as accepted
    FROM user_invitations
    WHERE invitation_date >= CURRENT_DATE - INTERVAL '90 days'
),
viral_metrics AS (
    SELECT 
        DATE_TRUNC('month', invitation_date) as month,
        COUNT(DISTINCT inviter_user_id) as inviters,
        COUNT(invited_email) as invitations_sent,
        COUNT(accepted_date) as invitations_accepted,
        COUNT(invited_email) * 1.0 / COUNT(DISTINCT inviter_user_id) as invites_per_inviter,
        COUNT(accepted_date) * 100.0 / COUNT(invited_email) as acceptance_rate,
        -- Viral coefficient (K-factor)
        COUNT(accepted_date) * 1.0 / COUNT(DISTINCT inviter_user_id) as viral_coefficient
    FROM invitations
    GROUP BY DATE_TRUNC('month', invitation_date)
),
growth_loop AS (
    SELECT 
        month,
        inviters,
        invitations_sent,
        invitations_accepted,
        ROUND(invites_per_inviter, 2) as avg_invites_per_user,
        ROUND(acceptance_rate, 2) as acceptance_rate_pct,
        ROUND(viral_coefficient, 3) as k_factor,
        CASE 
            WHEN viral_coefficient > 1 THEN 'Viral Growth'
            WHEN viral_coefficient > 0.5 THEN 'Strong Referral'
            ELSE 'Weak Referral'
        END as growth_classification
    FROM viral_metrics
)
SELECT * FROM growth_loop
ORDER BY month DESC;
```

## 9. Executive Product Metrics Dashboard

```sql
-- Executive product metrics summary
WITH product_kpis AS (
    SELECT 
        -- Activation
        (SELECT COUNT(DISTINCT user_id) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as new_users,
        (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_name = 'activation_complete' AND timestamp >= CURRENT_DATE - INTERVAL '30 days') as activated_users,
        -- Engagement  
        (SELECT COUNT(DISTINCT user_id) FROM events WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day') as dau,
        (SELECT COUNT(DISTINCT user_id) FROM events WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days') as mau,
        -- Feature adoption
        (SELECT COUNT(DISTINCT user_id) FROM events WHERE feature_name = 'new_feature_q3' AND timestamp >= CURRENT_DATE - INTERVAL '30 days') as new_feature_users,
        -- Retention
        (SELECT 
            COUNT(DISTINCT CASE WHEN e2.user_id IS NOT NULL THEN u.user_id END) * 100.0 / COUNT(DISTINCT u.user_id)
         FROM users u
         LEFT JOIN events e2 ON u.user_id = e2.user_id AND e2.timestamp >= CURRENT_DATE - INTERVAL '30 days'
         WHERE u.created_at >= CURRENT_DATE - INTERVAL '60 days' AND u.created_at < CURRENT_DATE - INTERVAL '30 days'
        ) as month_1_retention
)
SELECT 
    new_users,
    activated_users,
    ROUND(activated_users * 100.0 / new_users, 2) as activation_rate,
    dau,
    mau,
    ROUND(dau * 100.0 / mau, 2) as stickiness,
    new_feature_users,
    ROUND(new_feature_users * 100.0 / mau, 2) as feature_adoption_rate,
    ROUND(month_1_retention, 2) as month_1_retention_rate
FROM product_kpis;
```

## 10. Practical Exercises

### Exercise 1: Feature Adoption Analysis
Analyze the adoption of a new feature launched 60 days ago:
1. Create adoption funnel (awareness → trial → adoption → retention)
2. Segment by user characteristics
3. Identify adoption barriers
4. Recommend improvements

### Exercise 2: A/B Test Design
Design an experiment to test a new onboarding flow:
1. Define success metrics
2. Calculate required sample size
3. Design assignment logic
4. Plan analysis approach

### Exercise 3: Pricing Model Analysis
Current pricing doesn't align with value delivery. Analyze:
1. Usage patterns by pricing tier
2. Identify the best value metric
3. Recommend new pricing structure
4. Estimate revenue impact

## Key Takeaways

1. **Metrics Drive Decisions**: Choose metrics that align with business goals
2. **Experimentation Culture**: Test everything, but test smart
3. **User-Centric Analysis**: Always ask "what does this mean for the user?"
4. **Statistical Rigor**: Ensure results are significant before acting
5. **Continuous Learning**: Product analytics is iterative

## Next Steps

- Project 1: Feature Adoption Cohort Analysis
- Project 2: Engagement Driver Study (follow-up)
- Advanced Topics: Predictive user modeling
- Cross-functional: Product-CS analytics alignment