{{ config(
    materialized='incremental',
    unique_key=['user_id', 'week_start_date'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'week_start_date',
        'data_type': 'date'
    },
    cluster_by=['user_id', 'week_start_date'],
    indexes=[
        {'columns': ['user_id', 'week_start_date'], 'unique': True},
        {'columns': ['week_start_date']},
        {'columns': ['account_id']}
    ]
) }}

-- Entity: Users (Weekly Strategic Grain)
-- Weekly user engagement aggregations for product analytics and experience optimization
-- Supports product planning, user experience reporting, and retention analysis

{% if is_incremental() %}
    {% set lookback_days = 7 %}
{% else %}
    {% set lookback_days = 365 %}
{% endif %}

with date_spine as (
    select distinct
        date_trunc('week', series_date)::date as week_start_date,
        date_trunc('week', series_date)::date + interval '6 days' as week_end_date
    from (
        select generate_series(
            current_date - interval '{{ lookback_days }} days',
            current_date,
            '1 day'::interval
        )::date as series_date
    ) dates
    where date_trunc('week', series_date)::date < date_trunc('week', current_date)
),

user_base as (
    select distinct
        user_id,
        user_key,
        account_id,
        user_created_at,
        email,
        full_name,
        user_role,
        role_type_standardized
    from {{ ref('entity_users') }}
),

-- Session activity aggregated by week
weekly_sessions as (
    select
        user_id,
        date_trunc('week', start_time)::date as week_start_date,
        count(distinct session_id) as weekly_sessions,
        count(distinct date_trunc('day', start_time)) as active_days,
        sum(duration_seconds / 60.0) as total_session_minutes,
        avg(duration_seconds / 60.0) as avg_session_minutes,
        max(duration_seconds / 60.0) as max_session_minutes,
        count(distinct device_type) as device_types_used,
        max(start_time) as last_session_time
    from {{ ref('stg_app_database__user_sessions') }}
    where start_time >= current_date - interval '{{ lookback_days }} days'
    group by 1, 2
),

-- Feature usage aggregated by week
weekly_features as (
    select
        user_id,
        date_trunc('week', usage_timestamp)::date as week_start_date,
        count(distinct feature_name) as features_used,
        count(distinct feature_category) as feature_categories_used,
        count(*) as total_feature_interactions,
        sum(usage_count) as total_feature_uses,
        max(usage_timestamp) as last_feature_use
    from {{ ref('stg_app_database__feature_usage') }}
    where usage_timestamp >= current_date - interval '{{ lookback_days }} days'
    group by 1, 2
),

-- Page views aggregated by week
weekly_pages as (
    select
        user_id,
        date_trunc('week', page_view_timestamp)::date as week_start_date,
        count(*) as total_page_views,
        count(distinct page_category) as page_categories_visited,
        sum(time_on_page_seconds) as total_time_on_pages,
        avg(time_on_page_seconds) as avg_time_per_page,
        max(page_view_timestamp) as last_page_view
    from {{ ref('stg_app_database__page_views') }}
    where page_view_timestamp >= current_date - interval '{{ lookback_days }} days'
    group by 1, 2
),

-- Combine all metrics
final as (
    select
        -- Identifiers
        u.user_id,
        u.user_key,
        u.account_id,
        d.week_start_date,
        d.week_end_date,
        
        -- User profile
        u.email,
        u.full_name,
        u.user_role,
        u.role_type_standardized,
        
        -- Session metrics
        coalesce(ws.weekly_sessions, 0) as weekly_sessions,
        coalesce(ws.active_days, 0) as active_days,
        coalesce(ws.total_session_minutes, 0) as total_session_minutes,
        coalesce(ws.avg_session_minutes, 0) as avg_session_minutes,
        coalesce(ws.max_session_minutes, 0) as max_session_minutes,
        coalesce(ws.device_types_used, 0) as device_types_used,
        
        -- Feature metrics
        coalesce(wf.features_used, 0) as features_used,
        coalesce(wf.feature_categories_used, 0) as feature_categories_used,
        coalesce(wf.total_feature_interactions, 0) as total_feature_interactions,
        coalesce(wf.total_feature_uses, 0) as total_feature_uses,
        
        -- Page metrics
        coalesce(wp.total_page_views, 0) as total_page_views,
        coalesce(wp.page_categories_visited, 0) as page_categories_visited,
        coalesce(wp.total_time_on_pages, 0) as total_time_on_pages,
        coalesce(wp.avg_time_per_page, 0) as avg_time_per_page,
        
        -- Derived metrics
        case 
            when ws.weekly_sessions > 0 
            then round(wp.total_page_views::numeric / ws.weekly_sessions, 2)
            else 0 
        end as avg_pages_per_session,
        
        case 
            when wf.total_feature_interactions > 0 
            then round(wf.total_feature_uses::numeric / wf.total_feature_interactions, 3)
            else 0 
        end as feature_success_rate,
        
        case 
            when ws.active_days > 0 
            then round(ws.weekly_sessions::numeric / ws.active_days, 2)
            else 0 
        end as sessions_per_active_day,
        
        -- Engagement scoring (weekly)
        case 
            when ws.active_days >= 5 and wf.features_used >= 5 then 0.9
            when ws.active_days >= 3 and wf.features_used >= 3 then 0.7
            when ws.active_days >= 2 and wp.total_page_views >= 20 then 0.5
            when ws.weekly_sessions >= 1 then 0.3
            else 0.1
        end as weekly_engagement_score,
        
        -- Activity classification
        case 
            when ws.active_days >= 5 then 'highly_active'
            when ws.active_days >= 3 then 'moderately_active'
            when ws.active_days >= 1 then 'minimally_active'
            else 'inactive'
        end as weekly_activity_level,
        
        -- Feature adoption
        case 
            when wf.feature_categories_used >= 4 then 'comprehensive'
            when wf.feature_categories_used >= 2 then 'moderate'
            when wf.features_used >= 1 then 'basic'
            else 'none'
        end as weekly_feature_adoption,
        
        -- User lifecycle stage at week
        case 
            when d.week_start_date < u.user_created_at then 'not_yet_created'
            when d.week_start_date < u.user_created_at + interval '7 days' then 'first_week'
            when d.week_start_date < u.user_created_at + interval '30 days' then 'onboarding'
            when d.week_start_date < u.user_created_at + interval '90 days' then 'developing'
            else 'established'
        end as user_lifecycle_stage,
        
        -- Week-over-week trends (calculated in next run)
        0 as sessions_wow_change,
        0 as features_wow_change,
        0 as engagement_wow_change,
        
        -- Retention cohort
        date_trunc('month', u.user_created_at)::date as cohort_month,
        floor(extract(epoch from age(d.week_start_date, u.user_created_at)) / 604800)::integer as weeks_since_signup,
        
        -- Most recent activity
        greatest(
            coalesce(ws.last_session_time, '1900-01-01'::timestamp),
            coalesce(wf.last_feature_use, '1900-01-01'::timestamp),
            coalesce(wp.last_page_view, '1900-01-01'::timestamp)
        ) as last_activity_in_week,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from date_spine d
    cross join user_base u
    left join weekly_sessions ws on u.user_id = ws.user_id and d.week_start_date = ws.week_start_date
    left join weekly_features wf on u.user_id = wf.user_id and d.week_start_date = wf.week_start_date
    left join weekly_pages wp on u.user_id = wp.user_id and d.week_start_date = wp.week_start_date
    where d.week_start_date >= u.user_created_at
    
    {% if is_incremental() %}
        and d.week_start_date >= current_date - interval '{{ lookback_days }} days'
    {% endif %}
)

select * from final