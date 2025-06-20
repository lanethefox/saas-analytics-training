{{ config(materialized='view') }}

-- Staging model for Stripe subscription data
-- Tracks subscription lifecycle with MRR/ARR calculations

with source_data as (
    select * from {{ source('stripe', 'subscriptions') }}
),

enriched as (
    select
        -- Primary identifiers
        id as stripe_subscription_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_subscription_key,
        
        -- Foreign keys
        customer as stripe_customer_id,
        default_payment_method as stripe_payment_method_id,
        latest_invoice as stripe_latest_invoice_id,
        
        -- Subscription details
        status,
        cancel_at_period_end,
        'charge_automatically'::text as collection_method,  -- Default value since column doesn't exist
        days_until_due,
        
        -- Billing information
        billing_cycle_anchor,
        current_period_start,
        current_period_end,
        start_date as subscription_start_date,
        
        -- Trial information
        trial_start as trial_start_date,
        trial_end as trial_end_date,
        
        case
            when trial_end is not null and trial_end > current_timestamp then true
            else false
        end as is_in_trial,
        
        -- Cancellation information
        canceled_at as canceled_at_date,
        cancel_at as cancel_at_date,
        ended_at as ended_at_date,
        
        -- Extract account_id from metadata
        case 
            when metadata is not null 
            then metadata->>'account_id'
            else null
        end as account_id,
        
        -- Status categorization
        case
            when status = 'active' then 'Active'
            when status = 'past_due' then 'Past Due'
            when status = 'unpaid' then 'Unpaid'
            when status = 'canceled' then 'Canceled'
            when status = 'incomplete' then 'Incomplete'
            when status = 'incomplete_expired' then 'Incomplete Expired'
            when status = 'trialing' then 'Trialing'
            else 'Other'
        end as subscription_status_category,
        
        -- Lifecycle stage
        case
            when status = 'trialing' then 'Trial'
            when status = 'active' and current_period_start = start_date then 'New'
            when status = 'active' then 'Active'
            when status in ('past_due', 'unpaid') then 'At Risk'
            when status in ('canceled', 'incomplete_expired') then 'Churned'
            else 'Other'
        end as lifecycle_stage,
        
        -- Churn risk scoring
        case
            when status in ('canceled', 'incomplete_expired') then 100
            when cancel_at_period_end = true then 90
            when status = 'unpaid' then 80
            when status = 'past_due' then 70
            when status = 'incomplete' then 60
            when status = 'trialing' then 30
            when status = 'active' then 0
            else 50
        end as churn_risk_score,
        
        -- Subscription age
        extract(days from (current_timestamp - start_date)) as subscription_age_days,
        extract(months from age(current_timestamp, start_date)) as subscription_age_months,
        
        -- Additional flags
        livemode,
        
        -- Data quality
        case
            when id is null then 'Missing Subscription ID'
            when customer is null then 'Missing Customer'
            when status is null then 'Missing Status'
            else 'Valid'
        end as data_quality_flag,
        
        -- Raw data
        metadata,
        discount,
        items as subscription_items,
        
        -- Metadata
        created as subscription_created_at,
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
