{{ config(
    materialized='incremental',
    unique_key='page_view_id',
    on_schema_change='fail'
) }}

-- Staging model for page views
-- Web analytics and user navigation tracking

with source_data as (
    select * from {{ source('app_database', 'page_views') }}
),

{% if is_incremental() %}
max_timestamp as (
    select max(page_view_timestamp) as max_ts from {{ this }}
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
        page_view_id,
        {{ dbt_utils.generate_surrogate_key(['page_view_id']) }} as page_view_key,
        session_id,
        user_id,
        customer_id as account_id,
        
        -- Page information
        page_url,
        page_title,
        referrer_url,
        
        -- URL parsing
        split_part(page_url, '/', 4) as page_path,
        split_part(page_url, '?', 1) as clean_url,
        
        -- Page categorization
        case
            when page_url like '%/dashboard%' then 'Dashboard'
            when page_url like '%/reports%' then 'Reports'
            when page_url like '%/settings%' then 'Settings'
            when page_url like '%/devices%' then 'Devices'
            when page_url like '%/locations%' then 'Locations'
            when page_url like '%/users%' then 'Users'
            when page_url like '%/analytics%' then 'Analytics'
            when page_url like '%/billing%' then 'Billing'
            when page_url like '%/support%' then 'Support'
            when page_url like '%/login%' or page_url like '%/auth%' then 'Authentication'
            when page_url = '/' or page_url like '%/home%' then 'Home'
            else 'Other'
        end as page_category,
        
        -- Engagement metrics
        timestamp as page_view_timestamp,
        time_on_page_seconds,
        
        case
            when time_on_page_seconds < 10 then 'Bounce'
            when time_on_page_seconds < 30 then 'Quick View'
            when time_on_page_seconds < 60 then 'Normal View'
            when time_on_page_seconds < 180 then 'Engaged View'
            else 'Deep Engagement'
        end as engagement_type,
        
        -- Referrer analysis
        case
            when referrer_url is null or referrer_url = '' then 'Direct'
            when referrer_url like '%google%' then 'Google'
            when referrer_url like '%facebook%' or referrer_url like '%fb.%' then 'Facebook'
            when referrer_url like '%linkedin%' then 'LinkedIn'
            when referrer_url like '%twitter%' or referrer_url like '%t.co%' then 'Twitter'
            when referrer_url like page_url then 'Internal'
            else 'External'
        end as referrer_source,
        
        -- Time-based dimensions
        date(timestamp) as page_view_date,
        extract(hour from timestamp) as page_view_hour,
        extract(dow from timestamp) as page_view_day_of_week,
        
        -- Page depth (simplified - counts slashes after domain)
        length(page_url) - length(replace(page_url, '/', '')) - 2 as page_depth,
        
        -- Exit page indicator (would need window functions for accurate calculation)
        false as is_exit_page, -- Placeholder, would need session analysis
        
        -- Page value score
        case
            when page_url like '%/billing%' or page_url like '%/upgrade%' then 100
            when page_url like '%/reports%' or page_url like '%/analytics%' then 80
            when page_url like '%/devices%' or page_url like '%/locations%' then 60
            when page_url like '%/dashboard%' then 50
            when page_url like '%/settings%' then 30
            else 10
        end as page_value_score,
        
        -- Data quality flags
        case 
            when page_url is null or trim(page_url) = '' then true 
            else false 
        end as missing_page_url,
        
        case 
            when time_on_page_seconds is null or time_on_page_seconds < 0 then true 
            else false 
        end as invalid_time_on_page,
        
        -- Timestamps
        created_at as record_created_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from filtered_source
)

select * from enriched