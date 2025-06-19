-- Marketing mart tables
CREATE SCHEMA IF NOT EXISTS mart;

-- Marketing Campaigns
CREATE TABLE IF NOT EXISTS mart.mart_marketing_campaigns AS
SELECT 
    c.campaign_id,
    c.campaign_name,
    c.channel,
    c.campaign_type,
    c.campaign_status,
    DATE_TRUNC('day', c.campaign_start_date) as period_start,
    c.budget,
    c.total_spend,
    c.impressions,
    c.clicks,
    c.conversions,
    c.revenue_attributed,
    CASE 
        WHEN c.total_spend > 0 THEN (c.revenue_attributed - c.total_spend) / c.total_spend 
        ELSE 0 
    END as roi,
    CASE 
        WHEN c.conversions > 0 THEN c.total_spend / c.conversions 
        ELSE NULL 
    END as cost_per_conversion,
    CASE 
        WHEN c.clicks > 0 THEN c.conversions::FLOAT / c.clicks 
        ELSE 0 
    END as conversion_rate,
    CASE 
        WHEN c.impressions > 0 THEN c.clicks::FLOAT / c.impressions 
        ELSE 0 
    END as click_through_rate,
    c.created_at,
    c.updated_at
FROM entity.entity_campaigns c
WHERE c.campaign_start_date >= CURRENT_DATE - INTERVAL '2 years';

-- Marketing Attribution
CREATE TABLE IF NOT EXISTS mart.mart_marketing_attribution AS
SELECT 
    'first_touch' as attribution_model,
    channel,
    COUNT(DISTINCT customer_id) as attributed_customers,
    COUNT(DISTINCT CASE WHEN subscription_id IS NOT NULL THEN customer_id END) as attributed_conversions,
    SUM(COALESCE(first_order_value, 0)) as attributed_revenue,
    AVG(days_to_conversion) as avg_days_to_conversion
FROM entity.entity_customers
WHERE first_touch_channel IS NOT NULL
GROUP BY channel
UNION ALL
SELECT 
    'last_touch' as attribution_model,
    channel,
    COUNT(DISTINCT customer_id) as attributed_customers,
    COUNT(DISTINCT CASE WHEN subscription_id IS NOT NULL THEN customer_id END) as attributed_conversions,
    SUM(COALESCE(first_order_value, 0)) as attributed_revenue,
    AVG(days_to_conversion) as avg_days_to_conversion
FROM entity.entity_customers
WHERE last_touch_channel IS NOT NULL
GROUP BY channel;

-- Marketing Performance
CREATE TABLE IF NOT EXISTS mart.mart_marketing_performance AS
SELECT 
    DATE_TRUNC('month', s.subscription_created_at) as period_start,
    COUNT(DISTINCT c.customer_id) as new_customers,
    SUM(c.customer_acquisition_cost) as total_acquisition_cost,
    AVG(c.customer_acquisition_cost) as customer_acquisition_cost,
    SUM(s.monthly_recurring_revenue) as new_mrr,
    COUNT(DISTINCT s.subscription_id) as new_subscriptions,
    AVG(c.customer_lifetime_value) as avg_ltv,
    CASE 
        WHEN AVG(c.customer_acquisition_cost) > 0 
        THEN AVG(c.customer_lifetime_value) / AVG(c.customer_acquisition_cost)
        ELSE NULL 
    END as ltv_to_cac_ratio
FROM entity.entity_customers c
JOIN entity.entity_subscriptions s ON c.customer_id = s.customer_id
WHERE s.subscription_created_at >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', s.subscription_created_at);

