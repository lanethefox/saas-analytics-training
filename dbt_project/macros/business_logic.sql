-- Macro for calculating customer health scores
-- Standardizes health scoring logic across all customer-related models

{% macro calculate_customer_health_score(
    subscription_status, 
    device_events_30d, 
    device_online_ratio, 
    is_delinquent,
    mrr
) %}
    case 
        when {{ subscription_status }} = 'active' 
            and {{ device_events_30d }} > 1000
            and {{ device_online_ratio }} > 0.8
            and not {{ is_delinquent }}
            and {{ mrr }} > 100
        then 0.95
        
        when {{ subscription_status }} = 'active' 
            and {{ device_events_30d }} > 500
            and {{ device_online_ratio }} > 0.6
            and not {{ is_delinquent }}
        then 0.80
        
        when {{ subscription_status }} = 'active' 
            and {{ device_events_30d }} > 100
            and {{ device_online_ratio }} > 0.4
        then 0.65
        
        when {{ subscription_status }} = 'active' 
            and {{ device_events_30d }} > 10
        then 0.50
        
        when {{ subscription_status }} in ('trialing', 'past_due')
            and {{ device_events_30d }} > 50
        then 0.35
        
        when {{ subscription_status }} in ('trialing', 'past_due')
        then 0.20
        
        else 0.05
    end
{% endmacro %}


-- Macro for calculating churn risk scores
-- Provides consistent churn risk assessment across models

{% macro calculate_churn_risk_score(
    subscription_status,
    device_events_30d,
    days_since_last_activity,
    is_delinquent,
    customer_health_score
) %}
    case 
        when {{ subscription_status }} in ('canceled', 'churned') then 1.0
        
        when {{ is_delinquent }} 
            and ({{ device_events_30d }} is null or {{ device_events_30d }} < 10) 
        then 0.95
        
        when {{ device_events_30d }} is null or {{ device_events_30d }} = 0 
        then 0.90
        
        when {{ days_since_last_activity }} > 60 
            and {{ device_events_30d }} < 50 
        then 0.85
        
        when {{ days_since_last_activity }} > 30 
            and {{ device_events_30d }} < 100 
        then 0.70
        
        when {{ customer_health_score }} < 0.3 
        then 0.65
        
        when {{ device_events_30d }} < 100 
        then 0.55
        
        when {{ days_since_last_activity }} > 14 
        then 0.40
        
        when {{ customer_health_score }} < 0.6 
        then 0.30
        
        else 0.15
    end
{% endmacro %}


-- Macro for normalizing MRR across different billing cycles
-- Handles monthly, annual, and custom billing periods

{% macro normalize_to_mrr(amount_cents, billing_interval, interval_count) %}
    case 
        when {{ billing_interval }} = 'month' and {{ interval_count }} = 1 
        then {{ amount_cents }} / 100.0
        
        when {{ billing_interval }} = 'year' and {{ interval_count }} = 1
        then {{ amount_cents }} / 1200.0
        
        when {{ billing_interval }} = 'month' and {{ interval_count }} > 1
        then {{ amount_cents }} / (100.0 * {{ interval_count }})
        
        when {{ billing_interval }} = 'week' and {{ interval_count }} = 1
        then ({{ amount_cents }} * 52) / 1200.0
        
        else {{ amount_cents }} / 100.0
    end
{% endmacro %}
