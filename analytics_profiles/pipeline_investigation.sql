-- DATA PIPELINE INVESTIGATION: Tracing the Data Flow
-- ==================================================

\echo '============================================='
\echo 'DATA PIPELINE INVESTIGATION: TRACING THE FLOW'
\echo '============================================='
\echo ''

-- Check what schemas exist
\echo 'DATABASE SCHEMAS:'
\echo '----------------'
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;

-- Count records in each layer
\echo ''
\echo 'RECORD COUNTS BY LAYER:'
\echo '----------------------'

WITH layer_counts AS (
    SELECT 'staging' as layer, 'customers' as entity, COUNT(*) as count
    FROM staging.stg_marketing__marketing_qualified_leads
    
    UNION ALL
    
    SELECT 'intermediate', 'customers', COUNT(*)
    FROM intermediate.int_customers__core
    
    UNION ALL
    
    SELECT 'entity', 'customers', COUNT(*)
    FROM entity.entity_customers
    
    UNION ALL
    
    SELECT 'entity', 'devices', COUNT(*)
    FROM entity.entity_devices
    
    UNION ALL
    
    SELECT 'entity', 'users', COUNT(*)
    FROM entity.entity_users
    
    UNION ALL
    
    SELECT 'entity', 'subscriptions', COUNT(*)
    FROM entity.entity_subscriptions
)
SELECT layer, entity, count
FROM layer_counts
ORDER BY layer, entity;

-- Check intermediate customer data
\echo ''
\echo 'INTERMEDIATE CUSTOMER DATA CHECK:'
\echo '--------------------------------'

SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT account_id) as unique_accounts
FROM intermediate.int_customers__core
LIMIT 10;

-- Sample intermediate customer records
\echo ''
\echo 'SAMPLE INTERMEDIATE CUSTOMER DATA:'
\echo '---------------------------------'

SELECT 
    account_id,
    account_name,
    customer_status,
    monthly_recurring_revenue
FROM intermediate.int_customers__core
ORDER BY account_id
LIMIT 10;

-- Check for account_id mismatches
\echo ''
\echo 'ACCOUNT ID INVESTIGATION:'
\echo '------------------------'

-- Get sample account IDs from each entity
WITH customer_ids AS (
    SELECT DISTINCT account_id::text as id, 'customers' as source
    FROM entity.entity_customers
    LIMIT 5
),
subscription_ids AS (
    SELECT DISTINCT account_id::text as id, 'subscriptions' as source
    FROM entity.entity_subscriptions
    WHERE account_id IS NOT NULL
    LIMIT 5
),
user_ids AS (
    SELECT DISTINCT account_id::text as id, 'users' as source
    FROM entity.entity_users
    WHERE account_id IS NOT NULL
    LIMIT 5
),
location_ids AS (
    SELECT DISTINCT account_id as id, 'locations' as source
    FROM entity.entity_locations
    WHERE account_id IS NOT NULL
    LIMIT 5
)
SELECT * FROM customer_ids
UNION ALL
SELECT * FROM subscription_ids
UNION ALL
SELECT * FROM user_ids
UNION ALL
SELECT * FROM location_ids
ORDER BY source, id;

-- Check subscription account IDs that don't match customers
\echo ''
\echo 'ORPHANED SUBSCRIPTIONS (No matching customer):'
\echo '---------------------------------------------'

SELECT 
    s.account_id as subscription_account_id,
    s.subscription_status,
    s.monthly_recurring_revenue,
    s.plan_type
FROM entity.entity_subscriptions s
LEFT JOIN entity.entity_customers c 
    ON s.account_id::text = c.account_id::text
WHERE c.account_id IS NULL
    AND s.monthly_recurring_revenue > 0
ORDER BY s.monthly_recurring_revenue DESC
LIMIT 20;

-- Check data types in detail
\echo ''
\echo 'DATA TYPE MISMATCHES:'
\echo '--------------------'

SELECT 
    'customers' as entity,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'entity' 
    AND table_name = 'entity_customers'
    AND column_name = 'account_id'
UNION ALL
SELECT 
    'subscriptions',
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'entity' 
    AND table_name = 'entity_subscriptions'
    AND column_name = 'account_id'
UNION ALL
SELECT 
    'users',
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'entity' 
    AND table_name = 'entity_users'
    AND column_name = 'account_id'
UNION ALL
SELECT 
    'locations',
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'entity' 
    AND table_name = 'entity_locations'
    AND column_name = 'account_id';

-- Final summary
\echo ''
\echo 'PIPELINE HEALTH SUMMARY:'
\echo '-----------------------'

SELECT 
    'Customers with $0 MRR' as issue,
    COUNT(*) as count,
    '100%' as percentage
FROM entity.entity_customers
WHERE monthly_recurring_revenue = 0

UNION ALL

SELECT 
    'Subscriptions with >$0 MRR',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM entity.entity_subscriptions), 2)::text || '%'
FROM entity.entity_subscriptions
WHERE monthly_recurring_revenue > 0

UNION ALL

SELECT 
    'Devices with health < 1',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM entity.entity_devices), 2)::text || '%'
FROM entity.entity_devices
WHERE overall_health_score < 1

UNION ALL

SELECT 
    'Customer-Subscription Join Success',
    COUNT(DISTINCT c.account_id),
    ROUND(100.0 * COUNT(DISTINCT c.account_id) / (SELECT COUNT(*) FROM entity.entity_customers), 2)::text || '%'
FROM entity.entity_customers c
INNER JOIN entity.entity_subscriptions s 
    ON c.account_id::text = s.account_id::text;