-- Sales mart tables
-- Sales Pipeline
CREATE TABLE IF NOT EXISTS mart.mart_sales_pipeline AS
SELECT 
    DATE_TRUNC('week', s.subscription_created_at) as period_start,
    s.lifecycle_stage as stage,
    COUNT(DISTINCT s.subscription_id) as opportunities,
    SUM(s.monthly_recurring_revenue * 12) as total_pipeline_value,
    AVG(s.monthly_recurring_revenue * 12) as avg_deal_size,
    COUNT(DISTINCT CASE WHEN s.subscription_status = 'active' THEN s.subscription_id END) as won_deals,
    COUNT(DISTINCT CASE WHEN s.subscription_status = 'churned' THEN s.subscription_id END) as lost_deals,
    CASE 
        WHEN COUNT(DISTINCT s.subscription_id) > 0 
        THEN COUNT(DISTINCT CASE WHEN s.subscription_status = 'active' THEN s.subscription_id END)::FLOAT / COUNT(DISTINCT s.subscription_id)
        ELSE 0 
    END as win_rate,
    AVG(EXTRACT(DAY FROM s.subscription_activated_at - s.subscription_created_at)) as avg_sales_cycle_days
FROM entity.entity_subscriptions s
WHERE s.subscription_created_at >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY DATE_TRUNC('week', s.subscription_created_at), s.lifecycle_stage;

-- Sales Activities
CREATE TABLE IF NOT EXISTS mart.mart_sales_activities AS
SELECT 
    DATE_TRUNC('day', u.last_login_date) as period_start,
    u.user_role as sales_rep_role,
    'demo' as activity_type,
    COUNT(DISTINCT u.user_id) as activity_count,
    COUNT(DISTINCT c.customer_id) as customers_touched,
    AVG(u.total_sessions) as avg_engagement_score
FROM entity.entity_users u
LEFT JOIN entity.entity_customers c ON u.customer_id = c.customer_id
WHERE u.user_role IN ('sales', 'account_executive', 'sales_manager')
  AND u.last_login_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', u.last_login_date), u.user_role;

-- Sales Targets
CREATE TABLE IF NOT EXISTS mart.mart_sales_targets AS
SELECT 
    DATE_TRUNC('month', s.subscription_created_at) as period_start,
    u.user_email as sales_rep,
    COUNT(DISTINCT s.subscription_id) as deals_closed,
    SUM(s.monthly_recurring_revenue) as revenue_closed,
    1000 as revenue_target, -- Placeholder target
    CASE 
        WHEN 1000 > 0 THEN (SUM(s.monthly_recurring_revenue) / 1000) * 100
        ELSE 0 
    END as attainment_percentage
FROM entity.entity_subscriptions s
JOIN entity.entity_users u ON s.sales_rep_id = u.user_id
WHERE s.subscription_created_at >= CURRENT_DATE - INTERVAL '1 year'
  AND u.user_role IN ('sales', 'account_executive')
GROUP BY DATE_TRUNC('month', s.subscription_created_at), u.user_email;

-- Customer Success mart tables
-- Customer Health
CREATE TABLE IF NOT EXISTS mart.mart_customer_success_health AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_health_score as health_score,
    CASE 
        WHEN c.customer_health_score >= 80 THEN 'healthy'
        WHEN c.customer_health_score >= 60 THEN 'at_risk'
        ELSE 'critical'
    END as health_status,
    CASE 
        WHEN c.customer_health_score < 60 THEN 'high'
        WHEN c.customer_health_score < 80 THEN 'medium'
        ELSE 'low'
    END as churn_risk,
    c.monthly_recurring_revenue as mrr,
    c.device_count,
    c.active_users_count,
    c.avg_daily_events as usage_intensity,
    c.features_adopted_count,
    c.last_support_ticket_date,
    c.nps_score,
    c.created_at as customer_since,
    CASE 
        WHEN c.customer_health_score >= 90 THEN '90-100'
        WHEN c.customer_health_score >= 80 THEN '80-89'
        WHEN c.customer_health_score >= 70 THEN '70-79'
        WHEN c.customer_health_score >= 60 THEN '60-69'
        WHEN c.customer_health_score >= 50 THEN '50-59'
        ELSE '0-49'
    END as health_score_bucket,
    1 as customer_count
