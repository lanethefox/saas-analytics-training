{{ config(
    materialized='table',
    indexes=[
        {'columns': ['device_id'], 'unique': True},
        {'columns': ['location_id']},
        {'columns': ['operational_status']},
        {'columns': ['overall_health_score']},
        {'columns': ['performance_tier']}
    ]
) }}

-- Entity: Devices (Atomic Instance)
-- Current-state device view with real-time health metrics and operational insights
-- Primary use cases: Device fleet management, operational monitoring, maintenance scheduling

with devices_health as (
    select * from {{ ref('int_devices__performance_health') }}
),

locations as (
    select 
        location_id,
        location_name,
        account_id
    from {{ ref('stg_app_database__locations') }}
),

final as (
    select
        -- Primary identifiers
        dh.device_id,
        dh.device_key,
        dh.location_id,
        loc.account_id,
        
        -- Device attributes
        dh.device_type,
        dh.model,
        dh.firmware_version,
        dh.serial_number,
        
        -- Device categorization
        case 
            when dh.device_type = 'tap_controller' then 'primary'
            when dh.device_type = 'sensor' then 'secondary'
            when dh.device_type = 'gateway' then 'infrastructure'
            else 'other'
        end as device_priority,
        
        -- Installation and maintenance
        dh.device_installed_date,
        dh.last_maintenance_date,
        dh.next_maintenance_due_date,
        dh.maintenance_interval_days,
        dh.maintenance_status,
        dh.days_since_maintenance,
        
        -- Current operational status
        dh.device_status,
        dh.connectivity_status,
        dh.device_status as operational_status,
        dh.last_heartbeat_at,
        dh.activity_status,
        
        -- Real-time health metrics
        dh.overall_device_health_score as overall_health_score,
        dh.uptime_score,
        dh.performance_score,
        dh.alert_score,
        dh.performance_tier,
        
        -- 30-day operational metrics
        dh.total_events_30d,
        dh.active_days_30d,
        dh.usage_events_30d,
        dh.alert_events_30d,
        dh.maintenance_events_30d,
        dh.quality_issues_30d,
        
        -- 30-day performance metrics
        dh.total_volume_ml_30d,
        round((dh.total_volume_ml_30d / 1000.0)::numeric, 2) as total_volume_liters_30d,
        dh.avg_flow_rate_30d,
        dh.max_flow_rate_30d,
        dh.min_flow_rate_30d,
        
        -- 30-day environmental metrics
        dh.avg_temperature_30d,
        dh.max_temperature_30d,
        dh.min_temperature_30d,
        dh.high_temp_events_30d,
        dh.low_temp_events_30d,
        
        dh.avg_pressure_30d,
        dh.max_pressure_30d,
        dh.min_pressure_30d,
        dh.high_pressure_events_30d,
        dh.low_pressure_events_30d,
        
        -- Uptime calculations
        case 
            when dh.active_days_30d > 0 then 
                round(dh.active_days_30d::numeric / 30.0, 3)
            else 0
        end as uptime_percentage_30d,
        
        -- Alert rate calculations
        case 
            when dh.total_events_30d > 0 then 
                round(dh.alert_events_30d::numeric / dh.total_events_30d::numeric, 4)
            else 0
        end as alert_rate_30d,
        
        -- Quality issue rate
        case 
            when dh.total_events_30d > 0 then 
                round(dh.quality_issues_30d::numeric / dh.total_events_30d::numeric, 4)
            else 0
        end as quality_issue_rate_30d,
        
        -- Predictive maintenance indicators
        case 
            when (case when dh.total_events_30d > 0 then round(dh.alert_events_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.1 
                or (case when dh.total_events_30d > 0 then round(dh.quality_issues_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.15 then 'high'
            when (case when dh.total_events_30d > 0 then round(dh.alert_events_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.05 
                or (case when dh.total_events_30d > 0 then round(dh.quality_issues_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.08 then 'medium'
            when (case when dh.total_events_30d > 0 then round(dh.alert_events_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.02 
                or (case when dh.total_events_30d > 0 then round(dh.quality_issues_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.03 then 'low'
            else 'minimal'
        end as maintenance_risk_level,
        
        case 
            when dh.overall_device_health_score < 0.5 then true
            when (case when dh.total_events_30d > 0 then round(dh.alert_events_30d::numeric / dh.total_events_30d::numeric, 4) else 0 end) > 0.15 then true
            when dh.maintenance_status = 'overdue' then true
            else false
        end as requires_immediate_attention,
        
        -- Device lifecycle information
        dh.device_lifecycle_stage,
        dh.device_age_days,
        dh.is_newly_installed,
        
        -- Device lifetime metrics (calculated)
        case 
            when dh.device_age_days > 0 then
                round(dh.total_volume_ml_30d::numeric * 365.25 / 30.0 / dh.device_age_days, 2)
            else null
        end as avg_daily_volume_ml_lifetime,
        
        -- Operational insights
        case 
            when dh.device_status = 'operational' and dh.overall_device_health_score >= 0.8 then 'healthy'
            when dh.device_status = 'operational' and dh.overall_device_health_score >= 0.6 then 'degraded'
            when dh.device_status = 'operational' and dh.overall_device_health_score < 0.6 then 'unhealthy'
            when dh.device_status = 'maintenance' then 'maintenance'
            when dh.device_status = 'non_operational' then 'offline'
            else 'unknown'
        end as device_health_status,
        
        -- Revenue impact estimation (based on volume)
        round((dh.total_volume_ml_30d * 0.001 * 5.0)::numeric, 2) as estimated_revenue_30d, -- $5 per liter
        
        -- Location context
        loc.location_name,
        
        -- Timestamps
        dh.device_created_at,
        dh.device_updated_at,
        dh.latest_event_timestamp as last_activity_at,
        current_timestamp as _entity_updated_at
        
    from devices_health dh
    left join locations loc on dh.location_id = loc.location_id
)

select * from final