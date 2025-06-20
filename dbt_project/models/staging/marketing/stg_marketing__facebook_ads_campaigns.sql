{{ config(
    materialized='table',
    schema='staging'
) }}

WITH source AS (
    SELECT * FROM {{ source('marketing', 'facebook_ads_campaigns') }}
),

renamed AS (
    SELECT
        -- Primary Key
        id AS campaign_id,
        
        -- Campaign Details
        name AS campaign_name,
        status AS campaign_status,
        objective,
        NULL::text as bid_strategy,  -- Column doesn't exist
        
        -- Budget Information
        daily_budget,
        lifetime_budget,
        
        -- Performance Metrics
        impressions,
        clicks,
        spend,
        
        -- Calculated Metrics
        CASE 
            WHEN impressions > 0 THEN clicks::float / impressions * 100 
            ELSE 0 
        END AS click_through_rate,
        
        CASE 
            WHEN clicks > 0 THEN spend / clicks 
            ELSE 0 
        END AS cost_per_click,
        
        -- JSON Fields
        actions,
        NULL::jsonb as targeting,  -- Column doesn't exist
        NULL::jsonb as performance_stats,  -- Column doesn't exist
        
        -- Timestamps
        created_time,
        start_time,
        stop_time,
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed