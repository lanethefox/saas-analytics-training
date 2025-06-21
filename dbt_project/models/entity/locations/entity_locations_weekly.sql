{{ config(
    materialized='incremental',
    unique_key=['location_id', 'week_start_date'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'week_start_date',
        'data_type': 'date'
    },
    cluster_by=['location_id', 'week_start_date'],
    indexes=[
        {'columns': ['location_id', 'week_start_date'], 'unique': True},
        {'columns': ['week_start_date']},
        {'columns': ['account_id']}
    ]
) }}

-- Entity: Locations (Weekly Strategic Grain)
-- Weekly location performance for operational reporting and strategic planning
-- Supports operations reporting, regional analysis, expansion planning, and customer success

{% if is_incremental() %}
    {% set lookback_days = 7 %}
{% else %}
    {% set lookback_days = 180 %}
{% endif %}

with date_spine as (
    select distinct
        date_trunc('week', series_date)::date as week_start_date,
        date_trunc('week', series_date)::date + interval '6 days' as week_end_date
    from (
        select generate_series(
            current_date - interval '{{ lookback_days }} days',
            current_date,
            '1 day'::interval
        )::date as series_date
    ) dates
    where date_trunc('week', series_date)::date < date_trunc('week', current_date)
),

location_base as (
    select distinct
        location_id,
        location_key,
        account_id,
        location_name,
        location_type,
        location_category,
        city,
        state_code,
        country_code,
        geographic_market,
        location_created_at
    from {{ ref('entity_locations') }}
),

-- Get weekly tap events
weekly_tap_events as (
    select
        location_id,
        date_trunc('week', event_timestamp)::date as week_start_date,
        count(*) as weekly_tap_events,
        count(distinct device_id) as active_devices,
        count(distinct date(event_timestamp)) as active_days,
        sum(volume_ml::float) as total_volume,
        avg(flow_rate_ml_per_sec::float) as avg_flow_rate,
        count(case when temperature_anomaly or pressure_anomaly then 1 end) as quality_issues,
        count(distinct event_type) as beverage_types_served
    from {{ ref('stg_app_database__tap_events') }}
    where event_timestamp >= current_date - interval '{{ lookback_days }} days'
    group by 1, 2
),

-- Get device metrics from current state
location_device_metrics as (
    select
        location_id,
        total_devices,
        device_connectivity_rate,
        operational_health_score,
        device_health_tier,
        activity_level
    from {{ ref('entity_locations') }}
),

final as (
    select
        -- Identifiers
        lb.location_id,
        lb.location_key,
        lb.account_id,
        d.week_start_date,
        d.week_end_date,
        
        -- Location details
        lb.location_name,
        lb.location_type,
        lb.location_category,
        lb.city,
        lb.state_code,
        lb.country_code,
        lb.geographic_market,
        
        -- Weekly operational metrics
        coalesce(wte.weekly_tap_events, 0) as weekly_tap_events,
        coalesce(wte.active_devices, 0) as active_devices,
        coalesce(wte.active_days, 0) as active_days,
        coalesce(wte.total_volume, 0) as total_volume,
        coalesce(wte.avg_flow_rate, 0) as avg_flow_rate,
        coalesce(wte.quality_issues, 0) as quality_issues,
        coalesce(wte.beverage_types_served, 0) as beverage_types_served,
        
        -- Device infrastructure (from current state as proxy)
        ldm.total_devices,
        ldm.device_connectivity_rate,
        
        -- Calculated weekly metrics
        case 
            when ldm.total_devices > 0 and wte.weekly_tap_events > 0
            then round(wte.weekly_tap_events::numeric / ldm.total_devices, 2)
            else 0
        end as taps_per_device,
        
        case 
            when wte.active_days > 0 and wte.weekly_tap_events > 0
            then round(wte.weekly_tap_events::numeric / wte.active_days, 2)
            else 0
        end as avg_daily_taps,
        
        case 
            when wte.weekly_tap_events > 0 and wte.quality_issues >= 0
            then round(wte.quality_issues::numeric / wte.weekly_tap_events * 100, 2)
            else 0
        end as quality_issue_rate,
        
        -- Weekly health score
        case 
            when wte.active_days >= 6 and ldm.device_connectivity_rate > 0.9 and wte.quality_issues < wte.weekly_tap_events * 0.02
            then 0.95
            when wte.active_days >= 4 and ldm.device_connectivity_rate > 0.7 and wte.quality_issues < wte.weekly_tap_events * 0.05
            then 0.80
            when wte.active_days >= 2 and ldm.device_connectivity_rate > 0.5
            then 0.60
            when wte.weekly_tap_events > 0
            then 0.40
            else 0.20
        end as weekly_operational_score,
        
        -- Activity classification
        case 
            when wte.weekly_tap_events >= 500 then 'high_activity'
            when wte.weekly_tap_events >= 200 then 'medium_activity'
            when wte.weekly_tap_events >= 50 then 'low_activity'
            when wte.weekly_tap_events > 0 then 'minimal_activity'
            else 'no_activity'
        end as weekly_activity_level,
        
        -- Volume classification
        case 
            when wte.total_volume >= 50000 then 'high_volume'
            when wte.total_volume >= 20000 then 'medium_volume'
            when wte.total_volume >= 5000 then 'low_volume'
            when wte.total_volume > 0 then 'minimal_volume'
            else 'no_volume'
        end as weekly_volume_tier,
        
        -- Device utilization
        case 
            when ldm.total_devices > 0 
            then round(wte.active_devices::numeric / ldm.total_devices * 100, 2)
            else 0
        end as device_utilization_rate,
        
        -- Customer satisfaction trend (placeholder)
        case 
            when wte.quality_issues = 0 and wte.weekly_tap_events > 100 then 'improving'
            when wte.quality_issues > 5 then 'declining'
            else 'stable'
        end as satisfaction_trend,
        
        -- Revenue proxy (based on volume)
        round((wte.total_volume * 0.15)::numeric, 2) as estimated_weekly_revenue,
        
        -- Lifecycle stage at week
        case 
            when d.week_start_date < lb.location_created_at then 'not_yet_opened'
            when d.week_start_date < lb.location_created_at + interval '30 days' then 'newly_opened'
            when d.week_start_date < lb.location_created_at + interval '180 days' then 'establishing'
            else 'established'
        end as location_lifecycle_stage,
        
        -- Expansion readiness
        case 
            when wte.active_devices >= ldm.total_devices * 0.8 
                and wte.weekly_tap_events > 200
                and wte.quality_issues < 5
            then 'ready_for_expansion'
            else 'not_ready'
        end as expansion_readiness,
        
        -- Week-over-week trends (placeholder)
        0::numeric as taps_wow_change,
        0::numeric as volume_wow_change,
        0::numeric as quality_wow_change,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from date_spine d
    cross join location_base lb
    left join weekly_tap_events wte 
        on lb.location_id = wte.location_id 
        and d.week_start_date = wte.week_start_date
    left join location_device_metrics ldm 
        on lb.location_id = ldm.location_id
    where d.week_start_date >= date_trunc('week', lb.location_created_at)::date
    
    {% if is_incremental() %}
        and d.week_start_date >= current_date - interval '{{ lookback_days }} days'
    {% endif %}
)

select * from final