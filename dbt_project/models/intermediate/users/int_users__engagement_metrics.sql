{{
    config(
        materialized = 'table'
    )
}}

-- Intermediate model: User engagement metrics
-- Advanced behavioral analytics and engagement scoring
-- Updated to match aligned staging schema

with users as (
    select * from {{ ref('stg_app_database__users') }}
),

user_sessions as (
    select * from {{ ref('stg_app_database__user_sessions') }}
),

page_views as (
    select * from {{ ref('stg_app_database__page_views') }}
),

feature_usage as (
    select * from {{ ref('stg_app_database__feature_usage') }}
),

-- Session metrics
user_session_stats as (
    select
        user_id,
        count(distinct session_id) as total_sessions,
        count(distinct case when start_time >= current_date - interval '30 days' then session_id end) as sessions_last_30d,
        count(distinct case when start_time >= current_date - interval '7 days' then session_id end) as sessions_last_7d,
        avg(duration_seconds) as avg_session_duration_seconds,
        sum(duration_seconds) as total_session_duration_seconds,
        max(start_time) as last_session_time,
        min(start_time) as first_session_time
    from user_sessions
    group by 1
),

-- Page view metrics
user_page_stats as (
    select
        user_id,
        count(*) as total_page_views,
        count(distinct case when page_view_timestamp >= current_date - interval '30 days' then page_view_id end) as page_views_last_30d,
        count(distinct case when page_view_timestamp >= current_date - interval '7 days' then page_view_id end) as page_views_last_7d,
        count(distinct page_category) as unique_page_categories,
        sum(time_on_page_seconds) as total_time_on_pages_seconds,
        avg(time_on_page_seconds) as avg_time_per_page_seconds,
        max(page_view_timestamp) as last_page_view_time,
        min(page_view_timestamp) as first_page_view_time
    from page_views
    group by 1
),

-- Feature usage metrics
user_feature_stats as (
    select
        user_id,
        count(distinct feature_name) as unique_features_used,
        count(distinct case when usage_timestamp >= current_date - interval '30 days' then feature_name end) as features_used_last_30d,
        count(distinct case when usage_timestamp >= current_date - interval '7 days' then feature_name end) as features_used_last_7d,
        count(*) as total_feature_interactions,
        sum(usage_count) as total_feature_uses,
        max(usage_timestamp) as last_feature_use_time,
        min(usage_timestamp) as first_feature_use_time
    from feature_usage
    group by 1
),

