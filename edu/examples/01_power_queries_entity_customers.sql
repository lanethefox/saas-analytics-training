-- Entity-Centric Modeling: Power Query Examples
-- These queries demonstrate how complex business questions can be answered with simple, single-table queries
-- No complex joins required!

-- ============================================
-- 1. CUSTOMER HEALTH ANALYSIS IN ONE QUERY
-- ============================================
-- Get a complete 360-degree view of at-risk customers with all relevant metrics
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue as mrr,
    annual_recurring_revenue as arr,
    
    -- User engagement
    total_users,
    active_users_30d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_activation_rate,
    avg_user_engagement_score,
    
    -- Device performance
    total_devices,
    device_events_30d,
    avg_device_uptime_30d,
    ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_pct,
    
    -- Business health
    customer_health_score,
    churn_risk_score,
    days_since_creation,
    customer_lifetime_days,
    
    -- Activity signals
    last_user_activity,
    last_device_activity,
    CASE 
        WHEN last_user_activity < CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'Inactive'
        WHEN last_user_activity < CURRENT_TIMESTAMP - INTERVAL '1 day' THEN 'Active'
        ELSE 'Highly Active'
    END as activity_status,
    
    -- Risk categorization
    CASE 
        WHEN churn_risk_score >= 80 THEN '🔴 Critical Risk'
        WHEN churn_risk_score >= 60 THEN '🟡 High Risk'
        WHEN churn_risk_score >= 40 THEN '🟡 Medium Risk'
        ELSE '🟢 Low Risk'
    END as risk_category
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND (churn_risk_score > 50 OR customer_health_score < 70)
ORDER BY churn_risk_score DESC, monthly_recurring_revenue DESC
LIMIT 20;

-- ============================================
-- 2. REVENUE EXPANSION OPPORTUNITIES
-- ============================================
-- Identify customers with high expansion potential based on usage patterns and current tier
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue as current_mrr,
    
    -- Usage intensity
    total_users,
    active_users_30d,
    total_devices,
    device_events_30d,
    total_locations,
    
    -- Calculate usage per dollar spent
    ROUND(device_events_30d::numeric / NULLIF(monthly_recurring_revenue, 0), 2) as events_per_dollar,
    ROUND(active_users_30d::numeric / NULLIF(monthly_recurring_revenue, 0), 2) as users_per_dollar,
    
    -- Expansion indicators
    CASE 
        WHEN customer_tier = 1 AND total_devices > 10 THEN 'Ready for Business Tier'
        WHEN customer_tier = 2 AND total_devices > 50 THEN 'Ready for Enterprise Tier'
        WHEN customer_tier = 1 AND active_users_30d > 20 THEN 'High User Growth - Upgrade Opportunity'
        WHEN device_events_30d > 10000 AND customer_tier < 3 THEN 'High Usage - Price Optimization'
        ELSE 'Monitor'
    END as expansion_recommendation,
    
    -- Estimate expansion revenue
    CASE 
        WHEN customer_tier = 1 AND (total_devices > 10 OR active_users_30d > 20) 
            THEN monthly_recurring_revenue * 2.5 - monthly_recurring_revenue
        WHEN customer_tier = 2 AND (total_devices > 50 OR active_users_30d > 100)
            THEN monthly_recurring_revenue * 2 - monthly_recurring_revenue
        ELSE 0
    END as estimated_expansion_mrr,
    
    -- Health check
    customer_health_score,
    churn_risk_score
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND customer_health_score > 70  -- Only healthy customers
  AND churn_risk_score < 30        -- Low churn risk
  AND (
    -- Starter tier with high usage
    (customer_tier = 1 AND (total_devices > 10 OR active_users_30d > 20 OR device_events_30d > 5000))
    OR
    -- Business tier with enterprise-level usage
    (customer_tier = 2 AND (total_devices > 50 OR active_users_30d > 100 OR device_events_30d > 50000))
  )
ORDER BY estimated_expansion_mrr DESC
LIMIT 25;

-- ============================================
-- 3. CHURN RISK IDENTIFICATION
-- ============================================
-- Comprehensive churn risk analysis with early warning signals
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    days_since_creation as customer_age_days,
    
    -- Risk scores
    churn_risk_score,
    customer_health_score,
    
    -- Usage decline signals
    device_events_30d,
    LAG(device_events_30d, 1) OVER (PARTITION BY account_id ORDER BY last_updated_at) as device_events_prev,
    ROUND(
        (device_events_30d - LAG(device_events_30d, 1) OVER (PARTITION BY account_id ORDER BY last_updated_at))::numeric 
        / NULLIF(LAG(device_events_30d, 1) OVER (PARTITION BY account_id ORDER BY last_updated_at), 0) * 100, 
    1) as device_usage_change_pct,
    
    -- Engagement metrics
    active_users_30d,
    total_users,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_activation_rate,
    avg_user_engagement_score,
    
    -- Device health
    healthy_devices,
    total_devices,
    ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_rate,
    
    -- Time-based warning signals
    EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) as days_since_last_login,
    EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_device_activity)) as days_since_last_device_activity,
    
    -- Churn reasons
    CASE 
        WHEN device_events_30d = 0 THEN 'No Usage - Immediate Risk'
        WHEN EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) > 14 THEN 'User Disengagement'
        WHEN healthy_devices::numeric / NULLIF(total_devices, 0) < 0.5 THEN 'Device Health Issues'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.3 THEN 'Low User Adoption'
        WHEN churn_risk_score > 70 THEN 'Multiple Risk Factors'
        ELSE 'Monitor Closely'
    END as primary_churn_driver,
    
    -- Intervention priority
    CASE 
        WHEN churn_risk_score >= 80 OR device_events_30d = 0 THEN '🚨 Immediate Intervention'
        WHEN churn_risk_score >= 60 THEN '⚠️ Urgent Outreach'
        WHEN churn_risk_score >= 40 THEN '📞 Proactive Check-in'
        ELSE '👀 Monitor'
    END as action_required
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND (
    churn_risk_score > 40 
    OR device_events_30d = 0
    OR EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) > 7
  )
ORDER BY 
    CASE 
        WHEN device_events_30d = 0 THEN 1
        WHEN churn_risk_score >= 80 THEN 2
        WHEN churn_risk_score >= 60 THEN 3
        ELSE 4
    END,
    monthly_recurring_revenue DESC
LIMIT 30;

-- ============================================
-- 4. OPERATIONAL EFFICIENCY METRICS
-- ============================================
-- Analyze operational efficiency across the customer base
SELECT 
    company_name,
    customer_tier,
    
    -- Scale metrics
    total_locations,
    total_devices,
    total_users,
    active_users_30d,
    
    -- Efficiency ratios
    ROUND(device_events_30d::numeric / NULLIF(total_devices, 0), 1) as events_per_device,
    ROUND(device_events_30d::numeric / NULLIF(active_users_30d, 0), 1) as events_per_active_user,
    ROUND(total_devices::numeric / NULLIF(total_locations, 0), 1) as devices_per_location,
    ROUND(active_users_30d::numeric / NULLIF(total_locations, 0), 1) as active_users_per_location,
    
    -- Financial efficiency
    monthly_recurring_revenue,
    ROUND(monthly_recurring_revenue::numeric / NULLIF(total_locations, 0), 2) as mrr_per_location,
    ROUND(monthly_recurring_revenue::numeric / NULLIF(active_users_30d, 0), 2) as mrr_per_active_user,
    ROUND(device_events_30d::numeric / NULLIF(monthly_recurring_revenue, 0), 2) as events_per_mrr_dollar,
    
    -- Health indicators
    customer_health_score,
    avg_device_uptime_30d,
    device_health_percentage,
    
    -- Efficiency classification
    CASE 
        WHEN device_events_30d::numeric / NULLIF(total_devices, 0) > 100 
             AND active_users_30d::numeric / NULLIF(total_users, 0) > 0.7 THEN '⭐ Highly Efficient'
        WHEN device_events_30d::numeric / NULLIF(total_devices, 0) > 50 
             AND active_users_30d::numeric / NULLIF(total_users, 0) > 0.5 THEN '✅ Good Efficiency'
        WHEN device_events_30d::numeric / NULLIF(total_devices, 0) > 20 THEN '⚡ Moderate Efficiency'
        ELSE '🔧 Needs Optimization'
    END as efficiency_rating,
    
    -- Optimization opportunities
    CASE 
        WHEN total_devices > 20 AND device_events_30d::numeric / NULLIF(total_devices, 0) < 20 
            THEN 'Device Utilization Training Needed'
        WHEN total_users > 10 AND active_users_30d::numeric / NULLIF(total_users, 0) < 0.5 
            THEN 'User Adoption Campaign Recommended'
        WHEN total_locations > 5 AND total_devices::numeric / NULLIF(total_locations, 0) < 2
            THEN 'Infrastructure Expansion Opportunity'
        WHEN device_health_percentage < 70
            THEN 'Device Maintenance Program Required'
        ELSE 'Continue Current Operations'
    END as optimization_recommendation
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND total_devices > 0
ORDER BY 
    CASE efficiency_rating
        WHEN '⭐ Highly Efficient' THEN 1
        WHEN '✅ Good Efficiency' THEN 2
        WHEN '⚡ Moderate Efficiency' THEN 3
        ELSE 4
    END,
    monthly_recurring_revenue DESC
