{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Mart: Operations Performance Analytics
-- Comprehensive operational performance monitoring and optimization
-- Primary stakeholders: Operations team, facilities management, business operations

with device_performance_base as (
    select
        d.device_id,
        d.device_key,
        d.account_id,
        d.location_id,
        d.device_type,
        d.device_status,
        d.overall_health_score as device_health_score,
        d.uptime_percentage_30d,
        d.total_events_30d as events_30d,
        d.active_days_30d * (d.total_events_30d / 30.0) as events_7d, -- Approximation
        d.last_maintenance_date,
        d.device_created_at,
        
        -- Device performance classification
        case 
            when d.overall_health_score >= 90 and d.uptime_percentage_30d >= 95 then 'excellent_performance'
            when d.overall_health_score >= 70 and d.uptime_percentage_30d >= 90 then 'good_performance'
            when d.overall_health_score >= 50 and d.uptime_percentage_30d >= 80 then 'fair_performance'
            else 'poor_performance'
        end as device_performance_tier,
        
        -- Maintenance urgency
        case 
            when d.last_maintenance_date is null then 'never_maintained'
            when d.last_maintenance_date < current_date - 90 then 'due_for_maintenance'
            when d.last_maintenance_date < current_date - 60 then 'maintenance_recommended'
            else 'recently_maintained'
        end as maintenance_status,
        
        -- Activity level classification
        case 
            when d.total_events_30d >= 1000 then 'high_activity'
            when d.total_events_30d >= 500 then 'medium_activity'
            when d.total_events_30d >= 100 then 'low_activity'
            when d.total_events_30d > 0 then 'minimal_activity'
            else 'inactive'
        end as device_activity_level
        
    from {{ ref('entity_devices') }} d
),

location_performance_base as (
    select
        l.location_id,
        l.location_key,
        l.account_id,
        l.location_name,
        l.location_status,
        l.city,
        l.state_code as state_province,
        l.country_code as country,
        l.active_devices,
        l.tap_events_30d as total_events_30d,
        l.operational_health_score as location_health_score,
        l.operational_readiness_score as operational_efficiency_score,
        case 
            when l.seating_capacity > 0 then (l.active_devices::numeric / l.seating_capacity * 100)
            else 0
        end as capacity_utilization_pct,
        l.support_tickets_open,
        l.location_created_at,
        
        -- Location performance classification
        case 
            when l.operational_health_score >= 90 and l.operational_readiness_score >= 80 then 'exceptional_location'
            when l.operational_health_score >= 70 and l.operational_readiness_score >= 60 then 'high_performing_location'
            when l.operational_health_score >= 50 and l.operational_readiness_score >= 40 then 'average_location'
            else 'underperforming_location'
        end as location_performance_tier,
        
        -- Capacity optimization status
        case 
            when l.seating_capacity > 0 and (l.active_devices::numeric / l.seating_capacity * 100) >= 90 then 'over_capacity'
            when l.seating_capacity > 0 and (l.active_devices::numeric / l.seating_capacity * 100) >= 75 then 'optimal_capacity'
            when l.seating_capacity > 0 and (l.active_devices::numeric / l.seating_capacity * 100) >= 50 then 'underutilized'
            when l.seating_capacity > 0 and (l.active_devices::numeric / l.seating_capacity * 100) >= 25 then 'significantly_underutilized'
            else 'severely_underutilized'
        end as capacity_status,
        
        -- Support burden classification
        case 
            when l.support_tickets_open >= 5 then 'high_support_burden'
            when l.support_tickets_open >= 3 then 'medium_support_burden'
            when l.support_tickets_open >= 1 then 'low_support_burden'
            else 'no_support_issues'
        end as support_burden_level
        
    from {{ ref('entity_locations') }} l
),

account_operational_metrics as (
    select
        c.account_id,
        c.company_name as account_name,
        c.total_locations,
        
        -- Device aggregations
        count(distinct dpb.device_id) as total_devices,
        count(case when dpb.device_status = 'active' then dpb.device_id end) as active_devices,
        count(case when dpb.device_performance_tier = 'excellent_performance' then dpb.device_id end) as excellent_devices,
        count(case when dpb.device_performance_tier = 'poor_performance' then dpb.device_id end) as poor_performing_devices,
        count(case when dpb.maintenance_status in ('overdue_maintenance', 'never_maintained') then dpb.device_id end) as devices_needing_maintenance,
        sum(dpb.events_30d) as total_device_events_30d,
        avg(dpb.device_health_score) as avg_device_health_score,
        avg(dpb.uptime_percentage_30d) as avg_device_uptime,
        
        -- Location aggregations
        count(distinct lpb.location_id) as total_locations_detailed,
        count(case when lpb.location_status = 'active' then lpb.location_id end) as active_locations,
        count(case when lpb.location_performance_tier = 'exceptional_location' then lpb.location_id end) as exceptional_locations,
        count(case when lpb.location_performance_tier = 'underperforming_location' then lpb.location_id end) as underperforming_locations,
        count(case when lpb.capacity_status = 'over_capacity' then lpb.location_id end) as over_capacity_locations,
        count(case when lpb.support_burden_level = 'high_support_burden' then lpb.location_id end) as high_support_locations,
        sum(lpb.support_tickets_open) as total_support_tickets,
        avg(lpb.location_health_score) as avg_location_health_score,
        avg(lpb.operational_efficiency_score) as avg_operational_efficiency,
        avg(lpb.capacity_utilization_pct) as avg_capacity_utilization,
        
        -- Geographic distribution
        count(distinct lpb.city) as cities_served,
        count(distinct lpb.state_province) as states_served,
        count(distinct lpb.country) as countries_served
        
    from {{ ref('entity_customers') }} c
    left join device_performance_base dpb on c.account_id::varchar = dpb.account_id::varchar
    left join location_performance_base lpb on c.account_id::varchar = lpb.account_id::varchar
    group by c.account_id, c.company_name, c.total_locations
),

operations_performance_final as (
    select
        c.account_id,
        c.account_id as account_key,  -- Use account_id as key
        c.company_name as account_name,
        c.customer_tier as account_type,
        c.customer_status as subscription_status,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        
        -- Customer classification
        case 
            when c.monthly_recurring_revenue >= 1000 then 'enterprise_operations'
            when c.monthly_recurring_revenue >= 500 then 'mid_market_operations'
            when c.monthly_recurring_revenue >= 100 then 'smb_operations'
            else 'startup_operations'
        end as operations_segment,
        
        -- Operational scale metrics
        aom.total_devices,
        aom.active_devices,
        aom.total_locations_detailed as total_locations,
        aom.active_locations,
        aom.cities_served,
        aom.states_served,
        aom.countries_served,
        
        -- Device performance metrics
        aom.excellent_devices,
        aom.poor_performing_devices,
        aom.devices_needing_maintenance,
        aom.total_device_events_30d,
        aom.avg_device_health_score,
        aom.avg_device_uptime,
        
        -- Location performance metrics
        aom.exceptional_locations,
        aom.underperforming_locations,
        aom.over_capacity_locations,
        aom.high_support_locations,
        aom.total_support_tickets,
        aom.avg_location_health_score,
        aom.avg_operational_efficiency,
        aom.avg_capacity_utilization,
        
        -- Operational health scoring
        case 
            when aom.avg_device_health_score >= 80 and aom.avg_location_health_score >= 80 and aom.total_support_tickets <= 2 then 'excellent_operations'
            when aom.avg_device_health_score >= 60 and aom.avg_location_health_score >= 60 and aom.total_support_tickets <= 5 then 'good_operations'
            when aom.avg_device_health_score >= 40 and aom.avg_location_health_score >= 40 then 'fair_operations'
            else 'poor_operations'
        end as overall_operational_health,
        
        -- Device fleet efficiency
        case 
            when aom.total_devices > 0 and aom.active_devices::numeric / aom.total_devices >= 0.9 then 'highly_efficient_fleet'
            when aom.total_devices > 0 and aom.active_devices::numeric / aom.total_devices >= 0.8 then 'efficient_fleet'
            when aom.total_devices > 0 and aom.active_devices::numeric / aom.total_devices >= 0.6 then 'moderately_efficient_fleet'
            else 'inefficient_fleet'
        end as fleet_efficiency_status,
        
        -- Maintenance urgency assessment
        case 
            when aom.devices_needing_maintenance >= 5 then 'critical_maintenance_backlog'
            when aom.devices_needing_maintenance >= 3 then 'significant_maintenance_needed'
            when aom.devices_needing_maintenance >= 1 then 'routine_maintenance_due'
            else 'maintenance_up_to_date'
        end as maintenance_urgency,
        
        -- Capacity optimization opportunities
        case 
            when aom.over_capacity_locations >= 2 then 'expansion_opportunities'
            when aom.over_capacity_locations >= 1 then 'localized_expansion_needed'
            when aom.avg_capacity_utilization < 50 then 'optimization_opportunities'
            else 'capacity_well_managed'
        end as capacity_optimization_status,
        
        -- Support burden assessment
        case
            when aom.total_support_tickets >= 10 then 'critical_support_burden'
            when aom.total_support_tickets >= 5 then 'high_support_burden'
            when aom.total_support_tickets >= 2 then 'moderate_support_burden'
            when aom.total_support_tickets >= 1 then 'low_support_burden'
            else 'minimal_support_needs'
        end as support_burden_assessment,
        
        -- Geographic complexity
        case 
            when aom.countries_served > 1 then 'international_operations'
            when aom.states_served > 3 then 'multi_state_operations'
            when aom.cities_served > 1 then 'multi_city_operations'
            else 'localized_operations'
        end as geographic_complexity,
        
        -- Operations maturity assessment
        case 
            when aom.total_devices >= 20 and aom.total_locations >= 10 and aom.avg_operational_efficiency >= 70 then 'mature_operations'
            when aom.total_devices >= 10 and aom.total_locations >= 5 and aom.avg_operational_efficiency >= 50 then 'developing_operations'
            when aom.total_devices >= 5 and aom.total_locations >= 2 then 'emerging_operations'
            else 'startup_operations'
        end as operations_maturity_level,
        
        -- Operational KPIs
        case 
            when aom.total_devices > 0 
            then aom.total_device_events_30d::numeric / aom.total_devices
            else 0
        end as avg_events_per_device,
        
        case 
            when aom.total_locations > 0 
            then aom.total_device_events_30d::numeric / aom.total_locations
            else 0
        end as avg_events_per_location,
        
        case 
            when aom.total_devices > 0 
            then aom.devices_needing_maintenance::numeric / aom.total_devices
            else 0
        end as maintenance_backlog_ratio,
        
        case 
            when aom.total_locations > 0 
            then aom.total_support_tickets::numeric / aom.total_locations
            else 0
        end as support_tickets_per_location,
        
        -- Composite operational score (0-100)
        (
            coalesce(aom.avg_device_health_score / 100.0, 0) * 30 +
            coalesce(aom.avg_location_health_score / 100.0, 0) * 25 +
            coalesce(aom.avg_operational_efficiency / 100.0, 0) * 20 +
            coalesce(aom.avg_device_uptime / 100.0, 0) * 15 +
            case when aom.total_support_tickets = 0 then 10 
                 when aom.total_locations > 0 then greatest(0, 10 - (aom.total_support_tickets::numeric / aom.total_locations * 10))
                 else 0 end
        ) as composite_operational_score,
        
        -- Action prioritization
        case 
            when aom.devices_needing_maintenance >= 3 and aom.total_support_tickets >= 5 then 'immediate_action_required'
            when aom.poor_performing_devices >= 2 or aom.underperforming_locations >= 1 then 'proactive_intervention_needed'
            when aom.avg_capacity_utilization < 50 then 'optimization_opportunity'
            else 'operations_stable'
        end as operations_priority,
        
        -- Operational recommendations
        case 
            when aom.devices_needing_maintenance >= aom.total_devices * 0.3 then 'implement_preventive_maintenance_program'
            when aom.total_support_tickets >= aom.total_locations * 2 then 'improve_operational_training'
            when aom.avg_capacity_utilization >= 85 then 'consider_capacity_expansion'
            when aom.avg_capacity_utilization <= 40 then 'optimize_resource_allocation'
            when aom.poor_performing_devices >= 2 then 'device_optimization_program'
            else 'maintain_current_operations'
        end as operational_recommendation,
        
        -- Customer success alignment
        case 
            when aom.avg_device_health_score >= 80 and aom.avg_location_health_score >= 80 then 'operations_supporting_success'
            when aom.avg_device_health_score >= 60 and aom.avg_location_health_score >= 60 then 'operations_neutral_impact'
            else 'operations_hindering_success'
        end as customer_success_impact,
        
        -- Metadata
        current_timestamp as performance_analyzed_at
        
    from {{ ref('entity_customers') }} c
    join account_operational_metrics aom on c.account_id::varchar = aom.account_id::varchar
    where c.customer_status in ('active', 'trial')
)

select * from operations_performance_final
order by 
    case operations_priority
        when 'immediate_action_required' then 1
        when 'proactive_intervention_needed' then 2
        when 'optimization_opportunity' then 3
        else 4
    end,
    composite_operational_score desc,
    monthly_recurring_revenue desc