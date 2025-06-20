-- Create basic views for Superset dashboards
-- Working with actual table schemas

-- Clean up any existing views
DROP VIEW IF EXISTS superset_sales_metrics CASCADE;
DROP VIEW IF EXISTS superset_customer_metrics CASCADE;
DROP VIEW IF EXISTS superset_marketing_metrics CASCADE;
DROP VIEW IF EXISTS superset_product_metrics CASCADE;
DROP VIEW IF EXISTS superset_executive_metrics CASCADE;

-- 1. Sales Metrics View
CREATE VIEW superset_sales_metrics AS
SELECT 
    CURRENT_DATE as report_date,
    total_revenue,
    pipeline_value,
    win_rate * 100 as win_rate_pct,
    avg_won_deal_size,
    total_deals,
    won_deals,
    open_deals,
    mqls_last_30d,
    total_mqls
FROM public.metrics_sales;

-- 2. Customer Success Metrics View  
CREATE VIEW superset_customer_metrics AS
SELECT 
    CURRENT_DATE as report_date,
    active_customers,
    total_customers,
    avg_health_score,
    total_mrr,
    avg_customer_lifetime_months,
    total_users,
    avg_user_engagement_score,
    nps_score
FROM public.metrics_customer_success;

-- 3. Marketing Metrics View
CREATE VIEW superset_marketing_metrics AS
SELECT 
    CURRENT_DATE as report_date,
    total_campaigns,
    active_campaigns,
    total_spend,
    total_impressions,
    total_clicks,
    total_conversions,
    avg_ctr * 100 as avg_ctr_pct,
    avg_conversion_rate * 100 as avg_conversion_rate_pct,
    avg_cpa,
    total_mqls,
    google_ads_campaigns_count,
    facebook_campaigns_count,
    linkedin_campaigns_count
FROM public.metrics_marketing;

-- 4. Product Analytics Metrics View
CREATE VIEW superset_product_metrics AS
SELECT 
    CURRENT_DATE as report_date,
    total_users,
    daily_active_users,
    weekly_active_users,
    monthly_active_users,
    ROUND(daily_active_users::numeric / NULLIF(monthly_active_users, 0) * 100, 1) as dau_mau_ratio,
    avg_engagement_score,
    avg_sessions_per_user,
    avg_features_per_user,
    total_features,
    overall_feature_adoption_rate * 100 as feature_adoption_pct
FROM public.metrics_product_analytics;

-- 5. Executive Summary View
CREATE VIEW superset_executive_metrics AS
SELECT 
    metric_date,
    total_mrr,
    active_customers,
    avg_customer_health,
    pipeline_value,
    dau,
    mau,
    device_availability_pct,
    total_mqls
FROM public.metrics_unified
WHERE metric_date = CURRENT_DATE;

-- 6. Customer Daily Trends
CREATE VIEW superset_customer_daily_trends AS
SELECT 
    date,
    customer_name,
    total_mrr,
    new_mrr,
    expansion_revenue,
    churned_revenue,
    active_users,
    total_logins,
    support_tickets,
    health_score
FROM entity.entity_customers_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;

-- 7. Campaign Performance
CREATE VIEW superset_campaign_summary AS
SELECT 
    campaign_name,
    platform,
    campaign_type,
    campaign_status,
    impressions,
    clicks,
    conversions,
    total_spend,
    click_through_rate * 100 as ctr_pct,
    conversion_rate * 100 as conversion_rate_pct,
    cost_per_click,
    cost_per_conversion,
    performance_score,
    performance_tier
FROM entity.entity_campaigns
WHERE campaign_created_at >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY total_spend DESC;

-- 8. User Engagement Summary
CREATE VIEW superset_user_engagement_summary AS
SELECT 
    user_role,
    COUNT(*) as user_count,
    AVG(engagement_score) as avg_engagement,
    AVG(days_since_last_login) as avg_days_since_login,
    SUM(total_sessions_30d) as total_sessions,
    AVG(features_used_30d) as avg_features_used
FROM entity.entity_users
WHERE user_status = 'active'
GROUP BY user_role;

-- 9. Device Performance Summary
CREATE VIEW superset_device_summary AS
SELECT 
    device_type,
    COUNT(*) as device_count,
    AVG(uptime_percentage) as avg_uptime,
    AVG(response_time_ms) as avg_response_time,
    SUM(event_volume_24h) as total_events_24h,
    AVG(health_score) as avg_health_score
FROM entity.entity_devices
WHERE device_status = 'active'
GROUP BY device_type;

-- 10. Revenue Waterfall
CREATE VIEW superset_revenue_waterfall AS
SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(new_mrr) as new_revenue,
    SUM(expansion_revenue) as expansion,
    SUM(contraction_revenue) as contraction,
    SUM(churned_revenue) as churn,
    SUM(new_mrr + expansion_revenue - contraction_revenue - churned_revenue) as net_change
FROM entity.entity_customers_daily
WHERE date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '6 months')
GROUP BY DATE_TRUNC('month', date)
ORDER BY month;

-- Verify all views were created
SELECT 
    'Created ' || COUNT(*) || ' views successfully' as status
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname LIKE 'superset_%';