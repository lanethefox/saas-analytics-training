{{ config(
    materialized='table',
    schema='staging'
) }}

WITH source AS (
    SELECT * FROM {{ source('marketing', 'google_analytics_sessions') }}
),

renamed AS (
    SELECT
        -- Primary Key (using date + surrogate key)
        date AS session_date,
        {{ dbt_utils.generate_surrogate_key(['date']) }} AS session_id,
        
        -- Session Metrics
        sessions,
        users,
        new_users,
        COALESCE(page_views, pageviews) AS page_views, -- Handle both column names
        bounce_rate,
        avg_session_duration,
        
        -- Goal & Conversion Metrics
        goal_completions,
        goal_conversion_rate,
        
        -- Revenue Metrics
        revenue,
        transactions,
        
        -- Calculated Metrics
        CASE 
            WHEN sessions > 0 THEN new_users::float / sessions * 100 
            ELSE 0 
        END AS new_user_rate,
        
        CASE 
            WHEN sessions > 0 THEN page_views::float / sessions 
            ELSE 0 
        END AS pages_per_session,
        
        CASE 
            WHEN transactions > 0 THEN revenue / transactions 
            ELSE 0 
        END AS avg_transaction_value,
        
        -- Dimensions
        device_category,
        traffic_sources,
        
        -- Timestamps
        created_at,
        
        -- Audit
        CURRENT_TIMESTAMP AS _loaded_at
        
    FROM source
)

SELECT * FROM renamed