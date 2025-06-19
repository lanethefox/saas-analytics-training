-- ID Reconciliation Script for Entity Tables
-- This creates normalized views from entity tables with consistent IDs

-- Create normalized schema if not exists
CREATE SCHEMA IF NOT EXISTS normalized;

-- Create normalized customers from entity.entity_customers
DROP TABLE IF EXISTS normalized.customers CASCADE;
CREATE TABLE normalized.customers AS
SELECT
    -- Core Identity
    account_id::VARCHAR AS account_id,
    company_name,
    industry,
    customer_tier,
    customer_status,
    created_at,
    
    -- Lifecycle
    first_subscription_date,
    days_since_creation,
    customer_lifetime_days,
    
    -- Revenue Metrics  
    COALESCE(monthly_recurring_revenue, 0)::NUMERIC(10,2) AS monthly_recurring_revenue,
    COALESCE(annual_recurring_revenue, 0)::NUMERIC(10,2) AS annual_recurring_revenue,
    
    -- Subscription Metrics
    COALESCE(active_subscriptions, 0) AS active_subscriptions,
    COALESCE(total_subscriptions, 0) AS total_subscriptions,
    
    -- Device Metrics
    COALESCE(total_devices, 0) AS total_devices,
    COALESCE(device_events_30d, 0) AS device_events_30d,
    COALESCE(avg_device_uptime_30d, 50) AS avg_device_uptime_30d,
    COALESCE(healthy_devices, 0) AS healthy_devices,
    COALESCE(device_health_percentage, 0) AS device_health_percentage,
    last_device_activity,
    
    -- User Metrics
    COALESCE(total_users, 0) AS total_users,
    COALESCE(active_users_7d, 0) AS active_users_7d,
    COALESCE(active_users_30d, 0) AS active_users_30d,
    COALESCE(user_activation_rate_30d, 0) AS user_activation_rate_30d,
    COALESCE(avg_user_engagement_score, 0) AS avg_user_engagement_score,
    last_user_activity,
    
    -- Location Metrics
    COALESCE(total_locations, 0) AS total_locations,
    COALESCE(active_locations, 0) AS active_locations,
    
    -- Churn Risk Score (placeholder)
    CASE 
        WHEN customer_status = 'churned' THEN 1.0
        WHEN monthly_recurring_revenue = 0 THEN 0.8
        WHEN active_users_30d = 0 THEN 0.7
        ELSE LEAST(0.6 * (1 - COALESCE(user_activation_rate_30d, 0)/100.0), 0.5)
    END AS churn_risk_score,
    
    -- Customer Health Score (placeholder)
    GREATEST(
        0.1,
        LEAST(
            1.0,
            (COALESCE(user_activation_rate_30d, 0)/100.0) * 0.3 +
            (COALESCE(device_health_percentage, 0)/100.0) * 0.3 +
            (CASE WHEN monthly_recurring_revenue > 0 THEN 0.4 ELSE 0 END)
        )
    ) AS customer_health_score,
    
    CURRENT_TIMESTAMP AS normalized_at
FROM entity.entity_customers;

-- Create normalized subscriptions from raw.app_database_subscriptions
DROP TABLE IF EXISTS normalized.subscriptions CASCADE;
CREATE TABLE normalized.subscriptions AS
SELECT
    id::VARCHAR AS subscription_id,
    account_id::VARCHAR AS account_id,
    subscription_tier,
    status AS subscription_status,
    created_at,
    updated_at,
    start_date,
    end_date,
    billing_cycle,
    COALESCE(monthly_recurring