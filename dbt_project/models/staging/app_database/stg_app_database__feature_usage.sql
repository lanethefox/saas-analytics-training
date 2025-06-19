{{ config(
    materialized='incremental',
    unique_key='usage_id',
    on_schema_change='fail'
) }}

-- Staging model for feature usage
-- Tracks premium feature adoption and usage patterns

with source_data as (
    select * from {{ source('app_database', 'feature_usage') }}
),

{% if is_incremental() %}
max_timestamp as (
    select max(usage_timestamp) as max_ts from {{ this }}
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
        usage_id,
        {{ dbt_utils.generate_surrogate_key(['usage_id']) }} as usage_key,
        user_id,
        customer_id as account_id,
        
        -- Feature information
        feature_name,
        usage_count,
        timestamp as usage_timestamp,
        
        -- Feature categorization
        case
            when lower(feature_name) like '%report%' then 'Reporting'
            when lower(feature_name) like '%analytics%' then 'Analytics'
            when lower(feature_name) like '%export%' then 'Data Export'
            when lower(feature_name) like '%api%' then 'API'
            when lower(feature_name) like '%integration%' then 'Integration'
            when lower(feature_name) like '%automation%' then 'Automation'
            when lower(feature_name) like '%alert%' or lower(feature_name) like '%notification%' then 'Alerts'
            when lower(feature_name) like '%dashboard%' then 'Dashboard'
            when lower(feature_name) like '%inventory%' then 'Inventory'
            when lower(feature_name) like '%forecast%' then 'Forecasting'
            else 'Other'
        end as feature_category,
        
        -- Feature tier
        case
            when lower(feature_name) like '%premium%' or lower(feature_name) like '%advanced%' then 'Premium'
            when lower(feature_name) like '%pro%' then 'Professional'
            when lower(feature_name) like '%basic%' or lower(feature_name) like '%standard%' then 'Standard'
            else 'Unknown'
        end as feature_tier,
        
        -- Usage intensity
        case
            when usage_count = 1 then 'First Use'
            when usage_count <= 5 then 'Light Usage'
            when usage_count <= 20 then 'Moderate Usage'
            when usage_count <= 50 then 'Heavy Usage'
            else 'Power User'
        end as usage_intensity,
        
        -- Time-based dimensions
        date(timestamp) as usage_date,
        extract(hour from timestamp) as usage_hour,
        extract(dow from timestamp) as usage_day_of_week,
        extract(week from timestamp) as usage_week,
        extract(month from timestamp) as usage_month,
        
        -- Business hours flag
        case
            when extract(hour from timestamp) between 9 and 17 
                and extract(dow from timestamp) between 1 and 5 then true
            else false
        end as is_business_hours,
        
        -- Feature value score (arbitrary scoring for demonstration)
        case
            when lower(feature_name) like '%analytics%' or lower(feature_name) like '%report%' then 10
            when lower(feature_name) like '%automation%' or lower(feature_name) like '%api%' then 8
            when lower(feature_name) like '%export%' or lower(feature_name) like '%integration%' then 6
            when lower(feature_name) like '%dashboard%' then 5
            else 3
        end * usage_count as feature_value_score,
        
        -- Adoption indicators
        case
            when usage_count = 1 then true
            else false
        end as is_first_use,
        
        case
            when usage_count > 10 then true
            else false
        end as is_adopted,
        
        -- Data quality flags
        case 
            when feature_name is null or trim(feature_name) = '' then true 
            else false 
        end as missing_feature_name,
        
        case 
            when usage_count is null or usage_count < 0 then true 
            else false 
        end as invalid_usage_count,
        
        -- Timestamps
        created_at as record_created_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from filtered_source
)

select * from enriched