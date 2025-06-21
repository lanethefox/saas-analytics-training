-- Test: Entity Customers Data Freshness
-- Ensures customer data is updated within acceptable timeframes

select 
    account_id,
    account_key,
    account_name,
    customer_health_score,
    monthly_recurring_revenue,
    device_events_30d,
    days_since_signup
from {{ ref('entity_customers') }}
where 
    -- Data freshness check - ensure no stale customer records
    (current_timestamp - account_created_at) > interval '2 years'
    and subscription_status = 'active'
    
    -- Health score validation
    or customer_health_score < 0 
    or customer_health_score > 1
    
    -- MRR validation  
    or monthly_recurring_revenue < 0
    or monthly_recurring_revenue > 10000  -- Reasonable upper bound
    
    -- Device events validation
    or device_events_30d < 0
    
    -- Churn risk validation
    or churn_risk_score < 0
    or churn_risk_score > 1
    
    -- Required field validation
    or account_key is null
    or account_name is null
    or subscription_status is null
