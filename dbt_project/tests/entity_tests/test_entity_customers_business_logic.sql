-- Test: Entity Customers Business Logic Validation
-- Ensures business rules are consistently applied

WITH validation_checks AS (
    SELECT 
        account_id,
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        customer_health_score,
        churn_risk_score,
        total_users,
        active_users_30d,
        total_devices,
        device_events_30d,
        
        -- Business rule violations
        CASE 
            WHEN customer_tier = 1 AND monthly_recurring_revenue > 999 THEN 'Starter tier MRR exceeds limit'
            WHEN customer_tier = 2 AND monthly_recurring_revenue > 4999 THEN 'Business tier MRR exceeds limit'
            WHEN customer_tier = 1 AND monthly_recurring_revenue < 50 THEN 'Starter tier MRR below minimum'
            ELSE NULL
        END as pricing_violation,
        
        CASE 
            WHEN active_users_30d > total_users THEN 'Active users exceed total users'
            WHEN healthy_devices > total_devices THEN 'Healthy devices exceed total devices'
            WHEN device_events_7d > device_events_30d THEN '7-day events exceed 30-day events'
            ELSE NULL
        END as count_violation,
        
        CASE 
            WHEN customer_health_score > 80 AND churn_risk_score > 70 THEN 'High health with high churn risk'
            WHEN customer_health_score < 30 AND churn_risk_score < 20 THEN 'Low health with low churn risk'
            ELSE NULL
        END as score_consistency_violation,
        
        CASE 
            WHEN customer_status = 'active' AND device_events_30d = 0 AND days_since_creation > 30 THEN 'Active customer with no usage'
            WHEN customer_status = 'churned' AND device_events_30d > 0 THEN 'Churned customer with recent usage'
            ELSE NULL
        END as status_violation
        
    FROM {{ ref('entity_customers') }}
)
SELECT 
    account_id,
    company_name,
    COALESCE(pricing_violation, count_violation, score_consistency_violation, status_violation) as violation_type,
    customer_tier,
    monthly_recurring_revenue,
    customer_health_score,
    churn_risk_score,
    total_users,
    active_users_30d,
    device_events_30d
FROM validation_checks
WHERE pricing_violation IS NOT NULL
   OR count_violation IS NOT NULL  
   OR score_consistency_violation IS NOT NULL
   OR status_violation IS NOT NULL;