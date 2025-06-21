{{ config(materialized='table') }}

-- Intermediate model: Subscription revenue analysis
-- Combines app subscriptions with Stripe billing data for MRR tracking

with app_subscriptions as (
    select * from {{ ref('stg_app_database__subscriptions') }}
),

stripe_subscriptions as (
    select * from {{ ref('stg_stripe__subscriptions') }}
),

stripe_items as (
    select * from {{ ref('stg_stripe__subscription_items') }}
),

stripe_invoices as (
    select * from {{ ref('stg_stripe__invoices') }}
),

subscription_revenue as (
    select
        ss.account_id,
        ss.stripe_subscription_id,
        si.monthly_recurring_revenue as stripe_mrr,
        si.unit_amount_cents,
        si.quantity,
        si.billing_interval,
        si.interval_count,
        si.price_nickname,
        ss.subscription_status as stripe_status,
        ss.trial_start,
        ss.trial_end,
        ss.trial_duration_days,
        ss.current_period_start,
        ss.current_period_end,
        ss.canceled_at,
        ss.cancellation_reason,
        ss.stripe_subscription_created_at
    from stripe_subscriptions ss
    left join stripe_items si on ss.stripe_subscription_id = si.stripe_subscription_id
    where ss.account_id is not null
),

billing_health as (
    select
        si.account_id,
        count(*) as total_invoices,
        count(case when si.invoice_status = 'paid' then 1 end) as paid_invoices,
        count(case when si.invoice_status = 'open' then 1 end) as open_invoices,
        count(case when si.invoice_status = 'past_due' then 1 end) as past_due_invoices,
        sum(case when si.invoice_status = 'paid' then si.amount_paid_usd else 0 end) as total_revenue,
        sum(case when si.invoice_status = 'open' then si.amount_due_usd else 0 end) as outstanding_amount,
        max(si.stripe_invoice_created_at) as latest_invoice_date,
        avg(si.amount_paid_usd) as avg_invoice_amount
    from stripe_invoices si
    where si.account_id is not null
    group by si.account_id
),

final as (
    select
        -- Core identifiers
        apps.account_id,
        apps.subscription_id as app_subscription_id,
        sr.stripe_subscription_id,
        
        -- Subscription details
        apps.plan_type,
        apps.plan_name,
        apps.billing_cycle as app_billing_cycle,
        sr.billing_interval as stripe_billing_interval,
        apps.subscription_status as app_status,
        sr.stripe_status,
        
        -- Revenue calculations
        coalesce(apps.monthly_recurring_revenue, sr.stripe_mrr, 0) as monthly_recurring_revenue,
        coalesce(apps.monthly_recurring_revenue, sr.stripe_mrr, 0) * 12 as annual_recurring_revenue,
        sr.unit_amount_cents / 100.0 as unit_price_usd,
        sr.quantity,
        
        -- Trial information
        coalesce(apps.trial_start_date, sr.trial_start) as trial_start_date,
        coalesce(apps.trial_end_date, sr.trial_end) as trial_end_date,
        coalesce(apps.trial_duration_days, sr.trial_duration_days) as trial_duration_days,
        
        -- Subscription lifecycle
        coalesce(apps.subscription_created_at, sr.stripe_subscription_created_at) as subscription_created_at,
        apps.subscription_started_at,
        sr.current_period_start,
        sr.current_period_end,
        sr.canceled_at,
        sr.cancellation_reason,
        apps.subscription_canceled_at as app_canceled_at,
        
        -- Billing health metrics
        bh.total_invoices,
        bh.paid_invoices,
        bh.open_invoices,
        bh.past_due_invoices,
        bh.total_revenue,
        bh.outstanding_amount,
        bh.latest_invoice_date,
        bh.avg_invoice_amount,
        
        -- Health indicators
        case 
            when bh.past_due_invoices > 0 then 'past_due'
            when bh.open_invoices > 0 then 'pending_payment'
            when coalesce(apps.subscription_status, sr.stripe_status) = 'active' then 'healthy'
            when coalesce(apps.subscription_status, sr.stripe_status) = 'trialing' then 'trial'
            else 'at_risk'
        end as billing_health_status,
        
        -- Revenue metrics
        case 
            when apps.subscription_created_at is not null 
            then extract(days from (current_date - apps.subscription_created_at::date))
            else null
        end as subscription_age_days,
        
        case 
            when bh.total_invoices > 0 
            then bh.paid_invoices / bh.total_invoices::decimal
            else null
        end as payment_success_rate,
        
        -- Metadata
        current_timestamp as _intermediate_created_at
        
    from app_subscriptions apps
    full outer join subscription_revenue sr on apps.account_id = sr.account_id
    left join billing_health bh on coalesce(apps.account_id, sr.account_id) = bh.account_id
    where coalesce(apps.account_id, sr.account_id) is not null
)

select * from final
