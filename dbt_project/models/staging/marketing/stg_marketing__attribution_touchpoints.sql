{{ config(
    materialized='view',
    tags=['marketing', 'attribution']
) }}

with source as (
    select * from {{ source('marketing', 'attribution_touchpoints') }}
),

renamed as (
    select
        -- IDs
        id as touchpoint_id,
        mql_id as lead_id,
        campaign_id,
        
        -- Attribution Details
        channel,
        NULL::text as touchpoint_type,  -- Column doesn't exist
        attribution_weight,
        
        -- Additional fields from actual schema
        campaign_name,
        medium,
        source,
        content,
        touchpoint_position,
        touchpoint_position as position_in_journey,
        NULL::jsonb as interaction_details,  -- Column doesn't exist
        
        -- Timestamps
        touchpoint_date as touchpoint_timestamp,
        created_at,
        
        -- Derived Fields
        case
            -- Since touchpoint_type doesn't exist, use attribution_weight directly
            when attribution_weight is not null then attribution_weight
            else 0.0
        end as normalized_attribution_weight,
        
        -- Channel Groupings
        case
            when lower(channel) like '%google%' then 'Google'
            when lower(channel) like '%meta%' or lower(channel) like '%facebook%' then 'Meta'
            when lower(channel) like '%linkedin%' then 'LinkedIn'
            when lower(channel) like '%email%' then 'Email'
            when lower(channel) like '%organic%' then 'Organic'
            when lower(channel) like '%direct%' then 'Direct'
            else 'Other'
        end as channel_group,
        
        -- Attribution Model Type
        -- Default to Multi Touch since touchpoint_type doesn't exist
        'Multi Touch' as attribution_model_type,
        
        -- Data Quality
        case
            when mql_id is null then 'Missing Lead ID'
            when channel is null then 'Missing Channel'
            when touchpoint_date is null then 'Missing Timestamp'
            else 'Valid'
        end as data_quality_flag,
        
        -- Audit Fields
        current_timestamp as _dbt_inserted_at

    from source
),

final as (
    select * from renamed
)

select * from final
