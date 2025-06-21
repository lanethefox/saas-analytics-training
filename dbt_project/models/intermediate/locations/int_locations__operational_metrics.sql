{{
    config(
        materialized = 'table'
    )
}}

-- Intermediate model: Location operational metrics  
-- Detailed operational analytics for location performance monitoring
-- Updated to match aligned staging schema

with locations as (
    select * from {{ ref('stg_app_database__locations') }}
),

devices as (
    select * from {{ ref('stg_app_database__devices') }}
),

tap_events as (
    select * from {{ ref('stg_app_database__tap_events') }}
),

-- Calculate device counts and status per location
location_devices as (
    select
        location_id,
        count(distinct device_id) as total_devices,
        count(distinct case when status = 'online' then device_id end) as active_devices, -- Fixed status value
        count(distinct case when status = 'offline' then device_id end) as inactive_devices,
        count(distinct case when status = 'maintenance' then device_id end) as maintenance_devices,
        avg(case when status = 'online' then 1 else 0 end) as device_active_rate
    from devices
    group by 1
),

-- Calculate tap activity metrics per location
location_activity as (
    select
        te.location_id,
        count(distinct te.tap_event_id) as total_taps_last_30d,
        count(distinct te.device_id) as unique_devices_last_30d, -- Fixed to use device_id instead of user_id
        count(distinct date(te.event_timestamp)) as active_days_last_30d, -- Fixed column name
        sum(te.volume_ml::float) as total_volume_ml_30d, -- Added volume metric
        avg(te.flow_rate_ml_per_sec::float) as avg_flow_rate_30d, -- Added flow rate metric
        max(te.event_timestamp) as last_tap_timestamp -- Fixed column name
    from tap_events te
    where te.event_timestamp >= current_date - 30 -- Fixed column name and condition
    group by 1
),

-- User activity per location (joining through accounts)
location_user_activity as (
    select
        l.location_id,
        count(distinct u.user_id) as total_users,
        count(distinct case 
            when u.user_status in ('Active', 'Recent') 
            then u.user_id 
        end) as active_users,
        max(u.user_created_at) as last_user_activity -- Using user_created_at as proxy
    from locations l
    left join {{ ref('stg_app_database__users') }} u on l.account_id = u.account_id
    group by 1
),

-- Feature usage per location (through users)
location_feature_usage as (
    select
        l.location_id,
        count(distinct fu.feature_name) as unique_features_used_30d,
        count(distinct fu.usage_id) as total_feature_interactions_30d,
        sum(fu.usage_count) as total_feature_time_30d,
        max(fu.usage_timestamp) as last_feature_usage
    from locations l
    left join {{ ref('stg_app_database__users') }} u on l.account_id = u.account_id
    left join {{ ref('stg_app_database__feature_usage') }} fu on u.user_id = fu.user_id
    where fu.usage_timestamp >= current_date - 30
    group by 1
),

