{{ config(materialized='table') }}

-- Intermediate model: Device performance and health analytics
-- Combines device registration with event data for operational insights
-- Updated to match aligned staging schema

with devices_base as (
    select * from {{ ref('stg_app_database__devices') }}
),

device_events_summary as (
    select
        device_id,
        location_id,
        
        -- 30-day metrics
        count(*) as total_events_30d,
        count(distinct event_date) as active_days_30d,
        count(case when event_category = 'start' then 1 end) as usage_events_30d,
        count(case when event_category = 'error' then 1 end) as alert_events_30d,
        count(case when event_category = 'maintenance' then 1 end) as maintenance_events_30d,
        count(case when temperature_anomaly or pressure_anomaly then 1 end) as quality_issues_30d,
        
        -- Volume and flow metrics
        sum(volume_ml::float) as total_volume_ml_30d,
        avg(flow_rate_ml_per_sec::float) as avg_flow_rate_30d,
        max(flow_rate_ml_per_sec::float) as max_flow_rate_30d,
        min(flow_rate_ml_per_sec::float) as min_flow_rate_30d,
        
        -- Temperature monitoring
        avg(temperature_c::float) as avg_temperature_30d,
        max(temperature_c::float) as max_temperature_30d,
        min(temperature_c::float) as min_temperature_30d,
        count(case when temperature_c::float > 8 then 1 end) as high_temp_events_30d,
        count(case when temperature_c::float < 1 then 1 end) as low_temp_events_30d,
        
        -- Pressure monitoring
        avg(pressure_psi::float) as avg_pressure_30d,
        max(pressure_psi::float) as max_pressure_30d,
        min(pressure_psi::float) as min_pressure_30d,
        count(case when pressure_psi::float > 30 then 1 end) as high_pressure_events_30d,
        count(case when pressure_psi::float < 10 then 1 end) as low_pressure_events_30d,
        
        -- Timing metrics
        max(event_timestamp) as latest_event_timestamp,
        min(event_timestamp) as earliest_event_timestamp,
        
        -- Health scoring calculations
        case 
            when count(distinct event_date) >= 25 then 0.95  -- Active most days
            when count(distinct event_date) >= 20 then 0.85
            when count(distinct event_date) >= 15 then 0.75
            when count(distinct event_date) >= 10 then 0.60
            when count(distinct event_date) >= 5 then 0.40
            when count(*) > 0 then 0.20
            else 0.0
        end as uptime_score,
        
        case 
            when avg(flow_rate_ml_per_sec::float) between 10 and 30 
                and avg(temperature_c::float) between 2 and 6
                and avg(pressure_psi::float) between 10 and 15
            then 0.95
            when avg(flow_rate_ml_per_sec::float) between 5 and 35
                and avg(temperature_c::float) between 0 and 8
                and avg(pressure_psi::float) between 8 and 18
            then 0.80
            when count(*) > 0 then 0.60
            else 0.0
        end as performance_score,
        
        case 
            when count(case when temperature_anomaly or pressure_anomaly then 1 end) = 0 then 1.0
            when count(case when temperature_anomaly or pressure_anomaly then 1 end)::numeric / count(*) <= 0.05 then 0.90
            when count(case when temperature_anomaly or pressure_anomaly then 1 end)::numeric / count(*) <= 0.10 then 0.75
            when count(case when temperature_anomaly or pressure_anomaly then 1 end)::numeric / count(*) <= 0.20 then 0.50
            else 0.25
        end as alert_score
        
    from {{ ref('stg_app_database__tap_events') }}
    where event_date >= current_date - 30
    group by device_id, location_id
),

