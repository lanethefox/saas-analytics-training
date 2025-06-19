{{ config(
    materialized='incremental',
    unique_key='engagement_id',
    on_schema_change='fail',
    tags=['hubspot', 'sales']
) }}

with source as (
    select * from {{ source('hubspot', 'engagements') }}
),

{% if is_incremental() %}
max_createdat as (
    select max(record_created_at) as max_created from {{ this }}
),

filtered_source as (
    select 
        source.*
    from source
    cross join max_createdat
    where source.createdat > max_createdat.max_created
),
{% else %}
filtered_source as (
    select * from source
),
{% endif %}

renamed as (
    select
        -- IDs
        id as engagement_id,
        
        -- Extract from engagement JSON
        engagement->>'type' as engagement_type,
        (engagement->>'timestamp')::bigint as engagement_timestamp_ms,
        engagement->>'active' as is_active,
        engagement->>'ownerId' as owner_id,
        engagement->>'teamId' as team_id,
        
        -- Extract from associations JSON
        associations->>'contactIds' as contact_ids,
        associations->>'companyIds' as company_ids,
        associations->>'dealIds' as deal_ids,
        
        -- Extract from metadata JSON based on type
        metadata->>'body' as engagement_body,
        metadata->>'subject' as engagement_subject,
        metadata->>'status' as engagement_status,
        metadata->>'durationMilliseconds' as duration_ms,
        
        -- Convert timestamp
        to_timestamp((engagement->>'timestamp')::bigint / 1000) as engagement_timestamp,
        
        -- Engagement Type Categorization
        case
            when lower(engagement->>'type') = 'email' then 'Email'
            when lower(engagement->>'type') = 'call' then 'Call'
            when lower(engagement->>'type') = 'meeting' then 'Meeting'
            when lower(engagement->>'type') = 'note' then 'Note'
            when lower(engagement->>'type') = 'task' then 'Task'
            else 'Other'
        end as engagement_category,
        
        -- Engagement Channel
        case
            when lower(engagement->>'type') in ('email') then 'Digital'
            when lower(engagement->>'type') in ('call', 'meeting') then 'Direct'
            when lower(engagement->>'type') in ('note', 'task') then 'Internal'
            else 'Other'
        end as engagement_channel,
        
        -- Time-based Dimensions
        date(to_timestamp((engagement->>'timestamp')::bigint / 1000)) as engagement_date,
        extract(hour from to_timestamp((engagement->>'timestamp')::bigint / 1000)) as engagement_hour,
        extract(dow from to_timestamp((engagement->>'timestamp')::bigint / 1000)) as engagement_day_of_week,
        
        -- Business Hours Flag
        case
            when extract(hour from to_timestamp((engagement->>'timestamp')::bigint / 1000)) between 9 and 17 
                and extract(dow from to_timestamp((engagement->>'timestamp')::bigint / 1000)) between 1 and 5 then true
            else false
        end as is_business_hours,
        
        -- Engagement Scoring (for sales activity metrics)
        case
            when lower(engagement->>'type') = 'meeting' then 10
            when lower(engagement->>'type') = 'call' then 5
            when lower(engagement->>'type') = 'email' then 3
            when lower(engagement->>'type') = 'task' then 2
            else 1
        end as engagement_score,
        
        -- Duration in minutes (if available)
        case
            when metadata->>'durationMilliseconds' ~ '^\d+$'
            then (metadata->>'durationMilliseconds')::bigint / 60000.0
            else null
        end as duration_minutes,
        
        -- Data Quality
        case
            when id is null then 'Missing Engagement ID'
            when engagement->>'type' is null then 'Missing Type'
            when engagement->>'timestamp' is null then 'Missing Timestamp'
            else 'Valid'
        end as data_quality_flag,
        
        -- Timestamps
        createdat as record_created_at,
        updatedat as record_updated_at,
        
        -- Audit Fields
        current_timestamp as _dbt_inserted_at

    from filtered_source
),

final as (
    select * from renamed
)

select * from final