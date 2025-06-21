{{ config(materialized='table') }}

-- Operations Mart: Device Health and Performance Dashboard
-- Real-time operational metrics for device monitoring and maintenance planning  
-- Primary users: Operations managers, field technicians, customer success teams

with device_performance_summary as (
    select
        d.account_id,
        d.location_id,
        d.device_type,
        d.device_status,
        d.location_name,
        null as city,    -- Not available in entity_devices
        null as state,   -- Not available in entity_devices
        null as country, -- Not available in entity_devices
        
        -- Device counts and status
        count(*) as total_devices,
        count(case when d.device_status = 'active' then 1 end) as active_devices,
        count(case when d.connectivity_status = 'online' then 1 end) as online_devices,
        count(case when d.connectivity_status = 'offline' then 1 end) as offline_devices,
        
        -- Performance metrics (30-day)
        sum(d.total_events_30d) as total_events_30d,
        sum(d.total_volume_ml_30d) as total_volume_30d,
        sum(d.quality_issues_30d) as total_quality_issues_30d,
        avg(d.uptime_percentage_30d) as avg_uptime_30d,
        avg(d.performance_score) as avg_performance_score,
        
        -- Maintenance metrics
        min(d.last_maintenance_date) as oldest_maintenance_date,        max(d.last_maintenance_date) as most_recent_maintenance_date,
        avg(d.days_since_maintenance) as avg_days_since_maintenance,
        count(case when d.days_since_maintenance > 90 then 1 end) as overdue_maintenance_devices,
        
        -- Alert status based on health score
        count(case when d.overall_health_score < 20 then 1 end) as critical_alerts,
        count(case when d.overall_health_score >= 20 and d.overall_health_score < 40 then 1 end) as warning_alerts,
        count(case when d.overall_health_score >= 40 and d.overall_health_score < 60 then 1 end) as info_alerts
        
    from {{ ref('entity_devices') }} d
    group by 
        d.account_id, d.location_id, d.device_type, d.device_status,
        d.location_name
),

hourly_performance_trends as (
    select
        device_id,
        date_trunc('day', hour_timestamp) as performance_date,
        
        -- Daily aggregations from hourly data
        sum(total_events) as daily_events,
        sum(total_volume_ml) as daily_volume_ml,
        sum(error_events) as daily_quality_issues,
        avg(avg_flow_rate) as avg_daily_flow_rate,
        
        -- Performance indicators
        count(case when hourly_status = 'error' then 1 end) as error_hours,
        count(case when hourly_status = 'warning' then 1 end) as warning_hours,
        count(case when hourly_status = 'operational' then 1 end) as optimal_hours,        count(case when total_anomalies > 0 then 1 end) as anomaly_hours,
        
        -- Peak performance identification
        max(total_events) as peak_hourly_events,
        max(total_volume_ml) as peak_hourly_volume
        
    from {{ ref('entity_devices_hourly') }}
    where hour_timestamp >= current_date - 7  -- Last week
    group by device_id, date_trunc('day', hour_timestamp)
),

