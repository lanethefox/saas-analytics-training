{{ config(
    materialized='table',
    schema='staging'
) }}

WITH source AS (
    SELECT * FROM {{ source('marketing', 'google_ads_campaigns') }}
),

renamed AS (
    SELECT
        -- Primary Key
        id AS campaign_id,
        
        -- Campaign Details
        name AS campaign_name,
        status AS campaign_status,
        campaign_type,
        NULL::text AS campaign_subtype,  -- Column doesn't exist
        advertising_channel_type,
        NULL::text as campaign_objective,  -- Column doesn't exist
        
        -- Budget Information
        budget_amount,
        target_cpa,
        NULL::jsonb AS budget_details,  -- Column doesn't exist
        
        -- Date Range
        start_date,
        end_date,
        
        -- Performance Metrics
        impressions,
        clicks,
        cost,
        conversions,
        
        -- Calculated Metrics
        CASE 
            WHEN impressions > 0 THEN clicks::float / impressions * 100 
            ELSE 0 
        END AS click_through_rate,
        
        CASE 
            WHEN clicks > 0 THEN cost / clicks 
            ELSE 0 
        END AS cost_per_click,
        
        CASE 
            WHEN conversions > 0 THEN cost / conversions 
            ELSE 0 
        END AS cost_per_conversion,
        
        CASE 
            WHEN clicks > 0 THEN conversions / clicks * 100 
            ELSE 0 
        END AS conversion_rate,
        
        -- JSON Fields
        NULL::jsonb as targeting_settings,  -- Column doesn't exist
        NULL::jsonb as performance_stats,  -- Column doesn't exist
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed