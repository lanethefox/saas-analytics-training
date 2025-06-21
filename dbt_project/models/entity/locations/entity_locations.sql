{{ config(
    materialized='table',
    indexes=[
        {'columns': ['location_id'], 'unique': True},
        {'columns': ['account_id']},
        {'columns': ['operational_status']},
        {'columns': ['operational_health_score']},
        {'columns': ['location_status']}
    ]
) }}

-- Entity: Locations (Atomic/Current State)
-- Operational focus capturing device counts, performance metrics, and customer satisfaction
-- Provides comprehensive view of current location state for operations management

with location_core as (
    select * from {{ ref('int_locations__core') }}
),

location_operational as (
    select * from {{ ref('int_locations__operational_metrics') }}
),

final as (
    select
        -- Primary identifiers
        lc.location_id,
        lc.location_key,
        lc.account_id,
        
        -- Location details
        lc.location_name,
        lc.location_type,
        lc.location_category,
        lc.location_status,
        lc.operational_status,
        
        -- Geographic information
        lc.street_address,
        lc.city,
        lc.state_code,
        lc.country_code,
        lc.full_address,
        lc.geographic_market,
        lc.market_tier,
        
        -- Physical attributes
        lc.seating_capacity,
        lc.timezone,
        lc.is_customer_facing,
        
        -- Device infrastructure
        lc.total_devices,
        lc.active_devices,
        lc.online_devices,
        lc.device_connectivity_rate,
        lc.first_device_installed,
        lc.latest_device_installed,
        lc.last_maintenance_performed,
        lc.avg_days_since_maintenance,
        
        -- Operational activity (30-day metrics)
        lc.tap_events_30d,
        lc.active_devices_30d,
        lc.total_volume_30d,
        lc.avg_flow_rate_30d,
        lc.quality_issues_30d,
        lc.beverage_types_served_30d,
        lc.avg_events_per_device_30d,
        lc.avg_volume_per_event_30d,
        lc.quality_issue_rate_30d,
        
        -- User engagement
        lc.total_users,
        lc.active_users,
        lc.latest_user_login,
        lo.user_engagement_level,
        
        -- Advanced operational metrics
        lo.taps_per_device_30d,
        lo.avg_taps_per_active_day,
        lo.taps_per_user_30d,
        lo.avg_volume_per_tap,
        lo.active_days_last_30d,
        
        -- Health and performance scoring
        lc.operational_health_score,
        lo.device_health_tier,
        lo.activity_level,
        lc.volume_tier,
        lc.connectivity_tier,
        
        -- Customer satisfaction (placeholder - would come from surveys/reviews)
        case 
            when lc.quality_issue_rate_30d < 0.02 and lc.operational_health_score > 0.8 then 4.5
            when lc.quality_issue_rate_30d < 0.05 and lc.operational_health_score > 0.6 then 4.0
            when lc.quality_issue_rate_30d < 0.10 and lc.operational_health_score > 0.4 then 3.5
            when lc.operational_health_score > 0.2 then 3.0
            else 2.5
        end as customer_satisfaction_score,
        
        -- Support metrics (placeholder - would come from ticket system)
        case 
            when lc.quality_issues_30d > 10 then 5
            when lc.quality_issues_30d > 5 then 3
            when lc.quality_issues_30d > 0 then 1
            else 0
        end as support_tickets_open,
        
        -- Revenue per location (placeholder - would join with revenue data)
        case 
            when lc.volume_tier = 'high_volume' then 15000
            when lc.volume_tier = 'medium_volume' then 10000
            when lc.volume_tier = 'low_volume' then 5000
            when lc.volume_tier = 'minimal_volume' then 2000
            else 0
        end::numeric as revenue_per_location,
        
        -- Expansion opportunity
        case 
            when lc.operational_health_score > 0.8 
                and lc.volume_tier in ('high_volume', 'medium_volume')
                and lc.active_devices < lc.total_devices * 0.8
            then 'high_expansion_potential'
            when lc.operational_health_score > 0.6 
                and lc.tap_events_30d > 100
            then 'moderate_expansion_potential'
            else 'low_expansion_potential'
        end as expansion_indicator,
        
        -- Operational flags
        lo.has_maintenance_devices,
        lo.devices_but_no_activity,
        lo.users_but_no_taps,
        lo.recent_activity_status,
        
        -- Lifecycle information
        lc.location_created_at,
        lc.location_updated_at,
        lc.location_age_days,
        lc.location_age_months,
        lc.location_lifecycle_stage,
        lc.is_newly_opened,
        
        -- Operational readiness score
        round((
            lc.operational_health_score * 0.4 +
            case when lc.device_connectivity_rate > 0 then lc.device_connectivity_rate * 0.3 else 0 end +
            case when lc.quality_issue_rate_30d < 0.05 then 0.3 else 0.15 end
        )::numeric, 2) as operational_readiness_score,
        
        -- Support prioritization
        case 
            when lo.devices_but_no_activity or lo.has_maintenance_devices then 'urgent'
            when lc.operational_health_score < 0.5 then 'high'
            when lc.quality_issues_30d > 5 then 'medium'
            else 'low'
        end as support_priority,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from location_core lc
    left join location_operational lo on lc.location_id = lo.location_id
)

select * from final