-- Business Analytics Profile
-- This script provides key business metrics and insights

-- ========================================
-- 3. BUSINESS ANALYTICS PROFILE
-- ========================================

WITH revenue_metrics AS (
    SELECT 
        -- Overall revenue
        SUM(monthly_recurring_revenue) as total_mrr,
        SUM(annual_recurring_revenue) as total_arr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        
        -- Revenue by status
        SUM(CASE WHEN subscription_status = 'active' THEN monthly_recurring_revenue ELSE 0 END) as active_mrr,
        SUM(CASE WHEN subscription_status = 'trial' THEN monthly_recurring_revenue ELSE 0 END) as trial_mrr,
        SUM(CASE WHEN subscription_status = 'past_due' THEN monthly_recurring_revenue ELSE 0 END) as past_due_mrr,
        
        -- Subscription counts
        COUNT(*) as total_subscriptions,
        COUNT(CASE WHEN subscription_status = 'active' THEN 1 END) as active_subscriptions,
        COUNT(CASE WHEN subscription_status = 'trial' THEN 1 END) as trial_subscriptions,
        COUNT(CASE WHEN subscription_status = 'cancelled' THEN 1 END) as cancelled_subscriptions,
        COUNT(CASE WHEN subscription_status = 'past_due' THEN 1 END) as past_due_subscriptions,
        
        -- Health metrics
        AVG(payment_health_score) as avg_payment_health,
        AVG(churn_risk_score) as avg_churn_risk
        
    FROM entity.entity_subscriptions
),
plan_distribution AS (
    SELECT 
        plan_name,
        COUNT(*) as subscription_count,
        SUM(monthly_recurring_revenue) as plan_mrr,
        AVG(lifetime_value) as avg_ltv
    FROM entity.entity_subscriptions
    WHERE subscription_status = 'active'
    GROUP BY plan_name
),
user_engagement AS (
    SELECT 
        -- User counts
        COUNT(*) as total_users,
        COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_users,
        
        -- Engagement metrics
        AVG(engagement_score) as avg_engagement_score,
        
        -- User tiers
        COUNT(CASE WHEN user_engagement_tier = 'highly_engaged' THEN 1 END) as highly_engaged_users,
        COUNT(CASE WHEN user_engagement_tier = 'moderately_engaged' THEN 1 END) as moderately_engaged_users,
        COUNT(CASE WHEN user_engagement_tier = 'low_engagement' THEN 1 END) as low_engagement_users,
        COUNT(CASE WHEN user_engagement_tier = 'at_risk' THEN 1 END) as at_risk_users,
        
        -- Feature adoption
        AVG(features_adopted) as avg_features_adopted,
        AVG(feature_adoption_rate) as avg_feature_adoption_rate
        
    FROM entity.entity_users
),
location_metrics AS (
    SELECT 
        COUNT(*) as total_locations,
        COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_locations,
        AVG(operational_health_score) as avg_operational_health,
        COUNT(CASE WHEN operational_status = 'fully_operational' THEN 1 END) as fully_operational,
        COUNT(CASE WHEN operational_status = 'degraded' THEN 1 END) as degraded_locations,
        AVG(revenue_per_location) as avg_revenue_per_location
    FROM entity.entity_locations
),
growth_metrics AS (
    SELECT 
        DATE_TRUNC('month', created_at) as cohort_month,
        COUNT(*) as new_customers,
        SUM(monthly_recurring_revenue) as cohort_mrr
    FROM entity.entity_customers
    WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT 'BUSINESS ANALYTICS PROFILE' as profile_section, '=========================' as value
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'REVENUE METRICS', '---------------'
UNION ALL
SELECT 'Total MRR', '$' || TO_CHAR(total_mrr, 'FM999,999,999.00') FROM revenue_metrics
UNION ALL
SELECT 'Total ARR', '$' || TO_CHAR(total_arr, 'FM999,999,999.00') FROM revenue_metrics
UNION ALL
SELECT 'Average MRR per Subscription', '$' || TO_CHAR(avg_mrr, 'FM999,999.00') FROM revenue_metrics
UNION ALL
SELECT 'Active MRR', '$' || TO_CHAR(active_mrr, 'FM999,999,999.00') FROM revenue_metrics
UNION ALL
SELECT 'Trial MRR', '$' || TO_CHAR(trial_mrr, 'FM999,999,999.00') FROM revenue_metrics
UNION ALL
SELECT 'Past Due MRR', '$' || TO_CHAR(past_due_mrr, 'FM999,999,999.00') FROM revenue_metrics
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'SUBSCRIPTION METRICS', '-------------------'
UNION ALL
SELECT 'Total Subscriptions', total_subscriptions::text FROM revenue_metrics
UNION ALL
SELECT 'Active Subscriptions', active_subscriptions::text || ' (' || ROUND(active_subscriptions::numeric/total_subscriptions*100, 1) || '%)' FROM revenue_metrics
UNION ALL
SELECT 'Trial Subscriptions', trial_subscriptions::text || ' (' || ROUND(trial_subscriptions::numeric/total_subscriptions*100, 1) || '%)' FROM revenue_metrics
UNION ALL
SELECT 'Cancelled Subscriptions', cancelled_subscriptions::text || ' (' || ROUND(cancelled_subscriptions::numeric/total_subscriptions*100, 1) || '%)' FROM revenue_metrics
UNION ALL
SELECT 'Average Payment Health', ROUND(avg_payment_health, 1)::text FROM revenue_metrics
UNION ALL
SELECT 'Average Churn Risk', ROUND(avg_churn_risk, 1)::text FROM revenue_metrics
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'PLAN DISTRIBUTION', '-----------------'
UNION ALL
SELECT plan_name || ' (' || subscription_count || ')', 
       'MRR: $' || TO_CHAR(plan_mrr, 'FM999,999.00') || ', Avg LTV: $' || TO_CHAR(avg_ltv, 'FM999,999.00')
FROM plan_distribution
ORDER BY plan_mrr DESC
LIMIT 10;