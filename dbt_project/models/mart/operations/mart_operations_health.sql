{{ config(materialized='table') }}

-- Operations Performance and Health Mart
-- Comprehensive operational analytics for device management, location performance, and system health
-- Optimized for operations team workflows and real-time monitoring

with device_health_summary as (
    select
        ed.device_id,
        ed.device_key,
        ed.account_id,
        ed.location_id,
        ed.device_type,
        ed.device_status,
        ed.model as model_number,
        ed.firmware_version,
        ed.device_installed_date as installation_date,
        ed.last_maintenance_date,
        
        -- Current performance metrics from hourly data
        coalesce(sum(edh.total_events), 0) as events_24h,
        coalesce(sum(edh.total_volume_ml), 0) as volume_24h,
        coalesce(avg(edh.avg_flow_rate), 0) as avg_flow_rate_24h,
        coalesce(avg(edh.error_rate), 0) as quality_issue_rate_24h,
        coalesce(sum(edh.error_events), 0) as quality_issues_24h,
        coalesce(avg(edh.hourly_performance_score), 0) as performance_score_24h,
        
        -- Calculate device age and maintenance status
        ed.device_age_days,
        ed.days_since_maintenance,
        
        -- Health classification
        case 
            when ed.overall_health_score >= 90 then 'excellent'
            when ed.overall_health_score >= 70 then 'good'
            when ed.overall_health_score >= 50 then 'fair'
            when ed.overall_health_score >= 25 then 'poor'
            else 'critical'
        end as device_health_status,
        
        -- Maintenance priority
        case 
            when ed.maintenance_status = 'overdue' then 'immediate'
            when ed.days_since_maintenance > 90 then 'scheduled'
            when ed.overall_health_score < 50 then 'performance_review'
            else 'routine'
        end as maintenance_priority
        
    from {{ ref('entity_devices') }} ed
    left join {{ ref('entity_devices_hourly') }} edh 
        on ed.device_id = edh.device_id 
        and edh.hour_timestamp >= current_timestamp - interval '24 hours'
    group by 
        ed.device_id, ed.device_key, ed.account_id, ed.location_id,
        ed.device_type, ed.device_status, ed.model, ed.firmware_version,
        ed.device_installed_date, ed.last_maintenance_date, ed.device_age_days,
        ed.days_since_maintenance, ed.overall_health_score, ed.maintenance_status
),

