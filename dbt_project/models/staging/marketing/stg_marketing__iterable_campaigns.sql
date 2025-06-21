{{ config(
    materialized='table',
    schema='staging'
) }}

WITH source AS (
    SELECT * FROM {{ source('marketing', 'iterable_campaigns') }}
),

renamed AS (
    SELECT
        -- Primary Key
        id AS campaign_id,
        
        -- Campaign Details
        name AS campaign_name,
        campaign_type,
        status AS campaign_status,
        message_medium,
        labels,
        
        -- Audience Information
        send_size,
        NULL::integer as list_size,  -- Column doesn't exist
        
        -- Date/Time Fields
        created_at_source,
        updated_at_source,
        start_at,
        ended_at,
        NULL::timestamp as send_date,  -- Column doesn't exist
        
        -- JSON Fields (columns don't exist)
        NULL::jsonb as metrics,
        NULL::jsonb as performance_stats,
        NULL::jsonb as segment_info,
        
        -- Calculated Fields
        -- send_rate not calculated due to missing list_size
        0::numeric AS send_rate,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed