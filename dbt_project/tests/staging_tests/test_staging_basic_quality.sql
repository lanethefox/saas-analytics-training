-- Test all staging models for basic data quality
WITH staging_validation AS (
    -- App Database staging tests
    SELECT 'stg_app_database__accounts' AS model_name, COUNT(*) AS row_count, COUNT(*) - COUNT(DISTINCT account_id) AS duplicates
    FROM {{ ref('stg_app_database__accounts') }}
    
    UNION ALL
    
    SELECT 'stg_app_database__devices' AS model_name, COUNT(*) AS row_count, COUNT(*) - COUNT(DISTINCT device_id) AS duplicates
    FROM {{ ref('stg_app_database__devices') }}
    
    UNION ALL
    
    SELECT 'stg_app_database__locations' AS model_name, COUNT(*) AS row_count, COUNT(*) - COUNT(DISTINCT location_id) AS duplicates
    FROM {{ ref('stg_app_database__locations') }}
    
    UNION ALL
    
    SELECT 'stg_app_database__users' AS model_name, COUNT(*) AS row_count, COUNT(*) - COUNT(DISTINCT user_id) AS duplicates
    FROM {{ ref('stg_app_database__users') }}
    
    UNION ALL
    
    SELECT 'stg_app_database__subscriptions' AS model_name, COUNT(*) AS row_count, COUNT(*) - COUNT(DISTINCT subscription_id) AS duplicates
    FROM {{ ref('stg_app_database__subscriptions') }}
),
empty_models AS (
    SELECT *
    FROM staging_validation
    WHERE row_count = 0
),
duplicate_records AS (
    SELECT *
    FROM staging_validation
    WHERE duplicates > 0
)
-- Test fails if any staging models are empty or have duplicates
SELECT 
    (SELECT COUNT(*) FROM empty_models) AS empty_model_count,
    (SELECT COUNT(*) FROM duplicate_records) AS models_with_duplicates,
    (SELECT STRING_AGG(model_name, ', ') FROM empty_models) AS empty_models_list,
    (SELECT STRING_AGG(model_name || ' (' || duplicates || ')', ', ') FROM duplicate_records) AS duplicate_details
WHERE (SELECT COUNT(*) FROM empty_models) > 0
   OR (SELECT COUNT(*) FROM duplicate_records) > 0