-- Test relationships between staging and intermediate models
WITH staging_to_intermediate AS (
    -- Check that all staging accounts appear in intermediate
    SELECT 
        'accounts_coverage' AS test_name,
        COUNT(DISTINCT s.account_id) AS staging_count,
        COUNT(DISTINCT i.account_id) AS intermediate_count,
        COUNT(DISTINCT s.account_id) - COUNT(DISTINCT i.account_id) AS missing_records
    FROM {{ ref('stg_app_database__accounts') }} s
    LEFT JOIN {{ ref('int_customers__core') }} i
        ON s.account_id = i.account_id
    
    UNION ALL
    
    -- Check that all staging users appear in intermediate
    SELECT 
        'users_coverage' AS test_name,
        COUNT(DISTINCT s.user_id) AS staging_count,
        COUNT(DISTINCT i.user_id) AS intermediate_count,
        COUNT(DISTINCT s.user_id) - COUNT(DISTINCT i.user_id) AS missing_records
    FROM {{ ref('stg_app_database__users') }} s
    LEFT JOIN {{ ref('int_users__core') }} i
        ON s.user_id = i.user_id
    
    UNION ALL
    
    -- Check that all staging subscriptions appear in intermediate
    SELECT 
        'subscriptions_coverage' AS test_name,
        COUNT(DISTINCT s.subscription_id) AS staging_count,
        COUNT(DISTINCT i.subscription_id) AS intermediate_count,
        COUNT(DISTINCT s.subscription_id) - COUNT(DISTINCT i.subscription_id) AS missing_records
    FROM {{ ref('stg_app_database__subscriptions') }} s
    LEFT JOIN {{ ref('int_subscriptions__core') }} i
        ON s.subscription_id = i.subscription_id
),
intermediate_to_entity AS (
    -- Check that all intermediate customers appear in entity
    SELECT 
        'customers_to_entity' AS test_name,
        COUNT(DISTINCT i.account_id) AS intermediate_count,
        COUNT(DISTINCT e.account_id) AS entity_count,
        COUNT(DISTINCT i.account_id) - COUNT(DISTINCT e.account_id) AS missing_records
    FROM {{ ref('int_customers__core') }} i
    LEFT JOIN {{ ref('entity_customers') }} e
        ON i.account_id = e.account_id
),
coverage_issues AS (
    SELECT *
    FROM staging_to_intermediate
    WHERE missing_records > 0
    
    UNION ALL
    
    SELECT *
    FROM intermediate_to_entity
    WHERE missing_records > 0
)
-- Test fails if records are lost between layers
SELECT * FROM coverage_issues