location_operations_summary as (
    select
        el.location_id,
        el.location_key,
        el.account_id,
        el.location_name,
        el.location_type,
        el.location_status,
        el.city,
        el.state_code as state,
        el.country_code as country,
        
        -- Infrastructure metrics
        el.total_devices,
        el.active_devices,
        el.online_devices,
        el.device_connectivity_rate,
        
        -- Activity metrics
        el.tap_events_30d,
        el.active_devices_30d,
        el.total_volume_30d,
        el.quality_issues_30d,
        el.quality_issue_rate_30d,
        
        -- User metrics
        el.total_users,
        el.active_users,
        el.latest_user_login,
        
        -- Performance scores
        el.operational_health_score,
        el.operational_readiness_score as location_efficiency_score,
        case 
            when el.support_tickets_open = 0 and el.operational_health_score >= 80 then 90
            when el.support_tickets_open <= 2 and el.operational_health_score >= 70 then 75
            when el.support_tickets_open <= 5 and el.operational_health_score >= 60 then 60
            else 40
        end as customer_satisfaction_score,
        
        -- Classifications
        case 
            when el.total_volume_30d > 10000 then 'high_volume'
            when el.total_volume_30d > 5000 then 'medium_volume'
            else 'low_volume'
        end as volume_tier,
        
        case 
            when el.device_connectivity_rate >= 95 then 'excellent'
            when el.device_connectivity_rate >= 85 then 'good'
            when el.device_connectivity_rate >= 75 then 'fair'
            else 'poor'
        end as connectivity_tier,
        
        case 
            when el.operational_health_score >= 90 then 'top_performer'
            when el.operational_health_score >= 75 then 'good'
            when el.operational_health_score >= 60 then 'average'
            else 'needs_improvement'
        end as performance_category,
        
        case 
            when exists (select 1 from {{ ref('entity_devices') }} d where d.location_id = el.location_id and d.maintenance_status = 'overdue') then 'overdue'
            when exists (select 1 from {{ ref('entity_devices') }} d where d.location_id = el.location_id and d.maintenance_status = 'due_soon') then 'scheduled'
            else 'current'
        end as maintenance_tier,
        
        case 
            when el.operational_health_score < 40 then 'high'
            when el.operational_health_score < 60 then 'medium'
            when el.operational_health_score < 80 then 'low'
            else 'minimal'
        end as risk_status,
        
        case 
            when el.total_devices < 5 and el.revenue_per_location >= 5000 then 'infrastructure_upgrade'
            when el.operational_health_score < 60 then 'operational_improvement'
            when el.support_tickets_open > 5 then 'support_intervention'
            else 'standard_service'
        end as opportunity_classification,
        
        -- Revenue metrics
        el.revenue_per_location as estimated_monthly_revenue,
        case 
            when el.revenue_per_location >= 10000 then 'enterprise'
            when el.revenue_per_location >= 5000 then 'business'
            when el.revenue_per_location >= 1000 then 'growth'
            else 'starter'
        end as revenue_tier,
        
        -- Device health rollup
        count(distinct dhs.device_id) as total_monitored_devices,
        count(distinct case when dhs.device_health_status = 'excellent' then dhs.device_id end) as excellent_devices,
        count(distinct case when dhs.device_health_status = 'good' then dhs.device_id end) as good_devices,
        count(distinct case when dhs.device_health_status = 'fair' then dhs.device_id end) as fair_devices,
        count(distinct case when dhs.device_health_status = 'poor' then dhs.device_id end) as poor_devices,
        count(distinct case when dhs.device_health_status = 'critical' then dhs.device_id end) as critical_devices,
        count(distinct case when dhs.maintenance_priority = 'immediate' then dhs.device_id end) as immediate_maintenance_devices
        
    from {{ ref('entity_locations') }} el
    left join device_health_summary dhs on el.location_id = dhs.location_id
    group by 
        el.location_id, el.location_key, el.account_id, el.location_name,
        el.location_type, el.location_status, el.city, el.state_code, el.country_code,
        el.total_devices, el.active_devices, el.online_devices, el.device_connectivity_rate,
        el.tap_events_30d, el.active_devices_30d, el.total_volume_30d, el.quality_issues_30d, el.quality_issue_rate_30d,
        el.total_users, el.active_users, el.latest_user_login,
        el.operational_health_score, el.operational_readiness_score, el.support_tickets_open,
        el.revenue_per_location
),

account_operations_rollup as (
    select
        los.account_id,
        count(distinct los.location_id) as total_locations,
        count(distinct case when los.location_status = 'active' then los.location_id end) as active_locations,
        count(distinct case when los.risk_status = 'high' then los.location_id end) as at_risk_locations,
        
        sum(los.total_devices) as total_devices_across_locations,
        sum(los.active_devices) as active_devices_across_locations,
        sum(los.online_devices) as online_devices_across_locations,
        
        sum(los.tap_events_30d) as total_tap_events_30d,
        sum(los.total_volume_30d) as total_volume_30d,
        sum(los.quality_issues_30d) as total_quality_issues_30d,
        
        avg(los.operational_health_score) as avg_operational_health_score,
        avg(los.location_efficiency_score) as avg_location_efficiency_score,
        avg(los.customer_satisfaction_score) as avg_customer_satisfaction_score,
        
        sum(los.estimated_monthly_revenue) as total_estimated_revenue,
        
        -- Device health across account
        sum(los.excellent_devices) as excellent_devices_total,
        sum(los.good_devices) as good_devices_total,
        sum(los.fair_devices) as fair_devices_total,
        sum(los.poor_devices) as poor_devices_total,
        sum(los.critical_devices) as critical_devices_total,
        sum(los.immediate_maintenance_devices) as immediate_maintenance_devices_total
        
    from location_operations_summary los
    group by los.account_id
),

