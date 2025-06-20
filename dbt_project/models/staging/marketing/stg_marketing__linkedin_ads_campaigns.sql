{{ config(
    materialized='table',
    schema='staging'
) }}

WITH source AS (
    SELECT * FROM {{ source('marketing', 'linkedin_ads_campaigns') }}
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
        objective_type,
        NULL::text as cost_type,  -- Column doesn't exist
        
        -- Budget Information
        daily_budget,
        total_budget,
        NULL::jsonb AS budget_details,  -- Column doesn't exist
        
        -- Date Range
        start_date,
        end_date,
        
        -- Timestamp fields
        created_time,
        NULL::timestamp AS start_timestamp,  -- start_at column doesn't exist
        NULL::timestamp AS end_timestamp,  -- end_at column doesn't exist
        
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
            WHEN clicks > 0 THEN conversions::float / clicks * 100 
            ELSE 0 
        END AS conversion_rate,
        
        -- JSON Fields (columns don't exist)
        NULL::jsonb as targeting,
        NULL::jsonb as performance_stats,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed