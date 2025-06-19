{{
    config(
        materialized='incremental',
        unique_key=['account_id', 'valid_from'],
        on_schema_change='merge',
        indexes=[
            {'columns': ['account_id', 'valid_from']},
            {'columns': ['account_id', 'valid_to']},
            {'columns': ['change_type']}
        ]
    )
}}

-- Entity: Customers (Change History) - Simplified
-- Description: Complete audit trail of every customer state change
-- Primary Use Cases: Customer journey analysis, cohort studies, lifecycle progression tracking
-- Pattern: SCD Type 2 implementation

WITH current_state AS (
    SELECT 
        account_id,
        company_name,
        industry,
        customer_tier,
        customer_status,
        created_at,
        first_subscription_date,
        monthly_recurring_revenue,
        active_subscriptions,
        total_devices,
        device_events_30d,
        active_users_30d,
        customer_health_score,
        churn_risk_score,
        last_updated_at
    FROM {{ ref('entity_customers') }}
)

-- For initial load, create a single history record per customer
SELECT 
    account_id,
    company_name,
    industry,
    customer_tier,
    customer_status,
    created_at,
    first_subscription_date,
    monthly_recurring_revenue,
    active_subscriptions,
    total_devices,
    device_events_30d,
    active_users_30d,
    customer_health_score,
    churn_risk_score,
    created_at as valid_from,
    NULL::TIMESTAMP as valid_to,
    'initial_load' as change_type,
    monthly_recurring_revenue as mrr_change_amount,
    0 as health_score_change,
    active_subscriptions as subscription_change_count,
    0 as previous_health_score,
    0 as previous_churn_risk_score,
    0 as previous_mrr,
    NULL as previous_status,
    NULL as previous_tier,
    0 as previous_active_subscriptions,
    0 as previous_active_users_30d
FROM current_state

{% if is_incremental() %}
WHERE FALSE  -- Placeholder for incremental logic
{% endif %}