final as (
    select
        l.location_id,
        l.location_key,
        l.account_id,
        l.location_name,
        l.location_type,
        l.location_category,
        l.city,
        l.state as state_code,
        l.country as country_code,
        
        -- Device metrics
        coalesce(ld.total_devices, 0) as total_devices,
        coalesce(ld.active_devices, 0) as active_devices,
        coalesce(ld.inactive_devices, 0) as inactive_devices,
        coalesce(ld.maintenance_devices, 0) as maintenance_devices,
        coalesce(ld.device_active_rate, 0) as device_active_rate,
        
        -- Activity metrics (30-day)
        coalesce(la.total_taps_last_30d, 0) as total_taps_last_30d,
        coalesce(la.unique_devices_last_30d, 0) as unique_devices_last_30d,
        coalesce(la.active_days_last_30d, 0) as active_days_last_30d,
        coalesce(la.total_volume_ml_30d, 0) as total_volume_ml_30d,
        coalesce(la.avg_flow_rate_30d, 0) as avg_flow_rate_30d,
        la.last_tap_timestamp,
        
        -- User metrics
        coalesce(lua.total_users, 0) as total_users,
        coalesce(lua.active_users, 0) as active_users,
        lua.last_user_activity,
        
        -- Feature engagement
        coalesce(lfu.unique_features_used_30d, 0) as unique_features_used_30d,
        coalesce(lfu.total_feature_interactions_30d, 0) as total_feature_interactions_30d,
        coalesce(lfu.total_feature_time_30d, 0) as total_feature_time_30d,
        lfu.last_feature_usage,
        
        -- Derived operational metrics
        case 
            when ld.total_devices > 0
            then la.total_taps_last_30d::numeric / ld.total_devices
            else 0
        end as taps_per_device_30d,
        
        case 
            when la.active_days_last_30d > 0
            then la.total_taps_last_30d::numeric / la.active_days_last_30d
            else 0
        end as avg_taps_per_active_day,
        
        case 
            when lua.total_users > 0
            then la.total_taps_last_30d::numeric / lua.total_users
            else 0
        end as taps_per_user_30d,
        
        case 
            when la.total_taps_last_30d > 0
            then la.total_volume_ml_30d::numeric / la.total_taps_last_30d
            else 0
        end as avg_volume_per_tap,
        
        -- Operational health scoring
        case 
            when ld.device_active_rate >= 0.95 
                and la.active_days_last_30d >= 25
                and la.total_taps_last_30d > 100
            then 0.95
            when ld.device_active_rate >= 0.8 
                and la.active_days_last_30d >= 20
                and la.total_taps_last_30d > 50
            then 0.85
            when ld.device_active_rate >= 0.6 
                and la.active_days_last_30d >= 10
                and la.total_taps_last_30d > 10
            then 0.70
            when la.total_taps_last_30d > 0
            then 0.50
            else 0.20
        end as operational_health_score,
        
        -- Activity classification
        case 
            when la.total_taps_last_30d >= 1000 then 'high_activity'
            when la.total_taps_last_30d >= 500 then 'medium_activity'
            when la.total_taps_last_30d >= 100 then 'low_activity'
            when la.total_taps_last_30d > 0 then 'minimal_activity'
            else 'inactive'
        end as activity_level,
        
        case 
            when ld.device_active_rate >= 0.9 then 'excellent_health'
            when ld.device_active_rate >= 0.7 then 'good_health'
            when ld.device_active_rate >= 0.5 then 'fair_health'
            when ld.total_devices > 0 then 'poor_health'
            else 'no_devices'
        end as device_health_tier,
        
        -- Engagement assessment
        case 
            when lua.active_users >= 10 and lfu.unique_features_used_30d >= 5 then 'highly_engaged'
            when lua.active_users >= 5 and lfu.unique_features_used_30d >= 3 then 'engaged'
            when lua.active_users >= 2 and lfu.total_feature_interactions_30d >= 10 then 'moderately_engaged'
            when lua.active_users > 0 then 'lightly_engaged'
            else 'not_engaged'
        end as user_engagement_level,
        
        -- Performance indicators
        case 
            when la.last_tap_timestamp >= current_date - 1 then 'active_today'
            when la.last_tap_timestamp >= current_date - 7 then 'active_this_week'
            when la.last_tap_timestamp >= current_date - 30 then 'active_this_month'
            when la.last_tap_timestamp is not null then 'inactive'
            else 'never_active'
        end as recent_activity_status,
        
        -- Operational flags
        case 
            when ld.maintenance_devices > 0 then true
            else false
        end as has_maintenance_devices,
        
        case 
            when la.active_days_last_30d = 0 and ld.total_devices > 0 then true
            else false
        end as devices_but_no_activity,
        
        case 
            when lua.active_users > 0 and la.total_taps_last_30d = 0 then true
            else false
        end as users_but_no_taps,
        
        -- Location lifecycle
        extract(days from current_timestamp - l.location_created_at) as location_age_days,
        case 
            when extract(days from current_timestamp - l.location_created_at) <= 30 then 'new'
            when extract(days from current_timestamp - l.location_created_at) <= 180 then 'establishing'
            when extract(days from current_timestamp - l.location_created_at) <= 365 then 'mature'
            else 'veteran'
        end as location_lifecycle_stage,
        case 
            when extract(days from current_timestamp - l.location_created_at) <= 30 then true
            else false
        end as is_newly_opened,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from locations l
    left join location_devices ld on l.location_id = ld.location_id
    left join location_activity la on l.location_id = la.location_id
    left join location_user_activity lua on l.location_id = lua.location_id
    left join location_feature_usage lfu on l.location_id = lfu.location_id
)

select * from final