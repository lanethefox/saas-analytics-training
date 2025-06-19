{{ config(materialized='table') }}

-- Operations Device Health Monitoring Dashboard
-- Comprehensive operational monitoring for device fleet management

with device_operational_status as (
    select * from {{ ref('entity_devices') }}
),

hourly_performance_trends as (
    select
        device_id,
        
        -- Performance over last 24 hours
        avg(case when hour_timestamp >= current_timestamp - interval '24 hours' 
            then hourly_performance_score end) as avg_performance_24h,
        count(case when hour_timestamp >= current_timestamp - interval '24 hours' 
            and hourly_status != 'operational' then 1 end) as problematic_hours_24h,
        
        -- Performance over last 7 days
        avg(case when hour_timestamp >= current_timestamp - interval '7 days' 
            then hourly_performance_score end) as avg_performance_7d,
        count(case when hour_timestamp >= current_timestamp - interval '7 days' 
            and alert_level != 'none' then 1 end) as alert_hours_7d,
        
        -- Uptime calculation
        count(case when hour_timestamp >= current_timestamp - interval '24 hours' 
            and uptime_minutes > 0 then 1 end) as uptime_hours_24h,
        count(case when hour_timestamp >= current_timestamp - interval '7 days' 
            and uptime_minutes > 0 then 1 end) as uptime_hours_7d,
        
        -- Volume trends
        sum(case when hour_timestamp >= current_timestamp - interval '24 hours' 
            then total_volume_ml else 0 end) as total_volume_24h,
        sum(case when hour_timestamp >= current_timestamp - interval '7 days' 
            then total_volume_ml else 0 end) as total_volume_7d
        
    from {{ ref('entity_devices_hourly') }}
    group by device_id
),

location_operational_summary as (
    select
        location_id,
        account_id,
        
        -- Device health distribution based on overall_health_score
        count(*) as total_devices,
        count(case when overall_health_score >= 90 then 1 end) as excellent_devices,
        count(case when overall_health_score >= 75 and overall_health_score < 90 then 1 end) as good_devices,
        count(case when overall_health_score >= 60 and overall_health_score < 75 then 1 end) as fair_devices,
        count(case when overall_health_score >= 40 and overall_health_score < 60 then 1 end) as poor_devices,
        count(case when overall_health_score < 40 then 1 end) as critical_devices,
        
        -- Connectivity status
        count(case when connectivity_status = 'online' then 1 end) as online_devices,
        count(case when connectivity_status = 'offline' then 1 end) as offline_devices,
        count(case when connectivity_status = 'intermittent' then 1 end) as intermittent_devices,
        
        -- Activity levels
        count(case when activity_status = 'active' then 1 end) as active_devices,
        count(case when activity_status in ('recent', 'idle') then 1 end) as idle_devices,
        count(case when activity_status in ('stale', 'offline') then 1 end) as inactive_devices,
        
        -- Maintenance requirements
        count(case when maintenance_status = 'overdue' then 1 end) as maintenance_overdue,
        count(case when maintenance_status = 'due_soon' then 1 end) as maintenance_due_soon,
        
        -- Alert priorities based on health score and status
        count(case when overall_health_score < 40 or device_status = 'error' then 1 end) as devices_with_alerts,
        count(case when overall_health_score < 20 then 1 end) as critical_health_devices,
        count(case when connectivity_status = 'offline' then 1 end) as offline_alert_devices,
        count(case when maintenance_status = 'overdue' then 1 end) as overdue_maintenance_devices,
        
        -- Performance metrics
        avg(overall_health_score) as avg_device_health,
        sum(total_events_30d) as location_total_events,
        sum(usage_events_30d) as location_usage_events,
        sum(total_volume_ml_30d) as location_total_volume
        
    from device_operational_status
    group by location_id, account_id
),

