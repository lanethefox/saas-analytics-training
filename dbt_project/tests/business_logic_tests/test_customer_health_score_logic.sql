-- Test: Customer Health Score Business Logic Validation
-- Ensures customer health scores align with business rules and underlying metrics

select 
    account_id,
    account_name,
    customer_health_score,
    churn_risk_score,
    monthly_recurring_revenue,
    device_events_30d,
    total_locations,
    active_devices,
    subscription_status
from {{ ref('entity_customers') }}
where 
    -- Health score should be inversely related to churn risk
    (customer_health_score > 0.8 and churn_risk_score > 0.4)
    
    -- High revenue customers with low activity should have lower health scores
    or (monthly_recurring_revenue >= 500 and device_events_30d < 100 and customer_health_score > 0.7)
    
    -- Customers with no device activity should have high churn risk
    or (device_events_30d = 0 and subscription_status = 'active' and churn_risk_score < 0.6)
    
    -- Customers with many devices but low events indicate problems
    or (active_devices >= 5 and device_events_30d < 50 and customer_health_score > 0.5)
    
    -- Multi-location customers with single device usage indicate adoption issues
    or (total_locations >= 3 and active_devices <= 2 and customer_health_score > 0.6)
    
    -- Trial customers with high activity should have lower churn risk
    or (subscription_status = 'trial' and device_events_30d >= 200 and churn_risk_score > 0.5)
    
    -- Cancelled customers should have high churn risk (if still in dataset)
    or (subscription_status = 'cancelled' and churn_risk_score < 0.8)
    
    -- Enterprise customers (high MRR) with low health scores need investigation
    or (monthly_recurring_revenue >= 1000 and customer_health_score < 0.4)
