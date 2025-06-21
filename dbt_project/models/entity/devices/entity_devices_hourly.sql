{{ config(
    materialized='incremental',
    unique_key=['device_id', 'hour_timestamp'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'hour_timestamp',
        'data_type': 'timestamp',
        'granularity': 'day'
    },
    cluster_by=['device_id', 'location_id'],
    indexes=[
        {'columns': ['device_id', 'hour_timestamp']},
        {'columns': ['location_id', 'hour_timestamp']},
        {'columns': ['hour_timestamp']},
        {'columns': ['performance_tier']}
    ],
    pre_hook="{% if is_incremental() %}
        -- Clean up any partial data from the lookback window
        DELETE FROM {{ this }}
        WHERE hour_timestamp >= DATE_TRUNC(
            'hour',
            (SELECT COALESCE(MAX(hour_timestamp), '1900-01-01'::timestamp) - INTERVAL '2 hours' FROM {{ this }})
        )
    {% endif %}"
) }}

-- Entity: Devices (Hourly Grain)
-- Hourly device performance aggregations for operational monitoring and trend detection
-- Primary use cases: Operations dashboards, SLA monitoring, capacity planning, performance trending

with hourly_events as (
    select
        device_id,
        location_id,
        date_trunc('hour', event_timestamp) as hour_timestamp,
        
        -- Event counts by type
        count(*) as total_events,
        count(case when event_category = 'Pour' then 1 end) as pour_events,
        count(case when event_category = 'Error' then 1 end) as error_events,
        count(case when event_category = 'Maintenance' then 1 end) as maintenance_events,
        count(case when event_category = 'Cleaning' then 1 end) as cleaning_events,
        count(case when is_error then 1 end) as failed_events,
        count(case when is_successful then 1 end) as successful_events,
        
        -- Volume metrics
        sum(volume_ml::numeric) as total_volume_ml,
        avg(volume_ml::numeric) as avg_volume_per_event_ml,
        max(volume_ml::numeric) as max_volume_ml,
        min(case when volume_ml is not null then volume_ml::numeric end) as min_volume_ml,
        
        -- Flow rate metrics
        avg(flow_rate_ml_per_sec::numeric) as avg_flow_rate,
        max(flow_rate_ml_per_sec::numeric) as max_flow_rate,
        min(case when flow_rate_ml_per_sec is not null then flow_rate_ml_per_sec::numeric end) as min_flow_rate,
        stddev(flow_rate_ml_per_sec::numeric) as flow_rate_stddev,
        
        -- Temperature metrics
        avg(temperature_c::numeric) as avg_temperature,
        max(temperature_c::numeric) as max_temperature,
        min(temperature_c::numeric) as min_temperature,
        stddev(temperature_c::numeric) as temperature_stddev,
        
        -- Pressure metrics
        avg(pressure_psi::numeric) as avg_pressure,
        max(pressure_psi::numeric) as max_pressure,
        min(pressure_psi::numeric) as min_pressure,
        stddev(pressure_psi::numeric) as pressure_stddev,
        
        -- Anomaly counts
        count(case when temperature_anomaly then 1 end) as temperature_anomalies,
        count(case when pressure_anomaly then 1 end) as pressure_anomalies,
        count(case when temperature_anomaly or pressure_anomaly then 1 end) as total_anomalies,
        
        -- Duration metrics
        sum(duration_seconds::numeric) as total_active_seconds,
        avg(duration_seconds::numeric) as avg_event_duration_seconds,
        
        -- Revenue metrics
        sum(estimated_revenue) as hourly_revenue,
        
        -- Operational windows
        min(event_timestamp) as first_event_time,
        max(event_timestamp) as last_event_time
        
    from {{ ref('stg_app_database__tap_events') }}
    {% if is_incremental() %}
        where event_timestamp >= DATE_TRUNC(
            'hour',
            (SELECT COALESCE(MAX(hour_timestamp), '1900-01-01'::timestamp) - INTERVAL '2 hours' FROM {{ this }})
        )
    {% endif %}
    group by 1, 2, 3
),

device_info as (
    select
        device_id,
        device_type,
        model,
        operational_status
    from {{ ref('stg_app_database__devices') }}
),

hourly_metrics as (
    select
        he.device_id,
        he.location_id,
        he.hour_timestamp,
        
        -- Device info
        di.device_type,
        di.model,
        
        -- Hourly performance metrics
        he.total_events,
        he.pour_events,
        he.error_events,
        he.maintenance_events,
        he.cleaning_events,
        he.failed_events,
        he.successful_events,
        
        -- Success rate
        case 
            when he.total_events > 0 then 
                round(he.successful_events::numeric / he.total_events::numeric, 4)
            else 1.0
        end as success_rate,
        
        -- Error rate
        case 
            when he.total_events > 0 then 
                round(he.error_events::numeric / he.total_events::numeric, 4)
            else 0.0
        end as error_rate,
        
        -- Volume metrics
        coalesce(he.total_volume_ml, 0) as total_volume_ml,
        he.avg_volume_per_event_ml,
        he.max_volume_ml,
        he.min_volume_ml,
        
        -- Flow performance
        he.avg_flow_rate,
        he.max_flow_rate,
        he.min_flow_rate,
        he.flow_rate_stddev,
        
        -- Environmental conditions
        he.avg_temperature,
        he.max_temperature,
        he.min_temperature,
        he.temperature_stddev,
        
        he.avg_pressure,
        he.max_pressure,
        he.min_pressure,
        he.pressure_stddev,
        
        -- Anomaly metrics
        he.temperature_anomalies,
        he.pressure_anomalies,
        he.total_anomalies,
        
        -- Anomaly rates
        case 
            when he.total_events > 0 then 
                round(he.total_anomalies::numeric / he.total_events::numeric, 4)
            else 0.0
        end as anomaly_rate,
        
        -- Uptime calculation (device was active if it had events)
        case when he.total_events > 0 then 60 else 0 end as uptime_minutes,
        he.total_active_seconds,
        
        -- Utilization rate (active seconds / 3600)
        round((coalesce(he.total_active_seconds, 0) / 3600.0)::numeric, 3) as utilization_rate,
        
        -- Revenue
        coalesce(he.hourly_revenue, 0) as revenue,
        
        -- Temporal context
        extract(hour from he.hour_timestamp) as hour_of_day,
        extract(dow from he.hour_timestamp) as day_of_week,
        case 
            when extract(dow from he.hour_timestamp) in (0, 6) then true
            else false
        end as is_weekend,
        
        -- Business periods
        case
            when extract(hour from he.hour_timestamp) between 6 and 11 then 'morning'
            when extract(hour from he.hour_timestamp) between 12 and 16 then 'afternoon'
            when extract(hour from he.hour_timestamp) between 17 and 22 then 'evening'
            else 'night'
        end as business_period,
        
        -- Peak hours flag
        case
            when extract(hour from he.hour_timestamp) between 11 and 14 
                or extract(hour from he.hour_timestamp) between 17 and 21 
            then true
            else false
        end as is_peak_hour
        
    from hourly_events he
    left join device_info di on he.device_id = di.device_id
),

with_calculations as (
    select
        *,
        
        -- Moving averages (previous 24 hours)
        avg(total_events) over (
            partition by device_id 
            order by hour_timestamp 
            rows between 23 preceding and current row
        ) as avg_events_24h,
        
        avg(total_volume_ml) over (
            partition by device_id 
            order by hour_timestamp 
            rows between 23 preceding and current row
        ) as avg_volume_24h,
        
        avg(error_rate) over (
            partition by device_id 
            order by hour_timestamp 
            rows between 23 preceding and current row
        ) as avg_error_rate_24h,
        
        -- Trend indicators
        case 
            when lag(total_events, 1) over (partition by device_id order by hour_timestamp) > 0 then
                (total_events - lag(total_events, 1) over (partition by device_id order by hour_timestamp))::float / 
                lag(total_events, 1) over (partition by device_id order by hour_timestamp)
            else null
        end as event_change_rate,
        
        -- Performance scoring
        case 
            when success_rate >= 0.98 and anomaly_rate <= 0.02 then 1.0
            when success_rate >= 0.95 and anomaly_rate <= 0.05 then 0.9
            when success_rate >= 0.90 and anomaly_rate <= 0.10 then 0.75
            when success_rate >= 0.80 then 0.5
            else 0.25
        end as hourly_performance_score,
        
        -- Operational status during hour
        case 
            when error_rate > 0.2 then 'critical'
            when error_rate > 0.1 then 'degraded'
            when total_events = 0 then 'idle'
            else 'operational'
        end as hourly_status
        
    from hourly_metrics
),

final as (
    select
        -- Primary keys
        device_id,
        hour_timestamp,
        
        -- Identifiers
        location_id,
        device_type,
        model,
        
        -- Hourly event metrics
        total_events,
        pour_events,
        error_events,
        maintenance_events,
        cleaning_events,
        successful_events,
        failed_events,
        
        -- Performance rates
        success_rate,
        error_rate,
        anomaly_rate,
        
        -- Volume metrics
        total_volume_ml,
        round((total_volume_ml / 1000.0)::numeric, 3) as total_volume_liters,
        avg_volume_per_event_ml,
        max_volume_ml,
        min_volume_ml,
        
        -- Flow metrics
        avg_flow_rate,
        max_flow_rate,
        min_flow_rate,
        flow_rate_stddev,
        
        -- Environmental metrics
        avg_temperature,
        max_temperature,
        min_temperature,
        temperature_stddev,
        avg_pressure,
        max_pressure,
        min_pressure,
        pressure_stddev,
        
        -- Anomaly counts
        temperature_anomalies,
        pressure_anomalies,
        total_anomalies,
        
        -- Operational metrics
        uptime_minutes,
        total_active_seconds,
        utilization_rate,
        revenue,
        
        -- Moving averages
        round(avg_events_24h::numeric, 2) as avg_events_24h,
        round(avg_volume_24h::numeric, 2) as avg_volume_ml_24h,
        round(avg_error_rate_24h::numeric, 4) as avg_error_rate_24h,
        
        -- Trend indicators
        round(event_change_rate::numeric, 3) as event_change_rate,
        case 
            when event_change_rate > 0.1 then 'increasing'
            when event_change_rate < -0.1 then 'decreasing'
            else 'stable'
        end as volume_trend,
        
        -- Performance assessment
        hourly_performance_score,
        case 
            when hourly_performance_score >= 0.9 then 'excellent'
            when hourly_performance_score >= 0.75 then 'good'
            when hourly_performance_score >= 0.5 then 'fair'
            else 'poor'
        end as performance_tier,
        
        -- Temporal context
        hour_of_day,
        day_of_week,
        is_weekend,
        business_period,
        is_peak_hour,
        hourly_status,
        
        -- SLA tracking
        case when success_rate >= 0.95 then true else false end as meets_sla,
        case when uptime_minutes >= 55 then true else false end as meets_uptime_sla,
        
        -- Alert indicators
        case 
            when error_rate > 0.2 or anomaly_rate > 0.3 then 'critical'
            when error_rate > 0.1 or anomaly_rate > 0.2 then 'warning'
            else 'normal'
        end as alert_level,
        
        -- Metadata
        current_timestamp as _entity_updated_at
        
    from with_calculations
)

select * from final