-- Combined engagement metrics
final as (
    select
        u.user_id,
        u.user_key,
        u.account_id,
        u.email,
        u.full_name,
        u.user_role,
        u.role_category,
        u.created_date as user_created_at,
        
        -- Session engagement
        coalesce(uss.total_sessions, 0) as total_sessions,
        coalesce(uss.sessions_last_30d, 0) as sessions_last_30d,
        coalesce(uss.sessions_last_7d, 0) as sessions_last_7d,
        coalesce(uss.avg_session_duration_seconds, 0) as avg_session_duration_seconds,
        coalesce(uss.total_session_duration_seconds, 0) as total_session_duration_seconds,
        uss.last_session_time,
        uss.first_session_time,
        
        -- Page engagement
        coalesce(ups.total_page_views, 0) as total_page_views,
        coalesce(ups.page_views_last_30d, 0) as page_views_last_30d,
        coalesce(ups.page_views_last_7d, 0) as page_views_last_7d,
        coalesce(ups.unique_page_categories, 0) as unique_page_categories,
        coalesce(ups.total_time_on_pages_seconds, 0) as total_time_on_pages_seconds,
        coalesce(ups.avg_time_per_page_seconds, 0) as avg_time_per_page_seconds,
        ups.last_page_view_time,
        ups.first_page_view_time,
        
        -- Feature engagement
        coalesce(ufs.unique_features_used, 0) as unique_features_used,
        coalesce(ufs.features_used_last_30d, 0) as features_used_last_30d,
        coalesce(ufs.features_used_last_7d, 0) as features_used_last_7d,
        coalesce(ufs.total_feature_interactions, 0) as total_feature_interactions,
        coalesce(ufs.total_feature_uses, 0) as successful_feature_interactions,
        0 as total_feature_time_seconds,  -- Not available in staging
        0 as avg_feature_interaction_seconds,  -- Not available in staging
        ufs.last_feature_use_time,
        ufs.first_feature_use_time,
        
        -- Derived engagement metrics
        case 
            when ufs.total_feature_interactions > 0
            then ufs.total_feature_uses::numeric / ufs.total_feature_interactions
            else 0
        end as feature_success_rate,
        
        case 
            when uss.sessions_last_30d > 0
            then ups.page_views_last_30d::numeric / uss.sessions_last_30d
            else 0
        end as avg_page_views_per_session,
        
        case 
            when ups.page_views_last_30d > 0
            then ufs.features_used_last_30d::numeric / ups.page_views_last_30d
            else 0
        end as feature_adoption_ratio,
        
        -- Most recent activity across all channels
        greatest(
            coalesce(uss.last_session_time, '1900-01-01'::timestamp),
            coalesce(ups.last_page_view_time, '1900-01-01'::timestamp),
            coalesce(ufs.last_feature_use_time, '1900-01-01'::timestamp)
        ) as last_activity_timestamp,
        
        -- Engagement scoring (0-1 scale)
        least(1.0, greatest(0.0,
            (coalesce(uss.sessions_last_30d, 0) * 0.1 + 
             coalesce(ups.page_views_last_30d, 0) * 0.02 + 
             coalesce(ufs.features_used_last_30d, 0) * 0.15 +
             coalesce(ups.unique_page_categories, 0) * 0.05 +
             least(10, coalesce(uss.total_session_duration_seconds, 0) / 3600) * 0.1) / 5
        )) as engagement_score,
        
        -- User classification
        case 
            when coalesce(uss.sessions_last_30d, 0) >= 15 
                and coalesce(ufs.features_used_last_30d, 0) >= 5
                and coalesce(ups.unique_page_categories, 0) >= 3
            then 'power_user'
            when coalesce(uss.sessions_last_30d, 0) >= 8 
                and coalesce(ufs.features_used_last_30d, 0) >= 3
            then 'regular_user'
            when coalesce(uss.sessions_last_30d, 0) >= 3 
                and coalesce(ups.page_views_last_30d, 0) >= 10
            then 'casual_user'
            when coalesce(uss.sessions_last_30d, 0) >= 1
            then 'light_user'
            else 'inactive_user'
        end as user_engagement_tier,
        
        -- Activity recency
        case 
            when greatest(
                coalesce(uss.last_session_time, '1900-01-01'::timestamp),
                coalesce(ups.last_page_view_time, '1900-01-01'::timestamp),
                coalesce(ufs.last_feature_use_time, '1900-01-01'::timestamp)
            ) >= current_date - 1
            then 'active_today'
            when greatest(
                coalesce(uss.last_session_time, '1900-01-01'::timestamp),
                coalesce(ups.last_page_view_time, '1900-01-01'::timestamp),
                coalesce(ufs.last_feature_use_time, '1900-01-01'::timestamp)
            ) >= current_date - 7
            then 'active_this_week'
            when greatest(
                coalesce(uss.last_session_time, '1900-01-01'::timestamp),
                coalesce(ups.last_page_view_time, '1900-01-01'::timestamp),
                coalesce(ufs.last_feature_use_time, '1900-01-01'::timestamp)
            ) >= current_date - 30
            then 'active_this_month'
            else 'inactive'
        end as activity_recency,
        
        -- Behavioral patterns
        case 
            when coalesce(ups.avg_time_per_page_seconds, 0) >= 120 then 'deep_reader'
            when coalesce(ups.avg_time_per_page_seconds, 0) >= 30 then 'normal_reader'
            when coalesce(ups.total_page_views, 0) > 0 then 'quick_scanner'
            else 'non_reader'
        end as reading_behavior,
        
        case 
            when coalesce(ufs.features_used_last_30d, 0) >= 20 then 'thorough_user'
            when coalesce(ufs.features_used_last_30d, 0) >= 5 then 'normal_user'
            when coalesce(ufs.total_feature_interactions, 0) > 0 then 'quick_user'
            else 'non_user'
        end as feature_interaction_style,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from users u
    left join user_session_stats uss on u.user_id = uss.user_id
    left join user_page_stats ups on u.user_id = ups.user_id
    left join user_feature_stats ufs on u.user_id = ufs.user_id
)

select * from final