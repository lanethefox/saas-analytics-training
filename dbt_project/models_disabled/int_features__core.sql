{{ config(materialized='table') }}

-- Intermediate model: Feature core information
-- Aggregates feature usage patterns and business impact across all users
-- Updated to match aligned staging schema

with feature_usage_base as (
    select * from {{ ref('stg_app_database__feature_usage') }}
),

feature_aggregates as (
    select
        feature_name,
        feature_category,
        
        -- Usage volume metrics (30-day window)
        count(distinct user_id) as unique_users_30d,
        count(distinct account_id) as unique_accounts_30d,
        count(*) as total_interactions_30d,
        sum(usage_duration_seconds) as total_usage_seconds_30d,
        
        -- Success and engagement metrics
        count(case when success_indicator then 1 end) as successful_uses_30d,
        avg(usage_duration_seconds) as avg_usage_duration_seconds,
        
        -- Temporal patterns
        min(feature_used_at) as first_usage_date, -- Fixed column name
        max(feature_used_at) as last_usage_date, -- Fixed column name
        
        -- User behavior patterns
        count(distinct case when feature_used_at >= current_timestamp - interval '7 days' then user_id end) as weekly_active_users, -- Fixed column name
        count(distinct case when feature_used_at >= current_timestamp - interval '1 day' then user_id end) as daily_active_users -- Fixed column name
        
    from feature_usage_base
    where feature_used_at >= current_date - 30 -- Fixed column name
    group by feature_name, feature_category
),

user_base_stats as (
    select
        count(distinct user_id) as total_platform_users,
        count(distinct account_id) as total_platform_accounts
    from {{ ref('stg_app_database__users') }}
),

final as (
    select
        -- Core identifiers
        fa.feature_name,
        fa.feature_category,
        
        -- Usage volume metrics
        fa.unique_users_30d,
        fa.unique_accounts_30d,
        fa.total_interactions_30d,
        fa.total_usage_seconds_30d,
        fa.successful_uses_30d,
        fa.avg_usage_duration_seconds,
        
        -- Adoption metrics
        case 
            when ubs.total_platform_users > 0
            then fa.unique_users_30d::numeric / ubs.total_platform_users
            else 0
        end as user_adoption_rate,
        
        case 
            when ubs.total_platform_accounts > 0
            then fa.unique_accounts_30d::numeric / ubs.total_platform_accounts
            else 0
        end as account_adoption_rate,
        
        case 
            when fa.total_interactions_30d > 0
            then fa.successful_uses_30d::numeric / fa.total_interactions_30d
            else 0
        end as success_rate,
        
        -- Engagement metrics
        case 
            when fa.unique_users_30d > 0
            then fa.total_interactions_30d::numeric / fa.unique_users_30d
            else 0
        end as avg_interactions_per_user,
        
        case 
            when fa.unique_users_30d > 0
            then fa.total_usage_seconds_30d::numeric / fa.unique_users_30d
            else 0
        end as avg_usage_seconds_per_user,
        
        -- Activity levels
        fa.weekly_active_users,
        fa.daily_active_users,
        
        case 
            when fa.weekly_active_users > 0 and fa.unique_users_30d > 0
            then fa.weekly_active_users::numeric / fa.unique_users_30d
            else 0
        end as weekly_retention_rate,
        
        case 
            when fa.daily_active_users > 0 and fa.weekly_active_users > 0
            then fa.daily_active_users::numeric / fa.weekly_active_users
            else 0
        end as daily_weekly_ratio,
        
        -- Temporal information
        fa.first_usage_date,
        fa.last_usage_date,
        case 
            when fa.first_usage_date is not null
            then (current_date - fa.first_usage_date::date)
            else null
        end as feature_age_days,
        
        -- Feature classification
        case 
            when (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.5 then 'core_feature'
            when (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.2 then 'popular_feature'
            when (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.05 then 'niche_feature'
            when fa.unique_users_30d > 0 then 'experimental_feature'
            else 'unused_feature'
        end as adoption_tier,
        
        case 
            when fa.success_rate >= 0.9 then 'highly_reliable'
            when fa.success_rate >= 0.7 then 'reliable'
            when fa.success_rate >= 0.5 then 'moderate_reliability'
            when fa.total_interactions_30d > 0 then 'low_reliability'
            else 'unknown_reliability'
        end as reliability_tier,
        
        case 
            when fa.avg_usage_duration_seconds >= 300 then 'deep_engagement' -- 5+ minutes
            when fa.avg_usage_duration_seconds >= 60 then 'moderate_engagement' -- 1-5 minutes
            when fa.avg_usage_duration_seconds >= 10 then 'light_engagement' -- 10s-1min
            when fa.total_interactions_30d > 0 then 'minimal_engagement'
            else 'no_engagement'
        end as engagement_tier,
        
        -- Business impact scoring
        case 
            when fa.feature_category = 'core' and (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.8 then 0.95
            when fa.feature_category = 'core' and (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.5 then 0.85
            when fa.feature_category = 'analytics' and (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.3 then 0.75
            when fa.feature_category = 'device' and (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.4 then 0.80
            when (case when ubs.total_platform_users > 0 then fa.unique_users_30d::numeric / ubs.total_platform_users else 0 end) >= 0.1 and (case when fa.total_interactions_30d > 0 then fa.successful_uses_30d::numeric / fa.total_interactions_30d else 0 end) >= 0.8 then 0.65
            when fa.unique_users_30d > 0 then 0.40
            else 0.10
        end as business_value_score,
        
        -- Feature health indicators
        case 
            when fa.unique_users_30d = 0 then 'at_risk'
            when fa.success_rate < 0.5 then 'quality_issues'
            when fa.user_adoption_rate < 0.05 and fa.feature_age_days > 90 then 'underperforming'
            when fa.weekly_retention_rate < 0.3 then 'retention_issues'
            else 'healthy'
        end as health_status,
        
        -- Growth indicators  
        case 
            when fa.feature_age_days <= 30 then 'new_feature'
            when fa.weekly_active_users > fa.daily_active_users * 3 then 'growing'
            when fa.user_adoption_rate >= 0.2 and fa.success_rate >= 0.8 then 'established'
            when fa.unique_users_30d > 0 then 'stable'
            else 'declining'
        end as growth_stage,
        
        -- Cross-reference with total users for context
        ubs.total_platform_users,
        ubs.total_platform_accounts,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from feature_aggregates fa
    cross join user_base_stats ubs
)

select * from final