customer_operational_health as (
    select
        account_id,
        
        -- Fleet size and health
        sum(total_devices) as fleet_size,
        sum(excellent_devices + good_devices) as healthy_fleet,
        sum(critical_devices + poor_devices) as unhealthy_fleet,
        avg(avg_device_health) as avg_customer_device_health,
        
        -- Connectivity overview
        sum(online_devices) as total_online_devices,
        sum(offline_devices + intermittent_devices) as total_connectivity_issues,
        
        -- Operational priorities
        sum(maintenance_overdue) as total_maintenance_overdue,
        sum(devices_with_alerts) as total_devices_with_alerts,
        sum(critical_health_devices) as total_critical_devices,
        
        -- Activity levels
        sum(location_total_events) as customer_total_events,
        sum(location_usage_events) as customer_usage_events,
        sum(location_total_volume) as customer_total_volume,
        
        -- Location operational status
        count(*) as total_locations,
        count(case when avg_device_health >= 80 then 1 end) as healthy_locations,
        count(case when devices_with_alerts = 0 then 1 end) as locations_no_alerts
        
    from location_operational_summary
    group by account_id
),

operational_priority_scoring as (
    select
        dos.device_id,
        dos.location_id,
        dos.account_id,
        
        -- Critical priority scoring
        case 
            when dos.overall_health_score < 20 then 10
            when dos.connectivity_status = 'offline' then 9
            when dos.maintenance_status = 'overdue' then 8
            when dos.overall_health_score < 40 then 7
            when dos.maintenance_status = 'overdue' then 6
            when dos.connectivity_status = 'offline' then 5
            when dos.overall_health_score < 60 then 4
            when dos.maintenance_status = 'due_soon' then 3
            when dos.overall_health_score < 75 then 2
            else 1
        end as priority_score,
        
        -- Operational impact assessment
        case 
            when dos.overall_health_score < 20 and dos.total_events_30d > 1000 then 'high_impact'
            when dos.overall_health_score < 40 and dos.total_events_30d > 500 then 'medium_impact'
            when dos.overall_health_score < 60 then 'low_impact'
            else 'minimal_impact'
        end as operational_impact,
        
        -- Urgency classification
        case 
            when dos.overall_health_score < 20 then 'critical_4hr'
            when dos.connectivity_status = 'offline' and dos.last_activity_at > current_timestamp - interval '4 hours' then 'urgent_24hr'
            when dos.maintenance_status = 'overdue' and dos.days_since_maintenance > 60 then 'urgent_24hr'
            when dos.overall_health_score < 40 or dos.maintenance_status = 'overdue' then 'high_48hr'
            when dos.maintenance_status = 'due_soon' then 'medium_1week'
            else 'low_routine'
        end as urgency_category
        
    from device_operational_status dos
),

