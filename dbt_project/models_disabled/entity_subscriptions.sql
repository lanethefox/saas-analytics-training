{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['account_id']},
            {'columns': ['app_subscription_id']},
            {'columns': ['stripe_subscription_id']},
            {'columns': ['billing_health_status']}
        ],
        tags=['entity', 'atomic', 'subscriptions']
    )
}}

-- Entity Subscriptions: Current State Atomic Table
-- Contains the latest subscription state with billing metrics, health scoring, and risk indicators

with subscription_core as (
    select * from {{ ref('int_subscriptions__revenue_health') }}
),

final as (
    select
        -- Entity identifiers
        {{ dbt_utils.generate_surrogate_key(['sc.account_id', 'sc.app_subscription_id']) }} as subscription_key,
        sc.app_subscription_id,
        sc.account_id,
        sc.stripe_subscription_id,
        
        -- Current state attributes
        coalesce(sc.app_status, sc.stripe_status) as subscription_status,
        sc.plan_type,
        sc.plan_name,
        sc.app_billing_cycle,
        sc.stripe_billing_interval,
        
        -- Temporal attributes
        sc.subscription_created_at as created_at,
        sc.trial_start_date,
        sc.trial_end_date,
        sc.subscription_started_at as activated_at,
        coalesce(sc.canceled_at, sc.app_canceled_at) as canceled_at,
        sc.current_period_start,
        sc.current_period_end,
        sc.subscription_age_days,
        case 
            when sc.trial_end_date is not null 
            then extract(days from (sc.trial_end_date - current_date))
            else null
        end as days_until_trial_end,
        
        -- Revenue metrics
        sc.monthly_recurring_revenue,
        sc.annual_recurring_revenue,
        sc.unit_price_usd,
        sc.quantity,
        sc.total_revenue,
        sc.avg_invoice_amount,
        
        -- Billing health indicators
        sc.billing_health_status,
        sc.total_invoices,
        sc.paid_invoices,
        sc.open_invoices,
        sc.past_due_invoices,
        sc.outstanding_amount,
        sc.payment_success_rate,
        case 
            when sc.latest_invoice_date is not null
            then extract(days from (current_date - sc.latest_invoice_date::date))
            else null
        end as days_since_last_invoice,
        
        -- Risk scoring
        case 
            when sc.billing_health_status = 'past_due' then 0.9
            when sc.past_due_invoices > 0 then 0.8
            when sc.payment_success_rate < 0.5 then 0.7
            when sc.billing_health_status = 'pending_payment' then 0.6
            when coalesce(sc.app_status, sc.stripe_status) = 'trialing' 
                and sc.trial_end_date <= current_date + 7 then 0.5
            when sc.outstanding_amount > sc.monthly_recurring_revenue * 2 then 0.4
            when coalesce(sc.app_status, sc.stripe_status) = 'canceled' then 1.0
            else 0.1
        end as churn_risk_score,
        
        case 
            when coalesce(sc.app_status, sc.stripe_status) = 'canceled' then 'churned'
            when sc.billing_health_status = 'past_due' then 'critical'
            when sc.past_due_invoices > 0 then 'high'
            when sc.payment_success_rate < 0.8 then 'medium'
            else 'low'
        end as churn_risk_level,
        
        sc.cancellation_reason,
        
        -- Health grade calculation
        case 
            when coalesce(sc.app_status, sc.stripe_status) != 'active' then 'F'
            when sc.billing_health_status = 'past_due' then 'D'
            when sc.past_due_invoices > 2 then 'D'
            when sc.past_due_invoices > 0 then 'C'
            when sc.payment_success_rate >= 0.95 and sc.monthly_recurring_revenue >= 500 then 'A'
            when sc.payment_success_rate >= 0.8 then 'B'
            else 'C'
        end as subscription_health_grade,
        
        -- Derived risk categorization
        case 
            when coalesce(sc.app_status, sc.stripe_status) = 'trialing' 
                and sc.trial_end_date <= current_date + 7 then 'trial_ending_soon'
            when sc.billing_health_status = 'past_due' then 'payment_issue'
            when sc.past_due_invoices > 2 then 'repeated_payment_failures'
            when sc.outstanding_amount > sc.monthly_recurring_revenue * 2 then 'high_outstanding_balance'
            when coalesce(sc.app_status, sc.stripe_status) = 'canceled' then 'already_canceled'
            else 'low_risk'
        end as primary_risk_factor,
        
        -- Financial metrics
        case 
            when sc.subscription_age_days > 0 and sc.avg_invoice_amount > 0
            then sc.total_revenue / (sc.subscription_age_days / 30.0)
            else 0
        end as avg_monthly_revenue_realized,
        
        -- Contract value tiers
        case 
            when sc.annual_recurring_revenue >= 10000 then 'enterprise'
            when sc.annual_recurring_revenue >= 5000 then 'mid_market'
            when sc.annual_recurring_revenue >= 1000 then 'growth'
            when sc.annual_recurring_revenue >= 500 then 'starter'
            else 'micro'
        end as contract_value_tier,
        
        -- Billing frequency analysis
        case 
            when sc.app_billing_cycle = 'annual' or sc.stripe_billing_interval = 'year' then 'annual'
            when sc.app_billing_cycle = 'monthly' or sc.stripe_billing_interval = 'month' then 'monthly'
            else 'other'
        end as effective_billing_frequency,
        
        -- Next renewal timeline
        case 
            when sc.current_period_end is not null 
            then extract(days from (sc.current_period_end - current_date))
            else null
        end as days_to_renewal,
        
        case 
            when sc.current_period_end is not null then
                case 
                    when sc.current_period_end <= current_date + 7 then 'renewal_due'
                    when sc.current_period_end <= current_date + 30 then 'renewal_approaching'
                    when sc.current_period_end <= current_date + 90 then 'renewal_scheduled'
                    else 'renewal_distant'
                end
            else 'unknown'
        end as renewal_timeline,
        
        -- Customer lifetime value indicators
        sc.subscription_age_days * (sc.monthly_recurring_revenue / 30.0) as cumulative_subscription_value,
        
        -- Trial conversion probability (if applicable)
        case 
            when coalesce(sc.app_status, sc.stripe_status) = 'trialing' then
                case 
                    when sc.trial_duration_days > 0 
                        and sc.trial_start_date is not null
                        and extract(days from (current_date - sc.trial_start_date)) > 3
                    then 0.7  -- Simple heuristic: if they've been in trial for more than 3 days
                    else 0.3
                end
            else null
        end as trial_conversion_probability,
        
        -- Metadata
        current_timestamp as last_updated_at,
        '{{ invocation_id }}' as batch_id
        
    from subscription_core sc
)

select * from final