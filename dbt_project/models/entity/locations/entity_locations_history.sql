{{ config(
    materialized='incremental',
    unique_key='location_history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['location_id', 'valid_from']},
        {'columns': ['valid_from']},
        {'columns': ['change_type']}
    ]
) }}

-- Entity: Locations (History/Change Tracking)
-- Tracks location operational evolution including device changes, performance shifts, and customer feedback
-- Enables operational excellence analysis, location optimization, and expansion planning

with location_current as (
    select * from {{ ref('entity_locations') }}
),

history_records as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['location_id', 'current_timestamp']) }} as location_history_id,
        
        -- Location identifiers
        location_id,
        location_key,
        account_id,
        
        -- Change tracking
        'snapshot' as change_type,
        
        -- Location details at time of change
        location_name,
        location_type,
        location_category,
        location_status,
        operational_status,
        
        -- Device infrastructure at time of change
        total_devices,
        active_devices,
        online_devices,
        device_connectivity_rate,
        
        -- Operational metrics at time of change
        tap_events_30d,
        total_volume_30d,
        quality_issues_30d,
        quality_issue_rate_30d,
        
        -- Performance scoring
        operational_health_score,
        0::numeric as previous_health_score,
        0::numeric as health_score_change,
        
        operational_readiness_score,
        0::numeric as previous_readiness_score,
        
        -- Customer metrics
        customer_satisfaction_score,
        0::numeric as previous_satisfaction_score,
        0::numeric as satisfaction_delta,
        
        revenue_per_location,
        0::numeric as previous_revenue,
        0::numeric as revenue_change,
        
        -- Classification changes
        device_health_tier,
        ''::text as previous_device_health_tier,
        
        activity_level,
        ''::text as previous_activity_level,
        
        volume_tier,
        ''::text as previous_volume_tier,
        
        expansion_indicator,
        ''::text as previous_expansion_indicator,
        
        -- Support metrics
        support_tickets_open,
        support_priority,
        
        -- Operational flags
        has_maintenance_devices,
        devices_but_no_activity,
        users_but_no_taps,
        
        -- Key dates
        location_created_at,
        first_device_installed,
        last_maintenance_performed,
        
        -- Temporal validity
        current_timestamp as valid_from,
        null::timestamp as valid_to,
        true as is_current,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from location_current
    
    {% if is_incremental() %}
    -- For incremental runs, only capture meaningful changes
    where not exists (
        select 1 
        from {{ this }} h
        where h.location_id::text = location_current.location_id::text
          and h.is_current = true
          and h.operational_status = location_current.operational_status
          and h.operational_health_score = location_current.operational_health_score
          and h.total_devices = location_current.total_devices
          and h.activity_level = location_current.activity_level
    )
    {% endif %}
)

select * from history_records