final as (
    select
        -- Core identifiers
        db.device_id,
        db.device_key,
        db.location_id,
        
        -- Device attributes (using available columns)
        db.device_type,
        db.model,
        db.firmware_version,
        db.serial_number,
        
        -- Installation and maintenance (using available/proxy columns)
        db.install_date as device_installed_date,
        null as installer_name, -- Column doesn't exist
        db.install_date as last_maintenance_date, -- Using install_date as proxy
        db.install_date + interval '90 days' as next_maintenance_due_date, -- Calculated proxy
        90 as maintenance_interval_days, -- Default value
        
        -- Current status (using correct column names)
        db.operational_status as device_status,
        db.network_connectivity as connectivity_status,
        db.device_updated_at as last_heartbeat_at, -- Using updated_at as proxy for heartbeat
        
        -- Event metrics (30-day window)
        coalesce(dhs.total_events_30d, 0) as total_events_30d,
        coalesce(dhs.active_days_30d, 0) as active_days_30d,
        coalesce(dhs.usage_events_30d, 0) as usage_events_30d,
        coalesce(dhs.alert_events_30d, 0) as alert_events_30d,
        coalesce(dhs.maintenance_events_30d, 0) as maintenance_events_30d,
        coalesce(dhs.quality_issues_30d, 0) as quality_issues_30d,
        
        -- Performance metrics
        coalesce(dhs.total_volume_ml_30d, 0) as total_volume_ml_30d,
        dhs.avg_flow_rate_30d,
        dhs.max_flow_rate_30d,
        dhs.min_flow_rate_30d,
        
        -- Environmental metrics
        dhs.avg_temperature_30d,
        dhs.max_temperature_30d,
        dhs.min_temperature_30d,
        coalesce(dhs.high_temp_events_30d, 0) as high_temp_events_30d,
        coalesce(dhs.low_temp_events_30d, 0) as low_temp_events_30d,
        
        dhs.avg_pressure_30d,
        dhs.max_pressure_30d,
        dhs.min_pressure_30d,
        coalesce(dhs.high_pressure_events_30d, 0) as high_pressure_events_30d,
        coalesce(dhs.low_pressure_events_30d, 0) as low_pressure_events_30d,
        
        -- Health scoring
        coalesce(dhs.uptime_score, 0.0) as uptime_score,
        coalesce(dhs.performance_score, 0.0) as performance_score,
        coalesce(dhs.alert_score, 1.0) as alert_score,
        
        -- Overall device health (weighted average)
        round(
            (coalesce(dhs.uptime_score, 0.0) * 0.4 + 
             coalesce(dhs.performance_score, 0.0) * 0.4 + 
             coalesce(dhs.alert_score, 1.0) * 0.2), 3
        ) as overall_device_health_score,
        
        -- Maintenance indicators
        case 
            when db.install_date + interval '90 days' <= current_date then 'overdue'
            when db.install_date + interval '90 days' <= current_date + 7 then 'due_soon'
            when db.install_date + interval '90 days' <= current_date + 30 then 'scheduled'
            else 'not_scheduled'
        end as maintenance_status,
        
        db.days_since_install as days_since_maintenance, -- Using days_since_install as proxy
        
        -- Activity indicators
        dhs.latest_event_timestamp,
        dhs.earliest_event_timestamp,
        
        case 
            when dhs.latest_event_timestamp >= current_date - 1 then 'active_today'
            when dhs.latest_event_timestamp >= current_date - 7 then 'active_this_week'
            when dhs.latest_event_timestamp >= current_date - 30 then 'active_this_month'
            when dhs.latest_event_timestamp is not null then 'inactive'
            else 'never_active'
        end as activity_status,
        
        -- Performance categorization
        case 
            when coalesce(dhs.uptime_score, 0) >= 0.9 
                and coalesce(dhs.performance_score, 0) >= 0.9
                and coalesce(dhs.alert_score, 1) >= 0.9
            then 'excellent'
            when coalesce(dhs.uptime_score, 0) >= 0.7 
                and coalesce(dhs.performance_score, 0) >= 0.7
                and coalesce(dhs.alert_score, 1) >= 0.7
            then 'good'
            when coalesce(dhs.uptime_score, 0) >= 0.5 
                and coalesce(dhs.performance_score, 0) >= 0.5
            then 'fair'
            when dhs.total_events_30d > 0
            then 'poor'
            else 'inactive'
        end as performance_tier,
        
        -- Lifecycle information (calculated as staging doesn't have these)
        db.device_created_at,
        db.device_updated_at,
        db.days_since_install as device_age_days,
        case 
            when db.days_since_install <= 30 then 'new'
            when db.days_since_install <= 180 then 'establishing'
            when db.days_since_install <= 365 then 'mature'
            else 'veteran'
        end as device_lifecycle_stage,
        case 
            when db.days_since_install <= 7 then true
            else false
        end as is_newly_installed,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from devices_base db
    left join device_events_summary dhs on db.device_id = dhs.device_id
)

select * from final