FROM entity.entity_customers c
WHERE c.is_active = true;

-- Feature Adoption
CREATE TABLE IF NOT EXISTS mart.mart_customer_success_adoption AS
SELECT 
    f.feature_name,
    f.feature_category,
    COUNT(DISTINCT c.customer_id) as customers_using,
    COUNT(DISTINCT c.customer_id)::FLOAT / (SELECT COUNT(DISTINCT customer_id) FROM entity.entity_customers WHERE is_active = true) as adoption_rate,
    AVG(f.usage_frequency_daily) as avg_usage_frequency,
    SUM(c.monthly_recurring_revenue) as mrr_using_feature,
    AVG(c.customer_health_score) as avg_health_score_users
FROM entity.entity_features f
JOIN entity.entity_customers c ON true -- Simplified join for example
WHERE f.is_active = true
GROUP BY f.feature_name, f.feature_category
ORDER BY adoption_rate DESC;

-- Support Metrics
CREATE TABLE IF NOT EXISTS mart.mart_customer_success_support AS
SELECT 
    DATE_TRUNC('day', c.last_support_ticket_date) as period_start,
    COUNT(DISTINCT c.customer_id) as customers_with_tickets,
    COUNT(c.customer_id) as ticket_count,
    AVG(c.support_tickets_30d) as avg_tickets_per_customer,
    COUNT(CASE WHEN c.customer_health_score < 60 THEN 1 END) as high_risk_tickets,
    AVG(c.customer_health_score) as avg_health_score_ticket_customers
FROM entity.entity_customers c
WHERE c.last_support_ticket_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', c.last_support_ticket_date);

-- Product mart tables
-- Product Usage
CREATE TABLE IF NOT EXISTS mart.mart_product_usage AS
SELECT 
    DATE_TRUNC('day', u.last_active_date) as period_start,
    COUNT(DISTINCT u.user_id) as daily_active_users,
    COUNT(DISTINCT CASE WHEN u.sessions_last_7d > 0 THEN u.user_id END) as weekly_active_users,
    COUNT(DISTINCT CASE WHEN u.sessions_last_30d > 0 THEN u.user_id END) as monthly_active_users,
    AVG(u.total_sessions) as avg_sessions_per_user,
    AVG(u.total_events) as avg_events_per_user,
    f.feature_name,
    f.feature_category,
    COUNT(DISTINCT u.user_id) as usage_count,
    EXTRACT(HOUR FROM u.last_active_date) as hour_of_day
FROM entity.entity_users u
CROSS JOIN entity.entity_features f
WHERE u.last_active_date >= CURRENT_DATE - INTERVAL '90 days'
  AND u.is_active = true
GROUP BY DATE_TRUNC('day', u.last_active_date), f.feature_name, f.feature_category, EXTRACT(HOUR FROM u.last_active_date);

-- User Engagement
CREATE TABLE IF NOT EXISTS mart.mart_product_engagement AS
SELECT 
    u.user_id,
    u.user_email,
    u.user_role,
    CASE 
        WHEN u.engagement_score >= 80 THEN 'power_user'
        WHEN u.engagement_score >= 60 THEN 'regular_user'
        WHEN u.engagement_score >= 40 THEN 'occasional_user'
        ELSE 'dormant_user'
    END as user_segment,
    u.engagement_score,
    u.features_adopted_count,
    u.sessions_last_30d,
    u.events_last_30d,
    u.avg_session_duration_minutes,
    c.customer_name,
    c.industry,
    c.customer_size
FROM entity.entity_users u
LEFT JOIN entity.entity_customers c ON u.customer_id = c.customer_id
WHERE u.is_active = true;

