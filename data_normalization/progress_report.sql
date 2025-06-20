-- Data Normalization Progress Report

-- 1. Check all normalized tables
SELECT 
    'Successfully Normalized Tables' AS status;

SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size('normalized.' || table_name)) AS table_size
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 2. Record counts for each normalized table
SELECT 
    'Record Counts' AS status;

-- Check each table individually to avoid errors
SELECT 'account_id_mapping' AS table_name, COUNT(*) AS records FROM normalized.account_id_mapping
UNION ALL
SELECT 'customers', COUNT(*) FROM normalized.customers  
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM normalized.subscriptions
UNION ALL
SELECT 'locations', COUNT(*) FROM normalized.locations
UNION ALL
SELECT 'devices', COUNT(*) FROM normalized.devices
ORDER BY table_name;

-- 3. ID reconciliation effectiveness
SELECT 
    'ID Reconciliation Summary' AS status;

SELECT 
    COUNT(DISTINCT normalized_account_id) AS unique_accounts,
    COUNT(*) AS total_mappings,
    AVG(confidence_score) AS avg_confidence
FROM normalized.account_id_mapping;

-- 4. Revenue normalization check
SELECT 
    'Revenue Distribution' AS status;

SELECT 
    plan_tier,
    COUNT(*) AS subscriptions,
    SUM(monthly_recurring_revenue) AS total_mrr,
    AVG(monthly_recurring_revenue) AS avg_mrr,
    MIN(monthly_recurring_revenue) AS min_mrr,
    MAX(monthly_recurring_revenue) AS max_mrr
FROM normalized.subscriptions
GROUP BY plan_tier
ORDER BY plan_tier;

-- 5. Device health normalization
SELECT 
    'Device Health Distribution' AS status;

SELECT 
    device_type,
    COUNT(*) AS device_count,
    AVG(health_score)::NUMERIC(4,2) AS avg_health,
    MIN(health_score)::NUMERIC(4,2) AS min_health,
    MAX(health_score)::NUMERIC(4,2) AS max_health
FROM normalized.devices
GROUP BY device_type
ORDER BY device_count DESC
LIMIT 10;

-- 6. Location coverage
SELECT 
    'Location Coverage by Account' AS status;

SELECT 
    COUNT(DISTINCT account_id) AS accounts_with_locations,
    COUNT(*) AS total_locations,
    AVG(location_count) AS avg_locations_per_account
FROM (
    SELECT account_id, COUNT(*) AS location_count
    FROM normalized.locations
    GROUP BY account_id
) AS location_counts;

-- 7. Overall normalization progress
SELECT 
    'Normalization Progress Summary' AS status;

WITH target_tables AS (
    SELECT unnest(ARRAY['customers', 'subscriptions', 'users', 'locations', 'devices', 'campaigns', 'features']) AS table_name
),
existing_tables AS (
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'normalized'
    AND table_type = 'BASE TABLE'
)
SELECT 
    COUNT(DISTINCT e.table_name) AS tables_created,
    COUNT(DISTINCT t.table_name) AS target_tables,
    ROUND(COUNT(DISTINCT e.table_name)::NUMERIC / COUNT(DISTINCT t.table_name) * 100, 1) AS completion_percentage
FROM target_tables t
LEFT JOIN existing_tables e ON t.table_name = e.table_name;
