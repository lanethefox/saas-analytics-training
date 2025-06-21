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
    COALESCE(c.industry_vertical, 'unknown') as industry,
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
    
    -- Simple health score based on MRR and status
    CASE
        WHEN c.account_status != 'active' THEN 0
        WHEN c.monthly_recurring_revenue IS NULL OR c.monthly_recurring_revenue = 0 THEN 10
        ELSE LEAST(100, GREATEST(0, (c.monthly_recurring_revenue / 100) * 50 + 50))
    END as customer_health_score,
    
    -- Simple churn risk score
    CASE
        WHEN c.account_status != 'active' THEN 100
        WHEN c.monthly_recurring_revenue IS NULL OR c.monthly_recurring_revenue = 0 THEN 90
        ELSE GREATEST(0, 100 - LEAST(100, (c.monthly_recurring_revenue / 100) * 50 + 50))
    END as churn_risk_score,
    
    -- Metadata
    CURRENT_TIMESTAMP as last_updated_at

FROM customer_core c