-- Retention Cohorts
CREATE TABLE IF NOT EXISTS mart.mart_product_retention AS
WITH cohorts AS (
    SELECT 
        u.user_id,
        DATE_TRUNC('month', u.created_at) as cohort_month,
        DATE_TRUNC('month', u.last_active_date) as activity_month
    FROM entity.entity_users u
    WHERE u.created_at >= CURRENT_DATE - INTERVAL '2 years'
)
SELECT 
    cohort_month,
    EXTRACT(MONTH FROM AGE(activity_month, cohort_month)) as months_since_start,
    COUNT(DISTINCT user_id) as cohort_users,
    COUNT(DISTINCT CASE WHEN activity_month IS NOT NULL THEN user_id END)::FLOAT / 
        COUNT(DISTINCT user_id) as retention_rate
FROM cohorts
GROUP BY cohort_month, months_since_start;

-- Operations mart tables
-- Device Operations
CREATE TABLE IF NOT EXISTS mart.mart_operations_devices AS
SELECT 
    DATE_TRUNC('hour', CURRENT_TIMESTAMP) as period_start,
    l.location_id,
    l.location_name,
    l.location_city,
    l.location_state,
    COUNT(DISTINCT d.device_id) as total_devices,
    COUNT(DISTINCT CASE WHEN d.is_online THEN d.device_id END) as online_devices,
    AVG(d.uptime_percentage_30d) as avg_uptime_percentage,
    AVG(d.health_score) as avg_health_score,
    SUM(d.events_last_24h) as total_events_24h,
    COUNT(DISTINCT CASE WHEN d.last_maintenance_date < CURRENT_DATE - INTERVAL '90 days' THEN d.device_id END) as devices_needing_maintenance,
    COUNT(DISTINCT CASE WHEN d.health_score < 70 THEN d.device_id END) as unhealthy_devices
FROM entity.entity_devices d
JOIN entity.entity_locations l ON d.location_id = l.location_id
WHERE d.is_active = true
GROUP BY DATE_TRUNC('hour', CURRENT_TIMESTAMP), l.location_id, l.location_name, l.location_city, l.location_state;

-- Location Performance
CREATE TABLE IF NOT EXISTS mart.mart_operations_locations AS
SELECT 
    l.location_id,
    l.location_name,
    l.location_address,
    l.location_city,
    l.location_state,
    l.location_zip,
    l.location_lat,
    l.location_lon,
    l.location_type,
    l.active_devices_count,
    l.operational_efficiency_score as operational_efficiency,
    l.customer_satisfaction_score,
    l.monthly_revenue,
    l.avg_device_uptime,
    CASE 
        WHEN l.operational_efficiency_score >= 90 THEN 'excellent'
        WHEN l.operational_efficiency_score >= 80 THEN 'good'
        WHEN l.operational_efficiency_score >= 70 THEN 'fair'
        ELSE 'needs_improvement'
    END as performance_tier
FROM entity.entity_locations l
WHERE l.is_active = true;

-- Operational Efficiency
CREATE TABLE IF NOT EXISTS mart.mart_operations_efficiency AS
SELECT 
    DATE_TRUNC('day', CURRENT_DATE) as period_start,
    AVG(l.operational_efficiency_score) as overall_efficiency,
    AVG(d.uptime_percentage_30d) as avg_device_uptime,
    COUNT(DISTINCT l.location_id) as total_locations,
    COUNT(DISTINCT d.device_id) as total_devices,
    SUM(l.monthly_revenue) as total_revenue,
    SUM(l.monthly_revenue) / NULLIF(COUNT(DISTINCT l.location_id), 0) as revenue_per_location,
    SUM(d.events_last_24h) as total_events,
    COUNT(DISTINCT CASE WHEN d.health_score < 70 THEN d.device_id END)::FLOAT / 
        NULLIF(COUNT(DISTINCT d.device_id), 0) as device_issue_rate
FROM entity.entity_locations l
LEFT JOIN entity.entity_devices d ON l.location_id = d.location_id
WHERE l.is_active = true AND d.is_active = true
GROUP BY DATE_TRUNC('day', CURRENT_DATE);

