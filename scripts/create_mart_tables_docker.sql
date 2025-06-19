-- Create mart tables in Docker PostgreSQL (saas_platform_dev)
-- Based on available entity tables

-- First, let's create the mart schema
CREATE SCHEMA IF NOT EXISTS mart;

-- Marketing Campaigns Mart
-- Aggregates campaign data from entity_campaigns
CREATE TABLE IF NOT EXISTS mart.mart_marketing_campaigns AS
SELECT 
    campaign_id,
    campaign_name,
    channel,
    campaign_type,
    campaign_status,
    DATE_TRUNC('day', campaign_start_date) as period_start,
    budget,
    total_spend,
    impressions,
    clicks,
    conversions,
    revenue_attributed,
    CASE 
        WHEN total_spend > 0 THEN (revenue_attributed - total_spend) / total_spend 
        ELSE 0 
    END as roi,
    CASE 
        WHEN conversions > 0 THEN total_spend / conversions 
        ELSE NULL 
    END as cost_per_conversion,
    CASE 
        WHEN clicks > 0 THEN conversions::FLOAT / clicks 
        ELSE 0 
    END as conversion_rate,
    CASE 
        WHEN impressions > 0 THEN clicks::FLOAT / impressions 
        ELSE 0 
    END as click_through_rate,
    created_at,
    updated_at
FROM entity.entity_campaigns
WHERE campaign_start_date >= CURRENT_DATE - INTERVAL '2 years';

-- Customer Health Mart
CREATE TABLE IF NOT EXISTS mart.mart_customer_health AS
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
    END as health_score_bucket
FROM entity.entity_customers c
WHERE c.is_active = true;

-- MRR Analysis Mart
CREATE TABLE IF NOT EXISTS mart.mart_revenue_analysis AS
SELECT 
    DATE_TRUNC('month', cd.snapshot_date) as period_start,
    SUM(cd.total_mrr) as total_mrr,
    SUM(cd.new_mrr) as new_mrr,
    SUM(cd.expansion_mrr) as expansion_mrr,
    SUM(cd.churned_mrr) as churned_mrr,
    SUM(cd.total_mrr) * 12 as arr,
    COUNT(DISTINCT CASE WHEN cd.is_new_customer THEN cd.customer_id END) as new_customers,
    COUNT(DISTINCT CASE WHEN cd.is_churned THEN cd.customer_id END) as churned_customers,
    AVG(cd.customer_health_score) as avg_health_score
FROM entity.entity_customers_daily cd
WHERE cd.snapshot_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', cd.snapshot_date);

-- Device Operations Mart
CREATE TABLE IF NOT EXISTS mart.mart_device_operations AS
SELECT 
    d.device_id,
    d.device_serial_number,
    d.device_type,
    d.location_id,
    l.location_name,
    l.location_city,
    l.location_state,
    d.is_online,
    d.uptime_percentage_30d,
    d.health_score,
    d.events_last_24h,
    d.last_maintenance_date,
    CASE 
        WHEN d.health_score >= 90 THEN 'excellent'
        WHEN d.health_score >= 80 THEN 'good'
        WHEN d.health_score >= 70 THEN 'fair'
        ELSE 'needs_attention'
    END as health_status,
    CASE 
        WHEN d.last_maintenance_date < CURRENT_DATE - INTERVAL '90 days' THEN true
        ELSE false
    END as needs_maintenance
FROM entity.entity_devices d
LEFT JOIN entity.entity_locations l ON d.location_id = l.location_id
WHERE d.is_active = true;

-- User Engagement Mart
CREATE TABLE IF NOT EXISTS mart.mart_user_engagement AS
SELECT 
    u.user_id,
    u.user_email,
    u.user_role,
    u.customer_id,
    c.customer_name,
    u.engagement_score,
    CASE 
        WHEN u.engagement_score >= 80 THEN 'power_user'
        WHEN u.engagement_score >= 60 THEN 'regular_user'
        WHEN u.engagement_score >= 40 THEN 'occasional_user'
        ELSE 'dormant_user'
    END as user_segment,
    u.features_adopted_count,
    u.sessions_last_30d,
    u.events_last_30d,
    u.avg_session_duration_minutes,
    u.last_active_date,
    DATE_PART('day', CURRENT_DATE - u.last_active_date) as days_since_last_active
FROM entity.entity_users u
LEFT JOIN entity.entity_customers c ON u.customer_id = c.customer_id
WHERE u.is_active = true;