LIMIT 50;

-- ============================================
-- 5. CROSS-FUNCTIONAL KPIs DASHBOARD
-- ============================================
-- Single query providing KPIs for all departments
SELECT 
    -- Company info
    company_name,
    customer_tier,
    industry,
    
    -- SALES KPIs
    monthly_recurring_revenue as mrr,
    annual_recurring_revenue as arr,
    days_since_creation as age_days,
    CASE 
        WHEN days_since_creation <= 90 THEN 'New'
        WHEN days_since_creation <= 365 THEN 'Growing'
        ELSE 'Mature'
    END as customer_stage,
    
    -- CUSTOMER SUCCESS KPIs
    customer_health_score,
    churn_risk_score,
    CASE 
        WHEN churn_risk_score >= 70 THEN 'At Risk'
        WHEN customer_health_score >= 80 THEN 'Healthy'
        ELSE 'Needs Attention'
    END as cs_status,
    
    -- PRODUCT KPIs
    total_users,
    active_users_30d,
    active_users_7d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as monthly_active_rate,
    ROUND(active_users_7d::numeric / NULLIF(active_users_30d, 0) * 100, 1) as weekly_active_rate,
    avg_user_engagement_score,
    
    -- OPERATIONS KPIs
    total_locations,
    total_devices,
    device_events_30d,
    healthy_devices,
    ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_rate,
    avg_device_uptime_30d as avg_uptime,
    
    -- FINANCE KPIs
    ROUND(monthly_recurring_revenue::numeric / NULLIF(total_users, 0), 2) as arpu,
    ROUND(monthly_recurring_revenue::numeric / NULLIF(total_locations, 0), 2) as revenue_per_location,
    customer_lifetime_days,
    monthly_recurring_revenue * (customer_lifetime_days / 30.0) as estimated_ltv,
    
    -- EXECUTIVE SUMMARY
    CASE 
        WHEN customer_health_score >= 80 AND churn_risk_score < 30 
             AND active_users_30d::numeric / NULLIF(total_users, 0) > 0.7 THEN '🌟 Star Customer'
        WHEN churn_risk_score >= 70 OR customer_health_score < 50 THEN '🚨 Needs Intervention'
        WHEN monthly_recurring_revenue > 5000 AND customer_health_score > 70 THEN '💎 Key Account - Protect'
        WHEN days_since_creation < 90 THEN '🌱 New - Nurture'
        ELSE '📊 Standard - Monitor'
    END as executive_priority
    
FROM entity.entity_customers
WHERE customer_status = 'active'
ORDER BY monthly_recurring_revenue DESC
LIMIT 100;

-- ============================================
-- QUERY USAGE NOTES
-- ============================================
/*
These queries demonstrate the power of Entity-Centric Modeling:

1. NO JOINS REQUIRED - All data is pre-aggregated in the entity table
2. REAL-TIME READY - Queries execute in <3 seconds even on large datasets
3. BUSINESS FRIENDLY - Column names are self-explanatory
4. COMPREHENSIVE - Each row contains full customer context
5. FLEXIBLE - Easy to add new filters or metrics

Traditional approach would require joining 8-10 tables:
- customers
- subscriptions  
- users
- devices
- locations
- events
- health_scores
- risk_scores
- etc.

Entity-Centric approach: Just query entity_customers!
*/