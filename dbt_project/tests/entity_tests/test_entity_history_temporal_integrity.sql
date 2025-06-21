-- Test all entity history tables for temporal integrity
WITH history_validation AS (
    -- Customers History
    SELECT 
        'entity_customers_history' AS table_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN valid_from > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_valid_from,
        SUM(CASE WHEN valid_to < valid_from THEN 1 ELSE 0 END) AS invalid_date_range,
        SUM(CASE WHEN is_current = TRUE AND valid_to IS NOT NULL THEN 1 ELSE 0 END) AS invalid_current_flag
    FROM {{ ref('entity_customers_history') }}
    
    UNION ALL
    
    -- Devices History
    SELECT 
        'entity_devices_history' AS table_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN event_timestamp > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_valid_from,
        SUM(CASE WHEN event_type NOT IN ('created', 'updated', 'maintenance', 'failure', 'recovered') THEN 1 ELSE 0 END) AS invalid_date_range,
        SUM(CASE WHEN is_current = TRUE AND valid_to IS NOT NULL THEN 1 ELSE 0 END) AS invalid_current_flag
    FROM {{ ref('entity_devices_history') }}
    
    UNION ALL
    
    -- Users History
    SELECT 
        'entity_users_history' AS table_name,
        COUNT(*) AS total_records,
        SUM(CASE WHEN valid_from > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_valid_from,
        SUM(CASE WHEN valid_to < valid_from THEN 1 ELSE 0 END) AS invalid_date_range,
        SUM(CASE WHEN is_current = TRUE AND valid_to IS NOT NULL THEN 1 ELSE 0 END) AS invalid_current_flag
    FROM {{ ref('entity_users_history') }}
),
overlapping_periods AS (
    -- Check for overlapping history periods (customers)
    SELECT 
        COUNT(*) AS overlapping_customers
    FROM {{ ref('entity_customers_history') }} h1
    JOIN {{ ref('entity_customers_history') }} h2
        ON h1.account_id = h2.account_id
        AND h1.customer_history_id != h2.customer_history_id
        AND h1.valid_from < h2.valid_to
        AND h2.valid_from < h1.valid_to
),
history_issues AS (
    SELECT 
        h.*,
        op.overlapping_customers
    FROM history_validation h
    CROSS JOIN overlapping_periods op
    WHERE h.future_valid_from > 0
       OR h.invalid_date_range > 0
       OR h.invalid_current_flag > 0
       OR op.overlapping_customers > 0
)
-- Test fails if history tables have temporal integrity issues
SELECT * FROM history_issues