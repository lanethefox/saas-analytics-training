{{ config(
    materialized='incremental',
    unique_key='tap_event_id',
    on_schema_change='fail'
) }}

-- Staging model for tap events
-- Real-time IoT sensor data with anomaly detection and time-series enrichment

with source_data as (
    select * from {{ source('app_database', 'tap_events') }}
),

{% if is_incremental() %}
max_timestamp as (
    select max(event_timestamp) as max_ts from {{ this }}
),

filtered_source as (
    select 
        source_data.*
    from source_data
    cross join max_timestamp
    where source_data.timestamp > max_timestamp.max_ts
),
{% else %}
filtered_source as (
    select * from source_data
),
{% endif %}

enriched as (
    select
        -- Primary identifiers
        id as tap_event_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as tap_event_key,
        device_id,
        location_id,
        
        -- Event details
        timestamp as event_timestamp,
        event_type,
        status as event_status,
        device_category,
        
        -- JSON metrics extraction (common fields)
        metrics->>'volume_ml' as volume_ml,
        metrics->>'temperature_c' as temperature_c,
        metrics->>'pressure_psi' as pressure_psi,
        metrics->>'flow_rate_ml_per_sec' as flow_rate_ml_per_sec,
        metrics->>'duration_seconds' as duration_seconds,
        metrics as raw_metrics,
        
        -- Event type categorization
        case
            when lower(event_type) like '%pour%' then 'Pour'
            when lower(event_type) like '%clean%' then 'Cleaning'
            when lower(event_type) like '%error%' then 'Error'
            when lower(event_type) like '%maintenance%' then 'Maintenance'
            when lower(event_type) like '%calibration%' then 'Calibration'
            else 'Other'
        end as event_category,
        
        -- Status flags
        case 
            when lower(status) = 'success' then true
            else false
        end as is_successful,
        
        case 
            when lower(status) = 'error' or lower(event_type) like '%error%' then true
            else false
        end as is_error,
        
        -- Time-based dimensions
        date(timestamp) as event_date,
        extract(hour from timestamp) as event_hour,
        extract(dow from timestamp) as event_day_of_week,
        
        case
            when extract(hour from timestamp) between 11 and 14 then 'Lunch'
            when extract(hour from timestamp) between 17 and 20 then 'Dinner'
            when extract(hour from timestamp) between 20 and 23 then 'Evening'
            when extract(hour from timestamp) between 0 and 2 then 'Late Night'
            else 'Other'
        end as business_period,
        
        -- Volume calculations (if available)
        case
            when metrics->>'volume_ml' is not null then
                (metrics->>'volume_ml')::float / 29.5735  -- Convert to oz
            else null
        end as volume_oz,
        
        -- Revenue estimation (assuming $0.50 per oz average)
        case
            when metrics->>'volume_ml' is not null and lower(event_type) like '%pour%' then
                ((metrics->>'volume_ml')::float / 29.5735) * 0.50
            else 0
        end as estimated_revenue,
        
        -- Anomaly detection flags
        case
            when metrics->>'temperature_c' is not null and 
                 ((metrics->>'temperature_c')::float < -5 or (metrics->>'temperature_c')::float > 10) then true
            else false
        end as temperature_anomaly,
        
        case
            when metrics->>'pressure_psi' is not null and 
                 ((metrics->>'pressure_psi')::float < 10 or (metrics->>'pressure_psi')::float > 50) then true
            else false
        end as pressure_anomaly,
        
        -- Data quality flags
        case 
            when device_id is null then true 
            else false 
        end as missing_device_id,
        
        case 
            when timestamp is null then true 
            else false 
        end as missing_timestamp,
        
        -- Timestamps
        created_at as record_created_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from filtered_source
)

select * from enriched