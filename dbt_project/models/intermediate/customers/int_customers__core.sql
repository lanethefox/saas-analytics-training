{{ config(materialized='table') }}

-- Intermediate model: Customer core information
-- Combines account data with subscription and billing information
-- Updated to match aligned staging schema

with accounts_base as (
    select * from {{ ref('stg_app_database__accounts') }}
),

subscriptions_current as (
    select
        account_id,
        subscription_status,
        normalized_mrr as monthly_recurring_revenue,
        plan_tier as plan_type,
        subscription_created_at,
        start_date as subscription_started_at,
        start_date as current_period_start,
        end_date as current_period_end,
        null as trial_start_date,  -- Not available in staging
        null as trial_end_date,    -- Not available in staging
        0 as trial_duration_days   -- Not available in staging
    from {{ ref('stg_app_database__subscriptions') }}
    where subscription_status in ('Active', 'Trial', 'Pending')
),

final as (
    select
        -- Core identifiers
        ab.account_id,
        ab.account_key,
        ab.account_name,
        ab.account_type,
        null as industry_vertical,  -- Not available in staging
        ab.account_status,
        
        -- Subscription information
        coalesce(sc.subscription_status, 'no_subscription') as subscription_status,
        coalesce(sc.monthly_recurring_revenue, 0) as monthly_recurring_revenue,
        coalesce(sc.plan_type, 'none') as plan_type,
        sc.subscription_started_at,
        sc.current_period_start,
        sc.current_period_end,
        sc.trial_start_date,
        sc.trial_end_date,
        sc.trial_duration_days,
        
        -- Account attributes
        ab.email as billing_email,
        ab.location_count as total_locations,
        ab.company_size_category,
        ab.account_type_tier,
        ab.account_age_days,
        ab.account_age_months,
        case when ab.account_type = 'trial' then true else false end as is_trial_account,
        case when ab.account_age_days <= 30 then true else false end as is_new_customer,
        
        -- Calculated metrics
        case 
            when sc.monthly_recurring_revenue > 0 then sc.monthly_recurring_revenue * 12
            else 0
        end as annual_recurring_revenue,
        
        case 
            when ab.location_count > 0 and sc.monthly_recurring_revenue > 0
            then sc.monthly_recurring_revenue / ab.location_count
            else 0
        end as mrr_per_location,
        
        -- Customer health indicators
        case 
            when sc.subscription_status = 'active' and sc.monthly_recurring_revenue > 0 then 0.9
            when sc.subscription_status = 'trial' then 0.6
            when sc.subscription_status = 'past_due' then 0.3
            else 0.1
        end as subscription_health_score,
        
        -- Lifecycle stage
        case 
            when sc.subscription_status = 'trial' then 'trial'
            when sc.subscription_status = 'active' and ab.account_age_days <= 90 then 'new_customer'
            when sc.subscription_status = 'active' and sc.monthly_recurring_revenue > 0 then 'active_customer'
            when sc.subscription_status = 'past_due' then 'at_risk'
            else 'inactive'
        end as customer_lifecycle_stage,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from accounts_base ab
    left join subscriptions_current sc on ab.account_id = sc.account_id
)

select * from final