location_operational_health as (
    select
        l.location_id,
        l.location_name,
        l.account_id,
        l.operational_health_score,
        case 
            when l.revenue_per_location >= 10000 then 'enterprise'
            when l.revenue_per_location >= 5000 then 'business'  
            when l.revenue_per_location >= 1000 then 'growth'
            else 'starter'
        end as revenue_tier,
        
        -- Revenue context
        l.revenue_per_location as estimated_monthly_revenue,
        
        -- Operational metrics
        l.total_devices,
        l.active_devices,
        l.tap_events_30d as total_events_30d,        l.total_volume_30d,
        l.support_tickets_open as support_requests_30d,
        
        -- Categorizations
        case 
            when l.total_volume_30d > 10000 then 'high_volume'
            when l.total_volume_30d > 5000 then 'medium_volume'
            else 'low_volume'
        end as volume_tier,
        
        case 
            when l.online_devices::numeric / nullif(l.total_devices, 0) >= 0.95 then 'excellent'
            when l.online_devices::numeric / nullif(l.total_devices, 0) >= 0.85 then 'good'
            when l.online_devices::numeric / nullif(l.total_devices, 0) >= 0.75 then 'fair'
            else 'poor'
        end as connectivity_tier,
        
        case 
            when l.operational_health_score >= 90 then 'top_performer'
            when l.operational_health_score >= 75 then 'good'
            when l.operational_health_score >= 60 then 'average'
            else 'needs_improvement'
        end as performance_category,
        
        case 
            when exists (select 1 from {{ ref('entity_devices') }} d where d.location_id = l.location_id and d.maintenance_status = 'overdue') then 'overdue'
            when exists (select 1 from {{ ref('entity_devices') }} d where d.location_id = l.location_id and d.maintenance_status = 'due_soon') then 'scheduled'
            else 'current'
        end as maintenance_tier,        
        case 
            when l.operational_health_score < 40 then 'high'
            when l.operational_health_score < 60 then 'medium'
            when l.operational_health_score < 80 then 'low'
            else 'minimal'
        end as risk_status,
        
        case 
            when l.total_devices < 5 and l.revenue_per_location >= 5000 then 'infrastructure_upgrade'
            when l.operational_health_score < 60 then 'operational_improvement'
            when l.support_tickets_open > 5 then 'support_intervention'
            else 'standard_service'
        end as opportunity_classification,
        
        -- Customer satisfaction proxy
        case 
            when l.support_tickets_open = 0 and l.operational_health_score >= 80 then 90
            when l.support_tickets_open <= 2 and l.operational_health_score >= 70 then 75
            when l.support_tickets_open <= 5 and l.operational_health_score >= 60 then 60
            else 40
        end as customer_satisfaction_score,
        
        -- Efficiency metrics
        l.tap_events_30d::numeric / nullif(l.seating_capacity, 0) as daily_events_per_seat,
        l.total_volume_30d::numeric / nullif(l.total_devices, 0) as volume_per_device_30d,
        l.tap_events_30d::numeric / nullif(l.active_users, 0) as events_per_active_user_30d,
        l.operational_readiness_score as location_efficiency_score
            from {{ ref('entity_locations') }} l
),

maintenance_planning as (
    select
        d.device_id,
        d.account_id,
        d.location_id,
        d.device_type,
        d.model as model_number,
        d.device_installed_date as installation_date,
        d.last_maintenance_date,
        d.days_since_maintenance,
        
        -- Maintenance priority scoring
        case 
            when d.overall_health_score < 20 then 4
            when d.days_since_maintenance > 120 then 3
            when d.overall_health_score < 40 and d.performance_score < 70 then 3
            when d.days_since_maintenance > 90 then 2
            when d.performance_score < 80 then 2
            else 1
        end as maintenance_priority_score,
        
        case 
            when d.overall_health_score < 20 then 'immediate'
            when d.days_since_maintenance > 120 then 'urgent'
            when d.overall_health_score < 40 and d.performance_score < 70 then 'urgent'
            when d.days_since_maintenance > 90 then 'scheduled'
            when d.performance_score < 80 then 'recommended'            else 'routine'
        end as maintenance_priority,
        
        -- Estimated maintenance window
        case 
            when d.overall_health_score < 20 then 'within_24_hours'
            when d.days_since_maintenance > 120 then 'within_week'
            when d.days_since_maintenance > 90 then 'within_month'
            else 'next_quarter'
        end as recommended_maintenance_window
        
    from {{ ref('entity_devices') }} d
),

final as (
    select
        current_timestamp as report_timestamp,
        
        -- Location and device context
        dps.account_id,
        dps.location_id,
        dps.location_name,
        dps.city,
        dps.state,
        dps.country,
        dps.device_type,
        
        -- Device inventory and status
        dps.total_devices,
        dps.active_devices,        dps.online_devices,
        dps.offline_devices,
        
        case 
            when dps.total_devices > 0 
            then dps.active_devices::numeric / dps.total_devices
            else 0
        end as device_active_rate,
        
        case 
            when dps.active_devices > 0 
            then dps.online_devices::numeric / dps.active_devices
            else 0
        end as connectivity_rate,
        
        -- Performance metrics
        dps.total_events_30d,
        dps.total_volume_30d,
        dps.total_quality_issues_30d,
        dps.avg_uptime_30d,
        dps.avg_performance_score,
        
        case 
            when dps.total_events_30d > 0 
            then dps.total_quality_issues_30d::numeric / dps.total_events_30d
            else 0
        end as quality_issue_rate_30d,
        
        case 
            when dps.active_devices > 0             then dps.total_events_30d::numeric / dps.active_devices
            else 0
        end as avg_events_per_device_30d,
        
        -- Alert status
        dps.critical_alerts,
        dps.warning_alerts,
        dps.info_alerts,
        
        dps.critical_alerts + dps.warning_alerts + dps.info_alerts as total_alerts,
        
        -- Maintenance status
        dps.avg_days_since_maintenance,
        dps.overdue_maintenance_devices,
        
        case 
            when dps.total_devices > 0 
            then dps.overdue_maintenance_devices::numeric / dps.total_devices
            else 0
        end as overdue_maintenance_rate,
        
        -- Location operational health
        loh.operational_health_score,
        loh.volume_tier,
        loh.connectivity_tier,
        loh.performance_category,
        loh.maintenance_tier,
        loh.risk_status,
        loh.opportunity_classification,
        loh.estimated_monthly_revenue,        loh.revenue_tier,
        loh.customer_satisfaction_score,
        loh.support_requests_30d,
        loh.location_efficiency_score,
        
        -- Overall health scoring
        case 
            when dps.critical_alerts > 0 then 0.2
            when dps.online_devices::numeric / nullif(dps.active_devices, 0) < 0.8 then 0.4
            when dps.total_quality_issues_30d::numeric / nullif(dps.total_events_30d, 0) > 0.05 then 0.5
            when dps.avg_uptime_30d < 0.95 then 0.6
            when dps.overdue_maintenance_devices::numeric / nullif(dps.total_devices, 0) > 0.2 then 0.7
            when dps.avg_performance_score >= 90 then 0.95
            when dps.avg_performance_score >= 80 then 0.85
            else 0.75
        end as overall_operational_health,
        
        -- Status classifications
        case 
            when dps.critical_alerts > 0 then 'critical'
            when dps.warning_alerts > 0 or dps.online_devices::numeric / nullif(dps.active_devices, 0) < 0.9 then 'warning'
            when dps.overdue_maintenance_devices::numeric / nullif(dps.total_devices, 0) > 0.1 then 'maintenance_needed'
            when dps.avg_performance_score >= 90 then 'excellent'
            when dps.avg_performance_score >= 80 then 'good'
            else 'needs_attention'
        end as operational_status,
        
        case 
            when loh.risk_status in ('high', 'medium') then 'high_priority'            when dps.critical_alerts > 0 or dps.overdue_maintenance_devices::numeric / nullif(dps.total_devices, 0) > 0.3 then 'high_priority'
            when dps.warning_alerts > 0 or dps.overdue_maintenance_devices::numeric / nullif(dps.total_devices, 0) > 0.1 then 'medium_priority'
            else 'standard_priority'
        end as support_priority,
        
        -- Performance benchmarking
        case 
            when dps.avg_performance_score >= 90 and dps.total_quality_issues_30d::numeric / nullif(dps.total_events_30d, 0) <= 0.02 then 'top_performer'
            when dps.avg_performance_score >= 80 and dps.total_quality_issues_30d::numeric / nullif(dps.total_events_30d, 0) <= 0.05 then 'strong_performer'
            when dps.avg_performance_score >= 70 then 'average_performer'
            when dps.avg_performance_score >= 50 then 'underperformer'
            else 'poor_performer'
        end as performance_tier,
        
        -- Recommendations
        case 
            when dps.critical_alerts > 0 then 'immediate_intervention_required'
            when dps.overdue_maintenance_devices::numeric / nullif(dps.total_devices, 0) > 0.3 then 'schedule_maintenance_team_visit'
            when dps.online_devices::numeric / nullif(dps.active_devices, 0) < 0.8 then 'investigate_connectivity_issues'
            when dps.total_quality_issues_30d::numeric / nullif(dps.total_events_30d, 0) > 0.1 then 'quality_improvement_needed'
            when loh.opportunity_classification = 'infrastructure_upgrade' then 'consider_infrastructure_upgrade'
            when dps.avg_performance_score >= 90 then 'maintain_current_operations'
            else 'optimize_current_setup'
        end as recommended_action,
        
        current_timestamp as _mart_created_at
        
    from device_performance_summary dps
    left join location_operational_health loh on dps.location_id = loh.location_id
)

select * from final