-- Feature Adoption Mart
CREATE TABLE IF NOT EXISTS mart.mart_feature_adoption AS
SELECT 
    f.feature_id,
    f.feature_name,
    f.feature_category,
    f.adoption_rate,
    f.usage_frequency_daily,
    f.customer_segments,
    f.revenue_impact,
    f.satisfaction_score,
    CASE 
        WHEN f.adoption_rate >= 0.8 THEN 'high_adoption'
        WHEN f.adoption_rate >= 0.5 THEN 'medium_adoption'
        WHEN f.adoption_rate >= 0.2 THEN 'low_adoption'
        ELSE 'minimal_adoption'
    END as adoption_tier,
    CASE 
        WHEN f.revenue_impact >= 1000 THEN 'high_value'
        WHEN f.revenue_impact >= 500 THEN 'medium_value'
        ELSE 'low_value'
    END as value_tier
FROM entity.entity_features f
WHERE f.is_active = true;

-- Location Performance Mart
CREATE TABLE IF NOT EXISTS mart.mart_location_performance AS
SELECT 
    l.location_id,
    l.location_name,
    l.location_address,
    l.location_city,
    l.location_state,
    l.location_zip,
    l.location_type,
    l.active_devices_count,
    l.operational_efficiency_score,
    l.customer_satisfaction_score,
    l.monthly_revenue,
    l.avg_device_uptime,
    CASE 
        WHEN l.operational_efficiency_score >= 90 THEN 'excellent'
        WHEN l.operational_efficiency_score >= 80 THEN 'good'
        WHEN l.operational_efficiency_score >= 70 THEN 'fair'
        ELSE 'needs_improvement'
    END as performance_tier,
    l.location_lat,
    l.location_lon
FROM entity.entity_locations l
WHERE l.is_active = true;

-- Subscription Lifecycle Mart
CREATE TABLE IF NOT EXISTS mart.mart_subscription_lifecycle AS
SELECT 
    s.subscription_id,
    s.customer_id,
    c.customer_name,
    s.plan_type,
    s.subscription_status,
    s.lifecycle_stage,
    s.monthly_recurring_revenue,
    s.annual_recurring_revenue,
    s.subscription_created_at,
    s.subscription_activated_at,
    s.next_renewal_date,
    DATE_PART('day', s.next_renewal_date - CURRENT_DATE) as days_until_renewal,
    s.is_annual,
    s.has_overages,
    s.discount_percentage,
    CASE 
        WHEN s.lifecycle_stage = 'trial' THEN 'acquisition'
        WHEN s.lifecycle_stage IN ('new', 'active') THEN 'growth'
        WHEN s.lifecycle_stage = 'expansion' THEN 'expansion'
        WHEN s.lifecycle_stage IN ('contraction', 'churned') THEN 'retention'
        ELSE 'other'
    END as lifecycle_phase
FROM entity.entity_subscriptions s
LEFT JOIN entity.entity_customers c ON s.customer_id = c.customer_id
WHERE s.subscription_created_at >= CURRENT_DATE - INTERVAL '2 years';

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO saas_user;
GRANT USAGE ON SCHEMA mart TO saas_user;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mart_campaigns_period ON mart.mart_marketing_campaigns(period_start);
CREATE INDEX IF NOT EXISTS idx_mart_health_customer ON mart.mart_customer_health(customer_id);
CREATE INDEX IF NOT EXISTS idx_mart_revenue_period ON mart.mart_revenue_analysis(period_start);
CREATE INDEX IF NOT EXISTS idx_mart_devices_location ON mart.mart_device_operations(location_id);
CREATE INDEX IF NOT EXISTS idx_mart_engagement_customer ON mart.mart_user_engagement(customer_id);
CREATE INDEX IF NOT EXISTS idx_mart_features_category ON mart.mart_feature_adoption(feature_category);
CREATE INDEX IF NOT EXISTS idx_mart_locations_state ON mart.mart_location_performance(location_state);
CREATE INDEX IF NOT EXISTS idx_mart_subscriptions_customer ON mart.mart_subscription_lifecycle(customer_id);

-- Add comments for documentation
COMMENT ON TABLE mart.mart_marketing_campaigns IS 'Marketing campaign performance metrics for all channels';
COMMENT ON TABLE mart.mart_customer_health IS 'Customer health scores and risk analysis';
COMMENT ON TABLE mart.mart_revenue_analysis IS 'Monthly revenue metrics including MRR movement';
COMMENT ON TABLE mart.mart_device_operations IS 'Device operational metrics and health status';
COMMENT ON TABLE mart.mart_user_engagement IS 'User engagement scores and activity patterns';
COMMENT ON TABLE mart.mart_feature_adoption IS 'Feature adoption rates and value analysis';
COMMENT ON TABLE mart.mart_location_performance IS 'Location operational efficiency and revenue';
COMMENT ON TABLE mart.mart_subscription_lifecycle IS 'Subscription lifecycle stages and revenue';
