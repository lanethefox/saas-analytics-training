{{ config(materialized='table') }}

-- Intermediate model: Location core information
-- Combines location data with device counts and operational metrics
-- Updated to match aligned staging schema

with locations_base as (
    select * from {{ ref('stg_app_database__locations') }}
),

device_summary as (
    select
        location_id,
        count(*) as total_devices,
        count(case when status = 'online' then 1 end) as active_devices,
        count(case when status = 'online' then 1 end) as online_devices,
        min(device_created_at) as first_device_installed,
        max(device_created_at) as latest_device_installed,
        max(device_created_at) as last_maintenance_performed,
        avg(extract(days from current_timestamp - device_created_at)) as avg_days_since_maintenance
    from {{ ref('stg_app_database__devices') }}
    group by location_id
),

recent_activity as (
    select
        te.location_id,
        count(*) as tap_events_30d,
        count(distinct te.device_id) as active_devices_30d,
        sum(te.volume_ml::float) as total_volume_30d,
        avg(te.flow_rate_ml_per_sec::float) as avg_flow_rate_30d,
        count(case when te.temperature_anomaly or te.pressure_anomaly then 1 end) as quality_issues_30d,
        count(distinct te.event_type) as beverage_types_served_30d
    from {{ ref('stg_app_database__tap_events') }} te
    where te.event_date >= current_date - 30
    group by te.location_id
),

user_activity as (
    select
        l.location_id,
        count(distinct u.user_id) as total_users,
        count(distinct case 
            when u.user_status in ('Active', 'Recent') 
            then u.user_id 
        end) as active_users,
        max(u.user_created_at) as latest_user_login -- Using user_created_at as proxy
    from {{ ref('stg_app_database__locations') }} l
    left join {{ ref('stg_app_database__users') }} u on l.account_id = u.account_id
    group by l.location_id
),

final as (
    select
        -- Core identifiers
        lb.location_id,
        lb.location_key,
        lb.account_id,
        lb.location_name,
        lb.location_type,
        lb.location_category,
        case 
            when ds.total_devices > 0 and ra.tap_events_30d > 0 then 'active'
            when ds.total_devices > 0 then 'inactive'
            else 'no_devices'
        end as location_status,
        case 
            when ds.total_devices > 0 and ds.online_devices > 0 then 'operational'
            when ds.total_devices > 0 then 'offline'
            else 'not_operational'
        end as operational_status,
        
        -- Geographic information
        lb.address as street_address,
        lb.city,
        lb.state as state_code,
        lb.country as country_code,
        concat(lb.address, ', ', lb.city, ', ', lb.state, ' ', lb.zip_code) as full_address,
        lb.region as geographic_market,
        lb.location_category as market_tier,  -- Using location_category instead of non-existent time_zone_category
        
        -- Physical attributes
        0 as seating_capacity, -- Default since column doesn't exist in staging
        null as timezone,  -- Default since column doesn't exist in staging
        
        -- Device infrastructure
        coalesce(ds.total_devices, 0) as total_devices,
        coalesce(ds.active_devices, 0) as active_devices,
        coalesce(ds.online_devices, 0) as online_devices,
        case 
            when ds.total_devices > 0 
            then ds.online_devices::numeric / ds.total_devices
            else 0
        end as device_connectivity_rate,
        ds.first_device_installed,
        ds.latest_device_installed,
        ds.last_maintenance_performed,
        coalesce(ds.avg_days_since_maintenance, 0) as avg_days_since_maintenance,
        
        -- Operational activity (30-day metrics)
        coalesce(ra.tap_events_30d, 0) as tap_events_30d,
        coalesce(ra.active_devices_30d, 0) as active_devices_30d,
        coalesce(ra.total_volume_30d, 0) as total_volume_30d,
        coalesce(ra.avg_flow_rate_30d, 0) as avg_flow_rate_30d,
        coalesce(ra.quality_issues_30d, 0) as quality_issues_30d,
        coalesce(ra.beverage_types_served_30d, 0) as beverage_types_served_30d,
        
        -- User engagement
        coalesce(ua.total_users, 0) as total_users,
        coalesce(ua.active_users, 0) as active_users,
        ua.latest_user_login,
        
        -- Calculated operational metrics
        case 
            when ds.total_devices > 0 and ra.tap_events_30d > 0
            then ra.tap_events_30d::numeric / ds.total_devices
            else 0
        end as avg_events_per_device_30d,
        
        case 
            when ra.tap_events_30d > 0
            then ra.total_volume_30d::numeric / ra.tap_events_30d
            else 0
        end as avg_volume_per_event_30d,
        
        case 
            when ra.tap_events_30d > 0
            then ra.quality_issues_30d::numeric / ra.tap_events_30d
            else 0
        end as quality_issue_rate_30d,
        
        -- Health and performance scoring
        case 
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.95 
                and coalesce(ra.quality_issues_30d, 0) <= ra.tap_events_30d * 0.02
                and ra.tap_events_30d > 100
            then 0.95
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.8 
                and coalesce(ra.quality_issues_30d, 0) <= ra.tap_events_30d * 0.05
                and ra.tap_events_30d > 50
            then 0.8
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.6 
                and ra.tap_events_30d > 0
            then 0.6
            when ds.total_devices > 0
            then 0.3
            else 0.1
        end as operational_health_score,
        
        -- Volume and activity tiers
        case 
            when ra.total_volume_30d >= 100000 then 'high_volume'
            when ra.total_volume_30d >= 50000 then 'medium_volume'
            when ra.total_volume_30d >= 10000 then 'low_volume'
            when ra.total_volume_30d > 0 then 'minimal_volume'
            else 'no_volume'
        end as volume_tier,
        
        case 
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.95 then 'excellent_connectivity'
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.8 then 'good_connectivity'
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) >= 0.6 then 'fair_connectivity'
            when (case when ds.total_devices > 0 then ds.online_devices::numeric / ds.total_devices else 0 end) > 0 then 'poor_connectivity'
            else 'no_connectivity'
        end as connectivity_tier,
        
        -- Lifecycle information
        lb.location_created_at,
        lb.location_updated_at,
        extract(days from current_timestamp - lb.location_created_at) as location_age_days,
        extract(months from age(current_timestamp, lb.location_created_at)) as location_age_months,
        case 
            when extract(days from current_timestamp - lb.location_created_at) <= 30 then 'new'
            when extract(days from current_timestamp - lb.location_created_at) <= 180 then 'establishing'
            when extract(days from current_timestamp - lb.location_created_at) <= 365 then 'mature'
            else 'veteran'
        end as location_lifecycle_stage,
        case 
            when extract(days from current_timestamp - lb.location_created_at) <= 30 then true
            else false
        end as is_newly_opened,
        true as is_customer_facing,  -- Default value as column doesn't exist in staging
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from locations_base lb
    left join device_summary ds on lb.location_id = ds.location_id
    left join recent_activity ra on lb.location_id = ra.location_id
    left join user_activity ua on lb.location_id = ua.location_id
)

select * from final