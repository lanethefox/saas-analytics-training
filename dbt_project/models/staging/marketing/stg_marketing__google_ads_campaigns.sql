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
        type AS campaign_subtype,
        advertising_channel_type,
        campaign_objective,
        
        -- Budget Information
        budget_amount,
        target_cpa,
        budget AS budget_details,
        
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
        targeting_settings,
        performance_stats,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed