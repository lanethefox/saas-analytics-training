{{ config(
    materialized='incremental',
    unique_key='session_id',
    on_schema_change='fail'
) }}

-- Staging model for user sessions
-- Tracks application usage patterns and user engagement

with source_data as (
    select * from {{ source('app_database', 'user_sessions') }}
    
    {% if is_incremental() %}
        where start_time > (select max(start_time) from {{ this }})
    {% endif %}
),

enriched as (
    select
        -- Primary identifiers
        session_id,
        {{ dbt_utils.generate_surrogate_key(['session_id']) }} as session_key,
        user_id,
        customer_id as account_id,
        
        -- Session timing
        start_time,
        end_time,
        duration_seconds,
        
        -- Activity metrics
        page_views,
        actions_taken,
        
        -- Device information
        device_type,
        browser,
        
        -- Session duration categorization
        case
            when duration_seconds < 30 then 'Bounce'
            when duration_seconds < 120 then 'Quick'
            when duration_seconds < 300 then 'Short'
            when duration_seconds < 900 then 'Medium'
            when duration_seconds < 1800 then 'Long'
            else 'Extended'
        end as session_duration_category,
        
        -- Engagement level
        case
            when duration_seconds < 30 and page_views <= 1 then 'No Engagement'
            when page_views <= 2 then 'Low Engagement'
            when page_views <= 5 then 'Medium Engagement'
            when page_views <= 10 then 'High Engagement'
            else 'Very High Engagement'
        end as engagement_level,
        
        -- Actions per minute
        case
            when duration_seconds > 0 then 
                round((actions_taken::numeric / (duration_seconds::numeric / 60)), 2)
            else 0
        end as actions_per_minute,
        
        -- Pages per minute
        case
            when duration_seconds > 0 then 
                round((page_views::numeric / (duration_seconds::numeric / 60)), 2)
            else 0
        end as pages_per_minute,
        
        -- Device categorization
        case
            when lower(device_type) like '%mobile%' or lower(device_type) like '%phone%' then 'Mobile'
            when lower(device_type) like '%tablet%' or lower(device_type) like '%ipad%' then 'Tablet'
            when lower(device_type) like '%desktop%' or lower(device_type) like '%computer%' then 'Desktop'
            else 'Other'
        end as device_category,
        
        -- Browser grouping
        case
            when lower(browser) like '%chrome%' then 'Chrome'
            when lower(browser) like '%safari%' then 'Safari'
            when lower(browser) like '%firefox%' then 'Firefox'
            when lower(browser) like '%edge%' then 'Edge'
            else 'Other'
        end as browser_family,
        
        -- Time-based dimensions
        date(start_time) as session_date,
        extract(hour from start_time) as session_hour,
        extract(dow from start_time) as session_day_of_week,
        
        case
            when extract(dow from start_time) in (0, 6) then 'Weekend'
            else 'Weekday'
        end as day_type,
        
        case
            when extract(hour from start_time) between 6 and 11 then 'Morning'
            when extract(hour from start_time) between 12 and 17 then 'Afternoon'
            when extract(hour from start_time) between 18 and 22 then 'Evening'
            else 'Night'
        end as time_of_day,
        
        -- Session quality score
        case
            when duration_seconds > 0 then
                least(100, 
                    (duration_seconds / 10) +  -- Time component
                    (page_views * 5) +          -- Page view component
                    (actions_taken * 3)         -- Action component
                )
            else 0
        end as session_quality_score,
        
        -- Data quality flags
        case 
            when start_time is null then true 
            else false 
        end as missing_start_time,
        
        case 
            when duration_seconds is null or duration_seconds < 0 then true 
            else false 
        end as invalid_duration,
        
        case 
            when end_time < start_time then true 
            else false 
        end as invalid_time_sequence,
        
        -- Timestamps
        created_at as record_created_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
