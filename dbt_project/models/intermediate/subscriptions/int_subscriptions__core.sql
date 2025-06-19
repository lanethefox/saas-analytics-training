{{ config(materialized='table') }}

-- Intermediate model: Subscription core information
-- Reconciles subscription data from app database and Stripe
-- Provides unified view with accurate revenue calculations

with app_subscriptions as (
    select * from {{ ref('stg_app_database__subscriptions') }}
),

stripe_subscriptions as (
    select * from {{ ref('stg_stripe__subscriptions') }}
),

stripe_subscription_items as (
    select * from {{ ref('stg_stripe__subscription_items') }}
),

stripe_prices as (
    select * from {{ ref('stg_stripe__prices') }}
),

-- Calculate MRR from Stripe subscription items
stripe_mrr_calc as (
    select
        si.stripe_subscription_id as subscription_id,
        sum(
            case 
                -- Convert different billing intervals to monthly
                when p.billing_interval = 'month' then si.quantity * p.unit_amount / 100.0
                when p.billing_interval = 'year' then si.quantity * p.unit_amount / 100.0 / 12
                when p.billing_interval = 'week' then si.quantity * p.unit_amount / 100.0 * 52 / 12
                when p.billing_interval = 'day' then si.quantity * p.unit_amount / 100.0 * 365 / 12
                else 0
            end
        ) as calculated_mrr
    from stripe_subscription_items si
    join stripe_prices p on si.stripe_price_id = p.price_id
    group by 1
),

-- Reconcile app and Stripe subscriptions
subscriptions_reconciled as (
    select
        -- Use app subscription as primary source
        coalesce(app.subscription_id::varchar, stripe.stripe_subscription_id) as subscription_id,
        coalesce(app.account_id::varchar, stripe.stripe_customer_id) as account_id,
        
        -- Subscription details (prefer app data, fallback to Stripe)
        coalesce(app.subscription_status, stripe.status) as subscription_status,
        coalesce(app.plan_tier, 'Standard') as plan_type,  -- Default value since stripe doesn't have this
        coalesce(app.billing_cycle, 'monthly') as billing_interval,  -- Default value since stripe doesn't have this directly
        
        -- Revenue (prefer calculated MRR from Stripe items)
        coalesce(mrr.calculated_mrr, app.normalized_mrr, 0) as monthly_recurring_revenue,
        
        -- Dates
        coalesce(app.subscription_created_at, stripe.subscription_created_at) as subscription_created_at,
        coalesce(app.start_date, stripe.subscription_start_date) as subscription_started_at,
        coalesce(stripe.canceled_at_date, app.end_date) as canceled_at,
        coalesce(stripe.current_period_start, app.start_date) as current_period_start,
        coalesce(stripe.current_period_end, app.end_date) as current_period_end,
        
        -- Trial information
        stripe.trial_start_date as trial_start_date,
        stripe.trial_end_date as trial_end_date,
        case 
            when stripe.trial_end_date is not null and stripe.trial_start_date is not null 
            then extract(days from stripe.trial_end_date - stripe.trial_start_date)
            else null
        end as trial_duration_days,
        
        -- Metadata for reconciliation tracking
        case 
            when app.subscription_id is not null and stripe.stripe_subscription_id is not null then 'both'
            when app.subscription_id is not null then 'app_only'
            when stripe.stripe_subscription_id is not null then 'stripe_only'
        end as data_source,
        
        -- Flags for data quality
        case 
            when app.subscription_id is not null and stripe.stripe_subscription_id is not null 
                and abs(coalesce(app.normalized_mrr, 0) - coalesce(mrr.calculated_mrr, 0)) > 1
            then true
            else false
        end as mrr_mismatch
        
    from app_subscriptions app
    full outer join stripe_subscriptions stripe 
        on app.subscription_id::varchar = stripe.stripe_subscription_id
    left join stripe_mrr_calc mrr 
        on coalesce(app.subscription_id::varchar, stripe.stripe_subscription_id) = mrr.subscription_id
),

final as (
    select
        -- Core identifiers
        {{ dbt_utils.generate_surrogate_key(['subscription_id']) }} as subscription_key,
        subscription_id,
        account_id,
        
        -- Subscription details
        subscription_status,
        plan_type,
        billing_interval,
        
        -- Revenue metrics
        monthly_recurring_revenue,
        
        -- Annual calculation
        case 
            when billing_interval = 'annual' then monthly_recurring_revenue * 12
            when billing_interval = 'monthly' then monthly_recurring_revenue * 12
            else 0
        end as annual_recurring_revenue,
        
        -- Recognized revenue (only for active subscriptions)
        case 
            when subscription_status in ('active', 'past_due') then monthly_recurring_revenue
            else 0
        end as recognized_mrr,
        
        -- Subscription timeline
        subscription_created_at,
        subscription_started_at,
        canceled_at,
        current_period_start,
        current_period_end,
        
        -- Subscription age
        extract(days from current_timestamp - subscription_started_at) as subscription_age_days,
        extract(months from age(current_timestamp, subscription_started_at)) as subscription_age_months,
        
        -- Trial information
        trial_start_date,
        trial_end_date,
        trial_duration_days,
        case 
            when trial_end_date >= current_date then true
            else false
        end as is_in_trial,
        
        -- Churn indicators
        case 
            when canceled_at is not null then true
            else false
        end as has_churned,
        
        case 
            when canceled_at is not null then 
                extract(days from canceled_at - subscription_started_at)
            else null
        end as lifetime_days,
        
        -- Subscription health
        case 
            when subscription_status = 'active' and monthly_recurring_revenue > 0 then 'healthy'
            when subscription_status = 'trial' then 'trial'
            when subscription_status = 'past_due' then 'at_risk'
            when subscription_status in ('canceled', 'unpaid') then 'churned'
            else 'unknown'
        end as subscription_health_status,
        
        -- Value tier
        case 
            when monthly_recurring_revenue >= 1000 then 'high_value'
            when monthly_recurring_revenue >= 500 then 'mid_value'
            when monthly_recurring_revenue >= 100 then 'standard_value'
            when monthly_recurring_revenue > 0 then 'low_value'
            else 'no_value'
        end as subscription_value_tier,
        
        -- Data quality
        data_source,
        mrr_mismatch,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from subscriptions_reconciled
)

select * from final