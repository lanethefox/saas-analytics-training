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
        list_size,
        
        -- Date/Time Fields
        created_at_source,
        updated_at_source,
        start_at,
        ended_at,
        send_date,
        
        -- JSON Fields
        metrics,
        performance_stats,
        segment_info,
        
        -- Calculated Fields
        CASE 
            WHEN list_size > 0 THEN send_size::float / list_size * 100 
            ELSE 0 
        END AS send_rate,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed