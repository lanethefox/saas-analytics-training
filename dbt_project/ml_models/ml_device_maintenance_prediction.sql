{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- ML Model: Device Maintenance Prediction
-- Predicts device maintenance needs using IoT sensor data and performance patterns
-- Model Type: Classification features for predictive maintenance scheduling

with device_maintenance_features as (
    select
        d.device_id,
        d.device_key,
        d.account_id,
        d.location_id,
        d.device_type,
        d.device_health_score,
        d.performance_score,
        d.uptime_percentage_30d,
        d.events_30d,
        d.events_7d,
        d.last_maintenance_date,
        d.device_created_at,
        d.device_status,
        
        -- Device age and maintenance history
        (current_date - d.device_created_at::date) as device_age_days,
        case 
            when d.last_maintenance_date is null then (current_date - d.device_created_at::date)
            else (current_date - d.last_maintenance_date)
        end as days_since_last_maintenance,
        
        -- Usage intensity metrics
        case 
            when d.events_30d > 0 then d.events_30d::numeric / 30.0 
            else 0 
        end as avg_daily_events,
        
        case 
            when d.events_7d > 0 and d.events_30d > 0 
            then d.events_7d::numeric / (d.events_30d::numeric / 30.0 * 7.0)
            else 0 
        end as recent_usage_trend,
        
        -- Performance degradation indicators
        coalesce(perf_trend.performance_trend_7d, 0) as performance_trend_7d,
        coalesce(perf_trend.health_trend_7d, 0) as health_trend_7d,
        coalesce(perf_trend.uptime_trend_7d, 0) as uptime_trend_7d,
        coalesce(perf_trend.event_volume_trend_7d, 0) as event_volume_trend_7d,
        
        -- Environmental and operational stress
        coalesce(env_metrics.avg_temperature_variance, 0) as avg_temperature_variance,
        coalesce(env_metrics.avg_pressure_variance, 0) as avg_pressure_variance,
        coalesce(env_metrics.quality_issue_rate, 0) as quality_issue_rate,
        coalesce(env_metrics.error_rate, 0) as error_rate,
        
        -- Location context impact
        coalesce(loc_context.location_support_burden, 0) as location_support_burden,
        coalesce(loc_context.location_device_density, 0) as location_device_density,
        coalesce(loc_context.location_operational_stress, 0) as location_operational_stress
        
    from {{ ref('entity_devices') }} d
    
    -- Performance trend analysis from hourly data
    left join (
        select 
            device_id,
            avg(case when hour_timestamp >= current_timestamp - interval '7 days' then hourly_events else null end) -
            avg(case when hour_timestamp between current_timestamp - interval '14 days' and current_timestamp - interval '7 days' then hourly_events else null end) as event_volume_trend_7d,
            
            avg(case when hour_timestamp >= current_timestamp - interval '7 days' then quality_issue_rate else null end) -
            avg(case when hour_timestamp between current_timestamp - interval '14 days' and current_timestamp - interval '7 days' then quality_issue_rate else null end) as performance_trend_7d,
            
            -- Simplified health and uptime trends (using available columns)
            0 as health_trend_7d,  -- Placeholder - would calculate from actual health metrics
            0 as uptime_trend_7d   -- Placeholder - would calculate from actual uptime metrics
        from {{ ref('entity_devices_hourly') }}
        group by device_id
    ) perf_trend on d.device_id = perf_trend.device_id
    
    -- Environmental metrics from tap events
    left join (
        select 
            te.device_id,
            stddev(te.temperature_celsius) as avg_temperature_variance,
            stddev(te.pressure_psi) as avg_pressure_variance,
            count(case when te.quality_flag != 'normal' then 1 end)::numeric / count(*) as quality_issue_rate,
            count(case when te.quality_flag = 'error' then 1 end)::numeric / count(*) as error_rate
        from {{ ref('stg_app_database__tap_events') }} te
        where te.event_date >= current_date - 30
        group by te.device_id
    ) env_metrics on d.device_id = env_metrics.device_id
    
    -- Location operational context
    left join (
        select 
            l.location_id,
            l.support_tickets_open as location_support_burden,
            count(d2.device_id) as location_device_density,
            l.capacity_utilization_pct / 100.0 as location_operational_stress
        from {{ ref('entity_locations') }} l
        left join {{ ref('entity_devices') }} d2 on l.location_id = d2.location_id
        group by l.location_id, l.support_tickets_open, l.capacity_utilization_pct
    ) loc_context on d.location_id = loc_context.location_id
),

maintenance_predictions as (
    select
        device_id,
        device_key,
        account_id,
        location_id,
        device_type,
        device_status,
        
        -- Core device metrics
        device_health_score,
        performance_score,
        uptime_percentage_30d,
        events_30d,
        events_7d,
        device_age_days,
        days_since_last_maintenance,
        
        -- Usage and performance metrics
        avg_daily_events,
        recent_usage_trend,
        performance_trend_7d,
        event_volume_trend_7d,
        
        -- Environmental stress indicators
        avg_temperature_variance,
        avg_pressure_variance,
        quality_issue_rate,
        error_rate,
        
        -- Location context
        location_support_burden,
        location_device_density,
        location_operational_stress,
        
        -- Maintenance urgency scoring
        case 
            when days_since_last_maintenance >= 180 then 1.0
            when days_since_last_maintenance >= 120 then 0.8
            when days_since_last_maintenance >= 90 then 0.6
            when days_since_last_maintenance >= 60 then 0.4
            else 0.2
        end as maintenance_schedule_urgency,
        
        case 
            when device_health_score < 0.4 then 1.0
            when device_health_score < 0.6 then 0.8
            when device_health_score < 0.7 then 0.6
            when device_health_score < 0.8 then 0.4
            else 0.2
        end as health_based_urgency,
        
        case 
            when performance_score < 0.4 then 1.0
            when performance_score < 0.6 then 0.8
            when performance_score < 0.7 then 0.6
            when performance_score < 0.8 then 0.4
            else 0.2
        end as performance_based_urgency,
        
        case 
            when quality_issue_rate >= 0.2 then 1.0
            when quality_issue_rate >= 0.1 then 0.8
            when quality_issue_rate >= 0.05 then 0.6
            when quality_issue_rate >= 0.02 then 0.4
            else 0.2
        end as quality_based_urgency,
        
        -- Composite maintenance probability
        (
            case 
                when days_since_last_maintenance >= 180 then 0.3
                when days_since_last_maintenance >= 120 then 0.2
                when days_since_last_maintenance >= 90 then 0.15
                when days_since_last_maintenance >= 60 then 0.1
                else 0.05
            end +
            case 
                when device_health_score < 0.4 then 0.25
                when device_health_score < 0.6 then 0.2
                when device_health_score < 0.7 then 0.15
                when device_health_score < 0.8 then 0.1
                else 0.05
            end +
            case 
                when performance_score < 0.4 then 0.2
                when performance_score < 0.6 then 0.15
                when performance_score < 0.7 then 0.1
                when performance_score < 0.8 then 0.05
                else 0.02
            end +
            case 
                when quality_issue_rate >= 0.2 then 0.15
                when quality_issue_rate >= 0.1 then 0.1
                when quality_issue_rate >= 0.05 then 0.05
                else 0.02
            end +
            case 
                when uptime_percentage_30d < 80 then 0.1
                when uptime_percentage_30d < 90 then 0.05
                else 0.01
            end
        ) as maintenance_probability,
        
        -- Maintenance urgency classification
        case 
            when days_since_last_maintenance >= 180 or device_health_score < 0.4 or quality_issue_rate >= 0.2 then 'critical'
            when days_since_last_maintenance >= 120 or device_health_score < 0.6 or quality_issue_rate >= 0.1 then 'high'
            when days_since_last_maintenance >= 90 or device_health_score < 0.7 or quality_issue_rate >= 0.05 then 'medium'
            when days_since_last_maintenance >= 60 or device_health_score < 0.8 then 'low'
            else 'routine'
        end as maintenance_urgency,
        
        -- Recommended maintenance timeframe
        case 
            when days_since_last_maintenance >= 180 or device_health_score < 0.4 or quality_issue_rate >= 0.2 then 'within_1_week'
            when days_since_last_maintenance >= 120 or device_health_score < 0.6 or quality_issue_rate >= 0.1 then 'within_2_weeks'
            when days_since_last_maintenance >= 90 or device_health_score < 0.7 or quality_issue_rate >= 0.05 then 'within_1_month'
            when days_since_last_maintenance >= 60 or device_health_score < 0.8 then 'within_2_months'
            else 'routine_schedule'
        end as recommended_timeframe,
        
        -- Maintenance type prediction
        case 
            when quality_issue_rate >= 0.15 or error_rate >= 0.1 then 'corrective_maintenance'
            when avg_temperature_variance > 5 or avg_pressure_variance > 2 then 'calibration_maintenance'
            when days_since_last_maintenance >= 120 or device_health_score < 0.6 then 'preventive_maintenance'
            when uptime_percentage_30d < 90 then 'reliability_maintenance'
            else 'routine_maintenance'
        end as maintenance_type,
        
        -- Failure risk assessment
        case 
            when device_health_score < 0.3 and quality_issue_rate >= 0.2 and days_since_last_maintenance >= 180 then 'high_failure_risk'
            when device_health_score < 0.5 and (quality_issue_rate >= 0.1 or days_since_last_maintenance >= 120) then 'medium_failure_risk'
            when device_health_score < 0.7 and days_since_last_maintenance >= 90 then 'low_failure_risk'
            else 'minimal_failure_risk'
        end as failure_risk_level,
        
        -- Cost-benefit analysis
        case 
            when maintenance_probability >= 0.8 then device_age_days * 2.0  -- High cost of emergency repair
            when maintenance_probability >= 0.6 then device_age_days * 1.5  -- Medium cost
            when maintenance_probability >= 0.4 then device_age_days * 1.2  -- Standard cost
            else device_age_days * 1.0  -- Routine cost
        end as estimated_maintenance_cost,
        
        -- Operational impact assessment
        case 
            when location_device_density <= 2 and maintenance_probability >= 0.6 then 'high_operational_impact'
            when location_device_density <= 5 and maintenance_probability >= 0.4 then 'medium_operational_impact'
            when maintenance_probability >= 0.2 then 'low_operational_impact'
            else 'minimal_operational_impact'
        end as operational_impact,
        
        -- Maintenance scheduling recommendations
        case 
            when maintenance_probability >= 0.8 and location_operational_stress >= 0.8 then 'schedule_immediately_low_peak'
            when maintenance_probability >= 0.6 and location_operational_stress >= 0.6 then 'schedule_within_week_off_peak'
            when maintenance_probability >= 0.4 then 'schedule_within_month'
            else 'include_in_routine_schedule'
        end as scheduling_recommendation,
        
        -- Model metadata
        current_timestamp as prediction_generated_at,
        last_maintenance_date as last_actual_maintenance,
        device_created_at as device_installation_date
        
    from device_maintenance_features
)

select * from maintenance_predictions
order by 
    case maintenance_urgency
        when 'critical' then 1
        when 'high' then 2
        when 'medium' then 3
        when 'low' then 4
        else 5
    end,
    maintenance_probability desc,
    days_since_last_maintenance desc
