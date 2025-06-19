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
        touchpoint_type,
        attribution_weight,
        
        -- Additional fields from actual schema
        campaign_name,
        medium,
        source,
        content,
        touchpoint_position,
        position_in_journey,
        interaction_details,
        
        -- Timestamps
        touchpoint_date as touchpoint_timestamp,
        created_at,
        
        -- Derived Fields
        case
            when touchpoint_type = 'first_touch' then 1.0
            when touchpoint_type = 'last_touch' then 1.0
            when touchpoint_type = 'linear' then attribution_weight
            when touchpoint_type = 'time_decay' then attribution_weight
            when touchpoint_type = 'position_based' and position_in_journey in (1, touchpoint_position) then 0.4
            when touchpoint_type = 'position_based' then 0.2 / nullif(attribution_weight, 0)
            else coalesce(attribution_weight, 0)
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
        case
            when touchpoint_type in ('first_touch', 'last_touch') then 'Single Touch'
            when touchpoint_type in ('linear', 'time_decay', 'position_based') then 'Multi Touch'
            else 'Custom'
        end as attribution_model_type,
        
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