final as (
    select
        -- Device identification
        dos.device_id,
        dos.location_id,
        dos.account_id,
        dos.location_name,
        null as location_city,  -- Not available in entity
        null as location_state, -- Not available in entity
        
        -- Device details
        dos.device_type,
        dos.model as model_number,
        dos.serial_number,
        dos.firmware_version,
        
        -- Current operational status
        dos.device_status,
        dos.connectivity_status,
        dos.activity_status,
        case 
            when dos.overall_health_score >= 90 then 'excellent'
            when dos.overall_health_score >= 75 then 'good'
            when dos.overall_health_score >= 60 then 'fair'
            when dos.overall_health_score >= 40 then 'poor'
            else 'critical'
        end as device_health_grade,
        dos.overall_health_score,
        
        -- Alert and maintenance status
        case
            when dos.overall_health_score < 20 then 'health_critical'
            when dos.connectivity_status = 'offline' then 'device_offline'
            when dos.maintenance_status = 'overdue' then 'maintenance_overdue'
            when dos.overall_health_score < 40 then 'quality_degraded'
            else 'no_alerts'
        end as primary_alert_status,
        dos.maintenance_status,
        dos.days_since_maintenance,
        dos.last_maintenance_date,
        dos.next_maintenance_due_date,
        
        -- Priority and impact assessment
        ops.priority_score,
        ops.operational_impact,
        ops.urgency_category,
        
        -- Performance metrics (30-day)
        dos.total_events_30d,
        dos.usage_events_30d,
        dos.alert_events_30d,
        dos.quality_issues_30d,
        dos.total_volume_ml_30d,
        
        -- Recent performance trends
        coalesce(hpt.avg_performance_24h, 0) as avg_performance_24h,
        coalesce(hpt.avg_performance_7d, 0) as avg_performance_7d,
        coalesce(hpt.problematic_hours_24h, 0) as problematic_hours_24h,
        coalesce(hpt.alert_hours_7d, 0) as alert_hours_7d,
        
        -- Uptime metrics
        case 
            when 24 > 0 then coalesce(hpt.uptime_hours_24h, 0) / 24.0
            else 0
        end as uptime_rate_24h,
        
        case 
            when 168 > 0 then coalesce(hpt.uptime_hours_7d, 0) / 168.0
            else 0
        end as uptime_rate_7d,
        
        -- Volume trends
        coalesce(hpt.total_volume_24h, 0) as total_volume_24h,
        coalesce(hpt.total_volume_7d, 0) as total_volume_7d,
        
        -- Environmental metrics
        dos.avg_temperature_30d,
        dos.max_temperature_30d,
        dos.min_temperature_30d,
        dos.avg_pressure_30d,
        
        -- Utilization and efficiency
        case 
            when dos.total_events_30d > 0 then dos.usage_events_30d::numeric / dos.total_events_30d
            else 0
        end as utilization_rate_per_tap,
        dos.total_events_30d / 30.0 as avg_usage_events_per_day,
        dos.quality_issue_rate_30d as quality_issue_rate,
        
        -- Location context
        los.total_devices as location_total_devices,
        los.online_devices as location_online_devices,
        los.devices_with_alerts as location_devices_with_alerts,
        los.avg_device_health as location_avg_health,
        
        -- Customer fleet context
        coh.fleet_size as customer_fleet_size,
        coh.healthy_fleet as customer_healthy_devices,
        coh.total_maintenance_overdue as customer_maintenance_overdue,
        coh.avg_customer_device_health,
        
        -- Operational recommendations
        case 
            when ops.urgency_category = 'critical_4hr' then 'dispatch_technician_immediately'
            when ops.urgency_category = 'urgent_24hr' then 'schedule_emergency_maintenance'
            when dos.maintenance_status = 'overdue' then 'schedule_maintenance_visit'
            when dos.connectivity_status = 'offline' then 'check_network_connectivity'
            when dos.quality_issue_rate_30d > 0.1 then 'investigate_performance_degradation'
            when dos.overall_health_score < 60 then 'comprehensive_device_inspection'
            else 'continue_monitoring'
        end as recommended_action,
        
        -- SLA compliance
        case 
            when dos.overall_health_score >= 90 then 'exceeds_sla'
            when dos.overall_health_score >= 80 then 'meets_sla'
            when dos.overall_health_score >= 60 then 'below_sla'
            else 'critical_sla_breach'
        end as sla_status,
        
        -- Predictive maintenance indicators
        case 
            when dos.days_since_maintenance > 45 and dos.quality_issue_rate_30d > 0.05 then 'predictive_maintenance_due'
            when dos.alert_events_30d > dos.usage_events_30d * 0.1 then 'increasing_failure_rate'
            when hpt.avg_performance_7d < dos.overall_health_score * 0.8 then 'performance_declining'
            else 'stable_operation'
        end as predictive_maintenance_status,
        
        -- Time-based metrics
        extract(epoch from current_timestamp - dos.last_activity_at) / 3600 as hours_since_last_event,
        dos.device_age_days as days_since_installation,
        
        -- Geographic and timezone considerations
        null as location_timezone,  -- Not available in entity
        
        -- Metadata
        current_timestamp as mart_updated_at
        
    from device_operational_status dos
    left join hourly_performance_trends hpt on dos.device_id = hpt.device_id
    left join location_operational_summary los on dos.location_id = los.location_id
    left join customer_operational_health coh on dos.account_id = coh.account_id
    left join operational_priority_scoring ops on dos.device_id = ops.device_id
)

select * from final
order by 
    case urgency_category
        when 'critical_4hr' then 1
        when 'urgent_24hr' then 2
        when 'high_48hr' then 3
        when 'medium_1week' then 4
        else 5
    end,
    priority_score desc,
    overall_health_score asc