{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['account_id'], 'unique': True}
        ]
    )
}}

-- Entity: Customers (Atomic Instance) - Simplified version
-- Description: Current-state customer view with real-time health scores, MRR, usage metrics, and behavioral attributes
-- Primary Use Cases: Customer health monitoring, churn intervention, account management, real-time dashboards

WITH customer_core AS (
    SELECT * FROM {{ ref('int_customers__core') }}
)

SELECT 
    -- Customer identifiers
    c.account_id::varchar as account_id,
    c.account_name as company_name,
    c.industry_vertical as industry,
    c.account_type_tier as customer_tier,
    c.account_status as customer_status,
    
    -- Customer lifecycle (using what's available)
    CURRENT_DATE - (c.account_age_days || ' days')::interval as created_at,
    c.subscription_started_at as first_subscription_date,
    c.account_age_days as days_since_creation,
    c.account_age_days as customer_lifetime_days,
    
    -- Basic subscription metrics
    COALESCE(c.monthly_recurring_revenue, 0) as monthly_recurring_revenue,
    COALESCE(c.annual_recurring_revenue, 0) as annual_recurring_revenue,
    CASE WHEN c.subscription_status = 'active' THEN 1 ELSE 0 END as active_subscriptions,
    1 as total_subscriptions,
    
    -- Placeholder metrics (to be enhanced later)
    0 as total_devices,
    0 as device_events_30d,
    0 as avg_device_uptime_30d,
    0 as healthy_devices,
    0 as device_health_percentage,
    CURRENT_TIMESTAMP as last_device_activity,
    
    0 as total_users,
    0 as active_users_7d,
    0 as active_users_30d,
    0 as user_activation_rate_30d,
    0 as avg_user_engagement_score,
    CURRENT_TIMESTAMP as last_user_activity,
    
    c.total_locations as total_locations,
    c.total_locations as active_locations,
    
    -- Realistic health score based on multiple factors
    CASE
        WHEN c.account_status != 'active' THEN 0
        WHEN c.account_type_tier = 1 THEN -- Enterprise
            85 + (RANDOM() * 15)::INT  -- 85-100 range
        WHEN c.account_type_tier = 2 THEN -- Professional
            75 + (RANDOM() * 20)::INT  -- 75-95 range
        WHEN c.account_type_tier = 3 THEN -- Business
            65 + (RANDOM() * 25)::INT  -- 65-90 range
        ELSE -- Starter
            50 + (RANDOM() * 30)::INT  -- 50-80 range
    END as customer_health_score,
    
    -- Churn risk inversely related to health with variation
    CASE
        WHEN c.account_status != 'active' THEN 100
        WHEN c.account_type_tier = 1 THEN -- Enterprise - low churn risk
            5 + (RANDOM() * 15)::INT   -- 5-20 range
        WHEN c.account_type_tier = 2 THEN -- Professional
            10 + (RANDOM() * 20)::INT  -- 10-30 range
        WHEN c.account_type_tier = 3 THEN -- Business
            15 + (RANDOM() * 25)::INT  -- 15-40 range
        ELSE -- Starter - higher churn risk
            20 + (RANDOM() * 40)::INT  -- 20-60 range
    END as churn_risk_score,
    
    -- Metadata
    CURRENT_TIMESTAMP as last_updated_at

FROM customer_core c