final as (
    select
        -- Device Health Details
        'device_health' as mart_section,
        dhs.device_id::varchar,
        dhs.device_key,
        dhs.account_id,
        dhs.location_id::varchar,
        null::varchar as location_name,
        dhs.device_type,
        dhs.device_status,
        dhs.model_number,
        dhs.firmware_version,
        dhs.installation_date,
        dhs.last_maintenance_date,
        dhs.device_age_days,
        dhs.days_since_maintenance,
        dhs.events_24h,
        dhs.volume_24h,
        dhs.avg_flow_rate_24h,
        dhs.quality_issue_rate_24h,
        dhs.quality_issues_24h,
        dhs.performance_score_24h,
        dhs.device_health_status,
        dhs.maintenance_priority,
        
        -- Null fields for location/account sections
        null::varchar as location_type,
        null::varchar as location_status,
        null::varchar as city,
        null::varchar as state,
        null::varchar as country,
        null::bigint as total_devices,
        null::bigint as active_devices,
        null::bigint as online_devices,
        null::numeric as device_connectivity_rate,
        null::bigint as tap_events_30d,
        null::bigint as active_devices_30d,
        null::numeric as total_volume_30d,
        null::bigint as quality_issues_30d,
        null::numeric as quality_issue_rate_30d,
        null::bigint as total_users,
        null::bigint as active_users,
        null::timestamp as latest_user_login,
        null::numeric as operational_health_score,
        null::numeric as location_efficiency_score,
        null::numeric as customer_satisfaction_score,
        null::varchar as volume_tier,
        null::varchar as connectivity_tier,
        null::varchar as performance_category,
        null::varchar as maintenance_tier,
        null::varchar as risk_status,
        null::varchar as opportunity_classification,
        null::numeric as estimated_monthly_revenue,
        null::varchar as revenue_tier,
        null::bigint as total_locations,
        null::bigint as active_locations,
        null::bigint as at_risk_locations,
        null::bigint as total_devices_across_locations,
        null::bigint as active_devices_across_locations,
        null::bigint as online_devices_across_locations,
        null::bigint as total_tap_events_30d,
        null::numeric as total_volume_30d_account,
        null::bigint as total_quality_issues_30d,
        null::numeric as avg_operational_health_score,
        null::numeric as avg_location_efficiency_score,
        null::numeric as avg_customer_satisfaction_score,
        null::numeric as total_estimated_revenue,
        null::bigint as excellent_devices_total,
        null::bigint as good_devices_total,
        null::bigint as fair_devices_total,
        null::bigint as poor_devices_total,
        null::bigint as critical_devices_total,
        null::bigint as immediate_maintenance_devices_total
        
    from device_health_summary dhs
    
    union all
    
    select
        -- Location Operations Summary
        'location_operations' as mart_section,
        null::varchar as device_id,
        null::varchar as device_key,
        los.account_id,
        los.location_id::varchar,
        los.location_name,
        null::varchar as device_type,
        null::varchar as device_status,
        null::varchar as model_number,
        null::varchar as firmware_version,
        null::date as installation_date,
        null::date as last_maintenance_date,
        null::bigint as device_age_days,
        null::bigint as days_since_maintenance,
        null::bigint as events_24h,
        null::numeric as volume_24h,
        null::numeric as avg_flow_rate_24h,
        null::numeric as quality_issue_rate_24h,
        null::bigint as quality_issues_24h,
        null::numeric as performance_score_24h,
        null::varchar as device_health_status,
        null::varchar as maintenance_priority,
        los.location_type,
        los.location_status,
        los.city,
        los.state,
        los.country,
        los.total_devices,
        los.active_devices,
        los.online_devices,
        los.device_connectivity_rate,
        los.tap_events_30d,
        los.active_devices_30d,
        los.total_volume_30d,
        los.quality_issues_30d,
        los.quality_issue_rate_30d,
        los.total_users,
        los.active_users,
        los.latest_user_login,
        los.operational_health_score,
        los.location_efficiency_score,
        los.customer_satisfaction_score,
        los.volume_tier,
        los.connectivity_tier,
        los.performance_category,
        los.maintenance_tier,
        los.risk_status,
        los.opportunity_classification,
        los.estimated_monthly_revenue,
        los.revenue_tier,
        null::bigint as total_locations,
        null::bigint as active_locations,
        null::bigint as at_risk_locations,
        null::bigint as total_devices_across_locations,
        null::bigint as active_devices_across_locations,
        null::bigint as online_devices_across_locations,
        null::bigint as total_tap_events_30d,
        null::numeric as total_volume_30d_account,
        null::bigint as total_quality_issues_30d,
        null::numeric as avg_operational_health_score,
        null::numeric as avg_location_efficiency_score,
        null::numeric as avg_customer_satisfaction_score,
        null::numeric as total_estimated_revenue,
        null::bigint as excellent_devices_total,
        null::bigint as good_devices_total,
        null::bigint as fair_devices_total,
        null::bigint as poor_devices_total,
        null::bigint as critical_devices_total,
        null::bigint as immediate_maintenance_devices_total
        
    from location_operations_summary los
    
    union all
    
    select
        -- Account Operations Rollup
        'account_operations' as mart_section,
        null::varchar as device_id,
        null::varchar as device_key,
        aor.account_id,
        null::varchar as location_id,
        null::varchar as location_name,
        null::varchar as device_type,
        null::varchar as device_status,
        null::varchar as model_number,
        null::varchar as firmware_version,
        null::date as installation_date,
        null::date as last_maintenance_date,
        null::bigint as device_age_days,
        null::bigint as days_since_maintenance,
        null::bigint as events_24h,
        null::numeric as volume_24h,
        null::numeric as avg_flow_rate_24h,
        null::numeric as quality_issue_rate_24h,
        null::bigint as quality_issues_24h,
        null::numeric as performance_score_24h,
        null::varchar as device_health_status,
        null::varchar as maintenance_priority,
        null::varchar as location_type,
        null::varchar as location_status,
        null::varchar as city,
        null::varchar as state,
        null::varchar as country,
        null::bigint as total_devices,
        null::bigint as active_devices,
        null::bigint as online_devices,
        null::numeric as device_connectivity_rate,
        null::bigint as tap_events_30d,
        null::bigint as active_devices_30d,
        null::numeric as total_volume_30d,
        null::bigint as quality_issues_30d,
        null::numeric as quality_issue_rate_30d,
        null::bigint as total_users,
        null::bigint as active_users,
        null::timestamp as latest_user_login,
        null::numeric as operational_health_score,
        null::numeric as location_efficiency_score,
        null::numeric as customer_satisfaction_score,
        null::varchar as volume_tier,
        null::varchar as connectivity_tier,
        null::varchar as performance_category,
        null::varchar as maintenance_tier,
        null::varchar as risk_status,
        null::varchar as opportunity_classification,
        null::numeric as estimated_monthly_revenue,
        null::varchar as revenue_tier,
        aor.total_locations,
        aor.active_locations,
        aor.at_risk_locations,
        aor.total_devices_across_locations,
        aor.active_devices_across_locations,
        aor.online_devices_across_locations,
        aor.total_tap_events_30d,
        aor.total_volume_30d as total_volume_30d_account,
        aor.total_quality_issues_30d,
        aor.avg_operational_health_score,
        aor.avg_location_efficiency_score,
        aor.avg_customer_satisfaction_score,
        aor.total_estimated_revenue,
        aor.excellent_devices_total,
        aor.good_devices_total,
        aor.fair_devices_total,
        aor.poor_devices_total,
        aor.critical_devices_total,
        aor.immediate_maintenance_devices_total
        
    from account_operations_rollup aor
)

select * from final