-- Financial mart tables
-- Revenue Analysis
CREATE TABLE IF NOT EXISTS mart.mart_financial_revenue AS
SELECT 
    DATE_TRUNC('month', s.subscription_created_at) as period_start,
    s.plan_type as product_line,
    COUNT(DISTINCT s.subscription_id) as subscription_count,
    SUM(s.monthly_recurring_revenue) as total_mrr,
    SUM(CASE WHEN s.lifecycle_stage = 'new' THEN s.monthly_recurring_revenue ELSE 0 END) as new_mrr,
    SUM(CASE WHEN s.lifecycle_stage = 'expansion' THEN s.monthly_recurring_revenue ELSE 0 END) as expansion_mrr,
    SUM(CASE WHEN s.lifecycle_stage = 'churned' THEN s.monthly_recurring_revenue ELSE 0 END) as churned_mrr,
    SUM(s.monthly_recurring_revenue * 12) as arr,
    SUM(s.monthly_recurring_revenue) as revenue,
    AVG(s.monthly_recurring_revenue) as avg_revenue_per_subscription
FROM entity.entity_subscriptions s
WHERE s.subscription_created_at >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', s.subscription_created_at), s.plan_type;

-- Cost Analysis
CREATE TABLE IF NOT EXISTS mart.mart_financial_costs AS
SELECT 
    DATE_TRUNC('month', CURRENT_DATE) as period_start,
    'infrastructure' as cost_category,
    'cloud_hosting' as cost_subcategory,
    COUNT(DISTINCT d.device_id) * 10 as cost_amount -- Placeholder calculation
FROM entity.entity_devices d
WHERE d.is_active = true
GROUP BY DATE_TRUNC('month', CURRENT_DATE)
UNION ALL
SELECT 
    DATE_TRUNC('month', CURRENT_DATE) as period_start,
    'sales_marketing' as cost_category,
    'customer_acquisition' as cost_subcategory,
    SUM(c.customer_acquisition_cost) as cost_amount
FROM entity.entity_customers c
WHERE c.created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', CURRENT_DATE)
UNION ALL
SELECT 
    DATE_TRUNC('month', CURRENT_DATE) as period_start,
    'operations' as cost_category,
    'support' as cost_subcategory,
    COUNT(DISTINCT c.customer_id) * 50 as cost_amount -- Placeholder calculation
FROM entity.entity_customers c
WHERE c.last_support_ticket_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', CURRENT_DATE);

-- Profitability Analysis
CREATE TABLE IF NOT EXISTS mart.mart_financial_profitability AS
WITH revenue AS (
    SELECT 
        DATE_TRUNC('month', s.subscription_created_at) as period_start,
        SUM(s.monthly_recurring_revenue) as total_revenue
    FROM entity.entity_subscriptions s
    WHERE s.subscription_status = 'active'
    GROUP BY DATE_TRUNC('month', s.subscription_created_at)
),
costs AS (
    SELECT 
        DATE_TRUNC('month', c.created_at) as period_start,
        SUM(c.customer_acquisition_cost) + COUNT(DISTINCT c.customer_id) * 100 as total_costs -- Placeholder
    FROM entity.entity_customers c
    GROUP BY DATE_TRUNC('month', c.created_at)
)
SELECT 
    r.period_start,
    r.total_revenue,
    COALESCE(c.total_costs, 0) as total_costs,
    r.total_revenue - COALESCE(c.total_costs, 0) as gross_profit,
    CASE 
        WHEN r.total_revenue > 0 
        THEN ((r.total_revenue - COALESCE(c.total_costs, 0)) / r.total_revenue) * 100
        ELSE 0 
    END as gross_margin_percentage,
    r.total_revenue - COALESCE(c.total_costs, 0) as net_income
FROM revenue r
LEFT JOIN costs c ON r.period_start = c.period_start
WHERE r.period_start >= CURRENT_DATE - INTERVAL '2 years';

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO saas_user;
GRANT USAGE ON SCHEMA mart TO saas_user;
