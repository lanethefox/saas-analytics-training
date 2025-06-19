{{ config(materialized='view') }}

-- Staging model for subscriptions
-- Standardizes subscription data with revenue calculations and lifecycle tracking

with source_data as (
    select * from {{ source('app_database', 'subscriptions') }}
),

enriched as (
    select
        -- Primary identifiers
        id as subscription_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as subscription_key,
        customer_id as account_id,
        
        -- Subscription details
        plan_name,
        lower(trim(status)) as status,
        billing_cycle,
        
        -- Plan tier categorization
        case
            when lower(plan_name) like '%enterprise%' then 'Enterprise'
            when lower(plan_name) like '%pro%' or lower(plan_name) like '%professional%' then 'Professional'
            when lower(plan_name) like '%business%' then 'Business'
            when lower(plan_name) like '%starter%' or lower(plan_name) like '%basic%' then 'Starter'
            when lower(plan_name) like '%trial%' or lower(plan_name) like '%free%' then 'Trial'
            else 'Custom'
        end as plan_tier,
        
        -- Status standardization
        case
            when lower(status) = 'active' then 'Active'
            when lower(status) in ('cancelled', 'canceled') then 'Cancelled'
            when lower(status) = 'expired' then 'Expired'
            when lower(status) = 'trial' then 'Trial'
            when lower(status) = 'pending' then 'Pending'
            else 'Other'
        end as subscription_status,
        
        -- Revenue calculations
        monthly_price,
        case
            when lower(billing_cycle) = 'monthly' then monthly_price
            when lower(billing_cycle) = 'quarterly' then monthly_price / 3.0
            when lower(billing_cycle) = 'annual' then monthly_price / 12.0
            when lower(billing_cycle) = 'yearly' then monthly_price / 12.0
            else monthly_price
        end as normalized_mrr,
        
        case
            when lower(billing_cycle) = 'monthly' then monthly_price * 12
            when lower(billing_cycle) = 'quarterly' then monthly_price * 4
            when lower(billing_cycle) = 'annual' then monthly_price
            when lower(billing_cycle) = 'yearly' then monthly_price
            else monthly_price * 12
        end as annual_revenue,
        
        -- Dates and lifecycle
        start_date,
        end_date,
        current_date - start_date as subscription_age_days,
        
        case
            when end_date is not null and end_date < current_date then 'Ended'
            when end_date is not null and end_date <= current_date + interval '30 days' then 'Expiring Soon'
            when start_date > current_date then 'Future'
            when start_date >= current_date - interval '30 days' then 'New'
            when start_date >= current_date - interval '90 days' then 'Recent'
            else 'Established'
        end as lifecycle_stage,
        
        -- Churn risk indicators
        case
            when lower(status) = 'active' and end_date <= current_date + interval '30 days' then 'High'
            when lower(status) = 'active' and end_date <= current_date + interval '90 days' then 'Medium'
            when lower(status) in ('trial', 'pending') then 'Unknown'
            when lower(status) in ('cancelled', 'canceled', 'expired') then 'Churned'
            else 'Low'
        end as churn_risk,
        
        -- Contract value
        case
            when end_date is not null then
                monthly_price * extract(month from age(end_date, start_date))
            else
                monthly_price * extract(month from age(current_date, start_date))
        end as total_contract_value,
        
        -- Data quality flags
        case 
            when plan_name is null or trim(plan_name) = '' then true 
            else false 
        end as missing_plan_name,
        
        case 
            when status is null or trim(status) = '' then true 
            else false 
        end as missing_status,
        
        case 
            when monthly_price is null or monthly_price < 0 then true 
            else false 
        end as invalid_price,
        
        -- Timestamps
        created_at as subscription_created_at,
        updated_at as subscription_updated_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
