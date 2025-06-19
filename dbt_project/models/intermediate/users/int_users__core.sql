{{ config(materialized='table') }}

-- Intermediate model: User core information  
-- Combines user profiles with session activity and feature usage metrics
-- Updated to match aligned staging schema

with users_base as (
    select * from {{ ref('stg_app_database__users') }}
),

session_summary as (
    select
        user_id,
        count(*) as total_sessions_30d,
        sum(duration_seconds / 60.0) as total_session_minutes_30d,
        avg(duration_seconds / 60.0) as avg_session_minutes_30d,
        max(start_time) as last_session_start,
        count(distinct date_trunc('day', start_time)) as active_days_30d,
        count(distinct device_type) as device_types_used_30d
    from {{ ref('stg_app_database__user_sessions') }}
    where start_time >= current_date - 30
    group by user_id
),

feature_usage_summary as (
    select
        user_id,
        count(distinct feature_name) as features_used_30d,
        count(*) as total_feature_interactions_30d,
        sum(usage_count) as total_feature_uses_30d,
        count(distinct feature_category) as feature_categories_used_30d,
        max(usage_timestamp) as last_feature_usage
    from {{ ref('stg_app_database__feature_usage') }}
    where usage_timestamp >= current_date - 30
    group by user_id
),

page_view_summary as (
    select
        pv.user_id,
        count(*) as total_page_views_30d,
        sum(time_on_page_seconds) as total_time_on_pages_30d,
        count(distinct page_category) as page_categories_visited_30d,
        count(distinct date_trunc('day', page_view_timestamp)) as page_active_days_30d,
        max(page_view_timestamp) as last_page_view
    from {{ ref('stg_app_database__page_views') }} pv
    where pv.page_view_timestamp >= current_date - 30
    group by pv.user_id
),

final as (
    select
        -- Core identifiers
        ub.user_id,
        ub.user_key,
        ub.account_id,
        ub.email,
        ub.first_name,
        ub.last_name,
        ub.full_name,
        ub.user_role,
        ub.role_category as role_type_standardized,
        ub.user_status,
        ub.permission_level as access_level,
        
        -- User categorization
        case when ub.created_date >= current_date - interval '30 days' then true else false end as is_new_user,
        case when ub.role_category = 'Admin' then true else false end as is_admin_user,
        case when ub.role_category = 'Manager' then true else false end as is_manager_user,
        ub.email_domain,
        case 
            when ub.email_domain in ('gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com') then 'personal'
            else 'business'
        end as email_type,
        
        -- Session activity (30-day metrics)
        coalesce(ss.total_sessions_30d, 0) as total_sessions_30d,
        coalesce(ss.total_session_minutes_30d, 0) as total_session_minutes_30d,
        coalesce(ss.avg_session_minutes_30d, 0) as avg_session_minutes_30d,
        coalesce(ss.active_days_30d, 0) as active_days_30d,
        coalesce(ss.device_types_used_30d, 0) as device_types_used_30d,
        ss.last_session_start,
        
        -- Feature usage (30-day metrics)
        coalesce(fus.features_used_30d, 0) as features_used_30d,
        coalesce(fus.total_feature_interactions_30d, 0) as total_feature_interactions_30d,
        coalesce(fus.total_feature_uses_30d, 0) as total_feature_uses_30d,
        coalesce(fus.feature_categories_used_30d, 0) as feature_categories_used_30d,
        fus.last_feature_usage,
        
        -- Page activity (30-day metrics)
        coalesce(pvs.total_page_views_30d, 0) as total_page_views_30d,
        coalesce(pvs.total_time_on_pages_30d, 0) as total_time_on_pages_30d,
        coalesce(pvs.page_categories_visited_30d, 0) as page_categories_visited_30d,
        coalesce(pvs.page_active_days_30d, 0) as page_active_days_30d,
        pvs.last_page_view,
        
        -- Derived engagement metrics
        case 
            when fus.total_feature_interactions_30d > 0
            then fus.total_feature_uses_30d::numeric / fus.total_feature_interactions_30d
            else 0
        end as avg_features_per_interaction_30d,
        
        case 
            when pvs.total_page_views_30d > 0 and pvs.total_time_on_pages_30d > 0
            then pvs.total_time_on_pages_30d::numeric / pvs.total_page_views_30d
            else 0
        end as avg_time_per_page_view_30d,
        
        case 
            when ss.total_sessions_30d > 0 and ss.active_days_30d > 0
            then ss.total_sessions_30d::numeric / ss.active_days_30d
            else 0
        end as sessions_per_active_day_30d,
        
        -- Engagement scoring
        case 
            when ss.active_days_30d >= 20 
                and fus.features_used_30d >= 5
                and pvs.page_categories_visited_30d >= 3
            then 0.9
            when ss.active_days_30d >= 10 
                and fus.features_used_30d >= 3
                and pvs.total_page_views_30d >= 50
            then 0.7
            when ss.active_days_30d >= 5 
                and (fus.features_used_30d >= 1 or pvs.total_page_views_30d >= 10)
            then 0.5
            when ss.active_days_30d >= 1
            then 0.3
            else 0.1
        end as engagement_score_30d,
        
        -- Activity classification
        case 
            when ss.active_days_30d >= 20 then 'highly_active'
            when ss.active_days_30d >= 10 then 'moderately_active'
            when ss.active_days_30d >= 5 then 'somewhat_active'
            when ss.active_days_30d >= 1 then 'minimally_active'
            else 'inactive'
        end as activity_level_30d,
        
        case 
            when fus.feature_categories_used_30d >= 4 then 'power_user'
            when fus.feature_categories_used_30d >= 2 then 'regular_user'
            when fus.feature_categories_used_30d >= 1 then 'basic_user'
            else 'non_user'
        end as feature_adoption_level,
        
        -- Lifecycle information
        ub.created_date as user_created_at,
        ub.created_date as user_updated_at,  -- No updated_at in staging
        ub.account_age_days as user_age_days,
        extract(months from age(current_timestamp, ub.created_date)) as user_age_months,
        ub.user_status as activity_status,
        ub.days_since_last_login,
        
        -- Most recent activity timestamp
        greatest(
            coalesce(ss.last_session_start, '1900-01-01'::timestamp),
            coalesce(fus.last_feature_usage, '1900-01-01'::timestamp),
            coalesce(pvs.last_page_view, '1900-01-01'::timestamp)
        ) as last_activity_timestamp,
        
        case 
            when greatest(
                coalesce(ss.last_session_start, '1900-01-01'::timestamp),
                coalesce(fus.last_feature_usage, '1900-01-01'::timestamp),
                coalesce(pvs.last_page_view, '1900-01-01'::timestamp)
            ) >= current_date - 7
            then 'recently_active'
            when greatest(
                coalesce(ss.last_session_start, '1900-01-01'::timestamp),
                coalesce(fus.last_feature_usage, '1900-01-01'::timestamp),
                coalesce(pvs.last_page_view, '1900-01-01'::timestamp)
            ) >= current_date - 30
            then 'somewhat_recent'
            else 'not_recent'
        end as recency_classification,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from users_base ub
    left join session_summary ss on ub.user_id = ss.user_id
    left join feature_usage_summary fus on ub.user_id = fus.user_id
    left join page_view_summary pvs on ub.user_id = pvs.user_id
)

select * from final