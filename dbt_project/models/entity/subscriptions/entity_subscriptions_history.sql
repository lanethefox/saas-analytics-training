{{ config(
    materialized='incremental',
    unique_key='subscription_history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['subscription_id', 'valid_from']},
        {'columns': ['valid_from']},
        {'columns': ['change_type']}
    ]
) }}

-- Entity: Subscriptions (History/Change Tracking)
-- Tracks subscription lifecycle including trials, conversions, upgrades, downgrades, and churn
-- Enables CLV modeling, pricing optimization, and churn analysis

with subscription_current as (
    select * from {{ ref('entity_subscriptions') }}
),

history_records as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['subscription_id', 'current_timestamp']) }} as subscription_history_id,
        
        -- Subscription identifiers
        subscription_id,
        subscription_key,
        account_id,
        
        -- Change tracking
        'snapshot' as change_type,
        
        -- Subscription details at time of change
        subscription_status,
        plan_type,
        billing_interval,
        lifecycle_stage,
        
        -- Revenue metrics at time of change
        monthly_recurring_revenue,
        0::numeric as previous_mrr,
        0::numeric as mrr_change_amount,
        
        annual_recurring_revenue,
        recognized_mrr,
        lifetime_value,
        estimated_annual_ltv,
        mrr_at_risk,
        
        -- Health and risk at time of change
        payment_health_score,
        0::numeric as previous_payment_health_score,
        
        churn_risk_score,
        0::integer as previous_churn_risk_score,
        
        subscription_health_status,
        ''::text as previous_health_status,
        
        risk_classification,
        ''::text as previous_risk_classification,
        
        -- Payment behavior
        payment_success_rate,
        recent_payment_rate,
        charge_success_rate,
        payment_behavior,
        
        -- Value and opportunity
        subscription_value_tier,
        ''::text as previous_value_tier,
        
        expansion_opportunity_score,
        
        -- Lifecycle tracking
        subscription_age_days,
        subscription_age_months,
        is_in_trial,
        has_churned,
        
        -- Renewal tracking
        upcoming_renewal,
        days_until_renewal,
        
        -- Key dates
        subscription_created_at,
        subscription_started_at,
        canceled_at,
        trial_start_date,
        trial_end_date,
        last_payment_date,
        
        -- Temporal validity
        current_timestamp as valid_from,
        null::timestamp as valid_to,
        true as is_current,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from subscription_current
    
    {% if is_incremental() %}
    -- For incremental runs, only capture meaningful changes
    where not exists (
        select 1 
        from {{ this }} h
        where h.subscription_id = subscription_current.subscription_id
          and h.is_current = true
          and h.subscription_status = subscription_current.subscription_status
          and h.monthly_recurring_revenue = subscription_current.monthly_recurring_revenue
          and h.churn_risk_score = subscription_current.churn_risk_score
          and h.subscription_health_status = subscription_current.subscription_health_status
          and h.plan_type = subscription_current.plan_type
    )
    {% endif %}
)

select * from history_records