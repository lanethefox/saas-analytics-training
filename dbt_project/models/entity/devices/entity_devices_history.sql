{{ config(
    materialized='incremental',
    unique_key='history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['device_id', 'valid_from']},
        {'columns': ['location_id']},
        {'columns': ['event_type']},
        {'columns': ['change_date']}
    ],
    pre_hook="{% if is_incremental() %}
        -- Ensure we don't duplicate records on re-runs
        DELETE FROM {{ this }}
        WHERE change_date >= (
            SELECT COALESCE(MAX(change_date), '1900-01-01'::date) - INTERVAL '1 day'
            FROM {{ this }}
        )
    {% endif %}"
) }}

-- Entity: Devices (Change History)
-- Complete device lifecycle tracking including installations, maintenance, failures, and performance changes
-- Primary use cases: Predictive maintenance modeling, reliability analysis, warranty tracking, failure pattern analysis

with tap_events as (
    select 
        device_id,
        location_id,
        event_timestamp,
        event_type,
        event_category,
        event_status,
        volume_ml,
        temperature_c,
        pressure_psi,
        flow_rate_ml_per_sec,
        duration_seconds,
        temperature_anomaly,
        pressure_anomaly,
        estimated_revenue
    from {{ ref('stg_app_database__tap_events') }}
    {% if is_incremental() %}
        where event_date >= (
            SELECT COALESCE(MAX(change_date), '1900-01-01'::date) - INTERVAL '1 day'
            FROM {{ this }}
        )
    {% endif %}
),

device_changes as (
    -- Device state changes from main devices table
    select
        device_id,
        location_id,
        device_created_at as change_timestamp,
        'device_installed' as event_type,
        'installation' as event_category,
        'new_device' as change_reason,
        null::float as performance_impact,
        null::text as maintenance_type,
        null::text as failure_category,
        0 as error_count,
        0 as anomaly_count,
        'Newly installed device' as description
    from {{ ref('stg_app_database__devices') }}
    
    union all
    
    -- Operational events from tap events
    select
        device_id,
        location_id,
        event_timestamp as change_timestamp,
        event_type,
        event_category,
        case 
            when event_category = 'Error' then 'error_detected'
            when event_category = 'Maintenance' then 'scheduled_maintenance'
            when temperature_anomaly or pressure_anomaly then 'anomaly_detected'
            when event_category = 'Cleaning' then 'cleaning_performed'
            when event_category = 'Calibration' then 'calibration_performed'
            else 'operational_event'
        end as change_reason,
        -- Performance impact based on anomalies
        case 
            when temperature_anomaly and pressure_anomaly then -0.20
            when temperature_anomaly or pressure_anomaly then -0.10
            when event_category = 'Error' then -0.15
            when event_category = 'Maintenance' then 0.05
            when event_category = 'Cleaning' then 0.03
            when event_category = 'Calibration' then 0.02
            else 0
        end as performance_impact,
        case 
            when event_category = 'Maintenance' then 'scheduled'
            when event_category = 'Cleaning' then 'routine_cleaning'
            when event_category = 'Calibration' then 'calibration'
            else null
        end as maintenance_type,
        case 
            when event_category = 'Error' and temperature_anomaly then 'temperature_failure'
            when event_category = 'Error' and pressure_anomaly then 'pressure_failure'
            when event_category = 'Error' then 'operational_failure'
            else null
        end as failure_category,
        case when event_category = 'Error' then 1 else 0 end as error_count,
        case when temperature_anomaly or pressure_anomaly then 1 else 0 end as anomaly_count,
        -- Descriptive context
        concat(
            event_type, 
            case 
                when temperature_anomaly then ' (Temperature: ' || temperature_c || '°C)'
                when pressure_anomaly then ' (Pressure: ' || pressure_psi || ' PSI)'
                when volume_ml is not null then ' (Volume: ' || round(volume_ml::numeric, 1) || 'ml)'
                else ''
            end
        ) as description
    from tap_events
),

history_with_calculations as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['device_id', 'change_timestamp', 'event_type']) }} as history_id,
        
        -- Core identifiers
        device_id,
        location_id,
        
        -- Temporal fields
        change_timestamp,
        change_timestamp as valid_from,
        lead(change_timestamp, 1, '9999-12-31'::timestamp) over (
            partition by device_id order by change_timestamp
        ) as valid_to,
        date(change_timestamp) as change_date,
        
        -- Event details
        event_type,
        event_category,
        change_reason,
        description,
        
        -- Maintenance tracking
        maintenance_type,
        case 
            when maintenance_type is not null then
                lag(change_timestamp) over (
                    partition by device_id, maintenance_type 
                    order by change_timestamp
                )
            else null
        end as previous_maintenance_timestamp,
        
        -- Performance tracking
        performance_impact,
        sum(performance_impact) over (
            partition by device_id 
            order by change_timestamp 
            rows between unbounded preceding and current row
        ) as cumulative_performance_impact,
        
        -- Failure tracking
        failure_category,
        error_count,
        sum(error_count) over (
            partition by device_id 
            order by change_timestamp 
            rows between unbounded preceding and current row
        ) as cumulative_error_count,
        
        -- Anomaly tracking
        anomaly_count,
        sum(anomaly_count) over (
            partition by device_id 
            order by change_timestamp 
            rows between unbounded preceding and current row
        ) as cumulative_anomaly_count,
        
        -- Event sequencing
        row_number() over (partition by device_id order by change_timestamp) as event_sequence,
        row_number() over (
            partition by device_id, event_category 
            order by change_timestamp
        ) as category_sequence,
        
        -- Time since last event
        extract(epoch from (
            change_timestamp - lag(change_timestamp) over (
                partition by device_id order by change_timestamp
            )
        )) / 3600.0 as hours_since_last_event,
        
        -- Time since last category event
        extract(epoch from (
            change_timestamp - lag(change_timestamp) over (
                partition by device_id, event_category order by change_timestamp
            )
        )) / 3600.0 as hours_since_last_category_event
        
    from device_changes
),

final as (
    select
        history_id,
        device_id,
        location_id,
        
        -- Temporal fields
        valid_from,
        valid_to,
        case when valid_to = '9999-12-31'::timestamp then true else false end as is_current,
        change_date,
        extract(hour from change_timestamp) as change_hour,
        extract(dow from change_timestamp) as change_day_of_week,
        
        -- Event details
        event_type,
        event_category,
        change_reason,
        description,
        
        -- Maintenance tracking
        maintenance_type,
        previous_maintenance_timestamp,
        case 
            when previous_maintenance_timestamp is not null then
                extract(epoch from (
                    change_timestamp - previous_maintenance_timestamp
                )) / 86400.0
            else null
        end as days_since_previous_maintenance,
        
        -- Performance metrics
        performance_impact,
        cumulative_performance_impact,
        case 
            when cumulative_performance_impact >= 0 then 'improving'
            when cumulative_performance_impact >= -0.1 then 'stable'
            when cumulative_performance_impact >= -0.3 then 'degrading'
            else 'critical'
        end as performance_trend,
        
        -- Failure and reliability metrics
        failure_category,
        error_count,
        cumulative_error_count,
        anomaly_count,
        cumulative_anomaly_count,
        
        -- Mean time between failures (MTBF) calculation
        case 
            when cumulative_error_count > 1 then
                extract(epoch from (
                    change_timestamp - min(change_timestamp) over (
                        partition by device_id 
                        order by change_timestamp 
                        rows between unbounded preceding and current row
                    )
                )) / 3600.0 / greatest(cumulative_error_count - 1, 1)
            else null
        end as mtbf_hours,
        
        -- Event patterns
        event_sequence,
        category_sequence,
        hours_since_last_event,
        hours_since_last_category_event,
        
        -- Pattern detection flags
        case 
            when hours_since_last_event < 1 and event_category = 'Error' then true
            else false
        end as rapid_failure_flag,
        
        case 
            when anomaly_count > 0 and 
                 lag(anomaly_count, 1, 0) over (partition by device_id order by change_timestamp) > 0
            then true
            else false
        end as consecutive_anomaly_flag,
        
        -- Metadata
        current_timestamp as _entity_updated_at
        
    from history_with_calculations
)

select * from final