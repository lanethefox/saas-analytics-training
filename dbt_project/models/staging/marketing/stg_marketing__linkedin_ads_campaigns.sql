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
        type AS campaign_subtype,
        objective_type,
        cost_type,
        
        -- Budget Information
        daily_budget,
        total_budget,
        budget AS budget_details,
        
        -- Date Range
        start_date,
        end_date,
        
        -- Timestamp fields (bigint to timestamp conversion if needed)
        created_time,
        CASE 
            WHEN start_at IS NOT NULL THEN to_timestamp(start_at::double precision / 1000)
            ELSE NULL
        END AS start_timestamp,
        CASE 
            WHEN end_at IS NOT NULL THEN to_timestamp(end_at::double precision / 1000)
            ELSE NULL
        END AS end_timestamp,
        
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
        
        -- JSON Fields
        targeting,
        performance_stats,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed