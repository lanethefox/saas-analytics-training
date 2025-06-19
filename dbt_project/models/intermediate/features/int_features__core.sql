{{ config(materialized='table') }}

-- Intermediate model: Feature core information
-- Analyzes feature usage patterns and adoption metrics
-- Provides foundation for Entity-Centric Feature model

with feature_usage_raw as (
    select * from {{ ref('stg_app_database__feature_usage') }}
),

accounts as (
    select * from {{ ref('stg_app_database__accounts') }}
),

users as (
    select * from {{ ref('stg_app_database__users') }}
),

-- Aggregate feature usage by feature
feature_aggregates as (
    select
        feature_name,
        feature_category,
        
        -- Usage counts
        count(distinct account_id) as accounts_using,
        count(distinct user_id) as users_using,
        count(*) as total_usage_events,
        
        -- Usage over time
        min(usage_timestamp) as first_usage_date,
        max(usage_timestamp) as last_usage_date,
        
        -- Usage frequency
        count(distinct date_trunc('day', usage_timestamp)) as days_with_usage,
        count(distinct date_trunc('week', usage_timestamp)) as weeks_with_usage,
        count(distinct date_trunc('month', usage_timestamp)) as months_with_usage
        
    from feature_usage_raw
    group by 1, 2
),

-- Calculate adoption metrics
feature_adoption as (
    select
        fa.*,
        
        -- Total possible adopters
        (select count(distinct account_id) from accounts where account_status = 'active') as total_active_accounts,
        (select count(distinct user_id) from users where user_status = 'active') as total_active_users,
        
        -- Calculate age
        extract(days from current_timestamp - first_usage_date) as feature_age_days,
        
        -- Recent usage indicators
        case 
            when last_usage_date >= current_date - interval '7 days' then true
            else false
        end as used_last_7_days,
        
        case 
            when last_usage_date >= current_date - interval '30 days' then true
            else false
        end as used_last_30_days
        
    from feature_aggregates fa
),

-- Add account-level usage patterns
account_feature_usage as (
    select
        f.feature_name,
        f.account_id,
        a.account_type,
        a.company_size_category,
        count(*) as account_usage_count,
        min(f.usage_timestamp) as account_first_usage,
        max(f.usage_timestamp) as account_last_usage,
        count(distinct f.user_id) as account_users_using
    from feature_usage_raw f
    join accounts a on f.account_id = a.account_id
    group by 1, 2, 3, 4
),

-- Identify power users of each feature
feature_power_users as (
    select
        feature_name,
        account_type,
        company_size_category,
        count(distinct account_id) as segment_accounts_using,
        avg(account_usage_count) as avg_usage_per_account,
        percentile_cont(0.9) within group (order by account_usage_count) as p90_usage_count
    from account_feature_usage
    group by 1, 2, 3
),

final as (
    select
        -- Core identifiers
        {{ dbt_utils.generate_surrogate_key(['fa.feature_name']) }} as feature_key,
        fa.feature_name,
        fa.feature_category,
        
        -- Usage metrics
        fa.accounts_using,
        fa.users_using,
        fa.total_usage_events,
        
        -- Adoption rates
        case 
            when fa.total_active_accounts > 0 then 
                fa.accounts_using::float / fa.total_active_accounts * 100
            else 0
        end as account_adoption_rate,
        
        case 
            when fa.total_active_users > 0 then 
                fa.users_using::float / fa.total_active_users * 100
            else 0
        end as user_adoption_rate,
        
        -- Usage timeline
        fa.first_usage_date,
        fa.last_usage_date,
        fa.feature_age_days,
        fa.days_with_usage,
        fa.weeks_with_usage,
        fa.months_with_usage,
        
        -- Usage frequency
        case 
            when fa.accounts_using > 0 then 
                fa.total_usage_events::float / fa.accounts_using
            else 0
        end as avg_usage_per_account,
        
        case 
            when fa.days_with_usage > 0 then 
                fa.total_usage_events::float / fa.days_with_usage
            else 0
        end as avg_daily_usage,
        
        -- Recent activity
        fa.used_last_7_days,
        fa.used_last_30_days,
        
        -- Feature health indicators
        case 
            when (fa.accounts_using::float / fa.total_active_accounts * 100) >= 80 then 'universal'
            when (fa.accounts_using::float / fa.total_active_accounts * 100) >= 50 then 'mainstream'
            when (fa.accounts_using::float / fa.total_active_accounts * 100) >= 20 then 'growing'
            when (fa.accounts_using::float / fa.total_active_accounts * 100) >= 5 then 'emerging'
            else 'experimental'
        end as adoption_stage,
        
        -- Engagement classification
        case 
            when fa.used_last_7_days and (fa.total_usage_events::float / fa.days_with_usage) > 100 then 'highly_engaged'
            when fa.used_last_30_days and (fa.total_usage_events::float / fa.days_with_usage) > 10 then 'engaged'
            when fa.used_last_30_days then 'moderate'
            when fa.last_usage_date >= current_date - interval '90 days' then 'declining'
            else 'dormant'
        end as engagement_level,
        
        -- Growth indicators
        case 
            when fa.feature_age_days <= 30 then 'new_feature'
            when fa.feature_age_days <= 90 then 'recent_feature'
            when fa.feature_age_days <= 365 then 'established_feature'
            else 'mature_feature'
        end as feature_maturity,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from feature_adoption fa
)

select * from final