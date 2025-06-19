-- Simple Data Normalization Status Check

-- Entity tables record count
SELECT 
    'Entity Tables' AS category,
    'entity.entity_customers' AS table_name, 
    COUNT(*) AS records 
FROM entity.entity_customers
UNION ALL
SELECT 'Entity Tables', 'entity.entity_subscriptions', COUNT(*) FROM entity.entity_subscriptions
UNION ALL
SELECT 'Entity Tables', 'entity.entity_users', COUNT(*) FROM entity.entity_users
UNION ALL
SELECT 'Entity Tables', 'entity.entity_locations', COUNT(*) FROM entity.entity_locations
UNION ALL
SELECT 'Entity Tables', 'entity.entity_devices', COUNT(*) FROM entity.entity_devices;

-- Normalized tables that exist
SELECT 
    'Normalized Tables' AS category,
    table_name,
    (SELECT COUNT(*) FROM normalized.subscriptions) AS records
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_name = 'subscriptions'
UNION ALL
SELECT 
    'Normalized Tables',
    table_name,
    (SELECT COUNT(*) FROM normalized.account_id_mapping)
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_name = 'account_id_mapping';

-- Check MRR distribution in normalized subscriptions
SELECT 
    'MRR Analysis' AS analysis,
    COUNT(*) AS total_subscriptions,
    COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) AS with_revenue,
    SUM(monthly_recurring_revenue) AS total_mrr,
    AVG(monthly_recurring_revenue) AS avg_mrr,
    MAX(monthly_recurring_revenue) AS max_mrr
FROM normalized.subscriptions;

-- Check account ID reconciliation
SELECT 
    'ID Reconciliation' AS analysis,
    COUNT(DISTINCT account_id) AS unique_accounts,
    COUNT(DISTINCT subscription_id) AS unique_subscriptions,
    COUNT(*) AS total_records
FROM normalized.subscriptions;
