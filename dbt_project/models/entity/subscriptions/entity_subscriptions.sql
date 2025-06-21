{{ config(
    materialized='table',
    indexes=[
        {'columns': ['subscription_id'], 'unique': True},
        {'columns': ['account_id']},
        {'columns': ['subscription_status']},
        {'columns': ['monthly_recurring_revenue']},
        {'columns': ['churn_risk_score']}
    ]
) }}

-- Entity: Subscriptions (Atomic/Current State)
-- Revenue focus capturing MRR/ARR calculations, billing status, and lifecycle stage
-- Provides comprehensive view of current subscription state for revenue management

with subscription_core as (
    select * from {{ ref('int_subscriptions__core') }}
),

subscription_revenue as (
    select * from {{ ref('int_subscriptions__revenue_metrics') }}
),

final as (
    select
        -- Primary identifiers
        sr.subscription_id,
        sr.subscription_key,
        sr.account_id,
        
        -- Subscription details
        sr.subscription_status,
        sr.plan_type,
        sr.billing_interval,
        
        -- Revenue metrics
        sr.monthly_recurring_revenue,
        sr.annual_recurring_revenue,
        sr.recognized_mrr,
        sr.lifetime_value,
        sr.estimated_annual_ltv,
        sr.mrr_at_risk,
        
        -- Subscription timeline
        sr.subscription_created_at,
        sr.subscription_started_at,
        sr.canceled_at,
        sr.current_period_start,
        sr.current_period_end,
        
        -- Subscription age and lifecycle
        sr.subscription_age_days,
        sr.subscription_age_months,
        sr.lifetime_days,
        
        -- Trial information
        sr.trial_start_date,
        sr.trial_end_date,
        sr.trial_duration_days,
        sr.is_in_trial,
        
        -- Payment health metrics
        sr.total_invoices,
        sr.paid_invoices,
        sr.payment_success_rate,
        sr.recent_payment_rate,
        sr.charge_success_rate,
        sr.avg_days_to_payment,
        sr.days_since_last_payment,
        sr.last_payment_date,
        
        -- Health and risk scores
        sr.payment_health_score,
        sr.churn_risk_score,
        sr.subscription_health_status,
        sr.risk_classification,
        sr.payment_behavior,
        
        -- Value classification
        sr.subscription_value_tier,
        
        -- Lifecycle stage
        case 
            when sr.is_in_trial then 'trial'
            when sr.subscription_age_days < 30 then 'new'
            when sr.subscription_age_days < 90 then 'ramping'
            when sr.subscription_age_days < 365 then 'established'
            else 'mature'
        end as lifecycle_stage,
        
        -- Expansion opportunity scoring
        case 
            when sr.payment_health_score >= 90 
                and sr.subscription_age_months >= 3
                and sr.plan_type != 'Enterprise'
            then round((sr.payment_health_score * 0.5 + (100 - sr.churn_risk_score) * 0.5)::numeric, 2)
            else 0
        end as expansion_opportunity_score,
        
        -- Renewal risk indicators
        case 
            when sr.billing_interval = 'annual' 
                and sr.current_period_end <= current_date + interval '90 days'
                and sr.current_period_end > current_date
            then true
            else false
        end as upcoming_renewal,
        
        case 
            when sr.billing_interval = 'annual' 
                and sr.current_period_end <= current_date + interval '90 days'
                and sr.current_period_end > current_date
            then extract(days from sr.current_period_end - current_date)
            else null
        end as days_until_renewal,
        
        -- Status flags
        sr.has_churned,
        sr.mrr_mismatch,
        
        -- Data quality
        sr.data_source,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from subscription_revenue sr
)

select * from final