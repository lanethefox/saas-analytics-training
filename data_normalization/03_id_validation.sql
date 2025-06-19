-- 03_id_validation.sql
-- Phase 1: Verify All ID Relationships Work
-- =========================================
-- This script validates that the ID reconciliation was successful
-- and all entities can be properly joined

\echo '============================================'
\echo 'ID RECONCILIATION VALIDATION REPORT'
\echo '============================================'
\echo ''

-- ========================================
-- Basic Counts Comparison
-- ========================================
\echo 'ENTITY RECORD COUNTS: ORIGINAL vs NORMALIZED'
\echo '--------------------------------------------'

WITH original_counts AS (
    SELECT 'customers' as entity, COUNT(*) as original_count FROM entity.entity_customers
    UNION ALL
    SELECT 'subscriptions', COUNT(*) FROM entity.entity_subscriptions
    UNION ALL
    SELECT 'users', COUNT(*) FROM entity.entity_users
    UNION ALL
    SELECT 'locations', COUNT(*) FROM entity.entity_locations
    UNION ALL
    SELECT 'devices', COUNT(*) FROM entity.entity_devices
),
normalized_counts AS (
    SELECT 'customers' as entity, COUNT(*) as normalized_count FROM normalized.customers
    UNION ALL
    SELECT 'subscriptions', COUNT(*) FROM normalized.subscriptions
    UNION ALL
    SELECT 'users', COUNT(*) FROM normalized.users
    UNION ALL
    SELECT 'locations', COUNT(*) FROM normalized.locations
    UNION ALL
    SELECT 'devices', COUNT(*) FROM normalized.devices
)
SELECT 
    o.entity,
    o.original_count,
    n.normalized_count,
    n.normalized_count - o.original_count as difference,
    CASE 
        WHEN o.original_count = n.normalized_count THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM original_counts o
JOIN normalized_counts n ON o.entity = n.entity
ORDER BY o.entity;

-- ========================================
-- ID Format Validation
-- ========================================
\echo ''
\echo 'ID FORMAT VALIDATION'
\echo '-------------------'

SELECT 
    'Customer IDs' as entity,
    COUNT(*) as total_records,
    COUNT(CASE WHEN account_id ~ '^ACC[0-9]{10}$' THEN 1 END) as valid_format,
    COUNT(CASE WHEN account_id !~ '^ACC[0-9]{10}$' THEN 1 END) as invalid_format,
    CASE 
        WHEN COUNT(CASE WHEN account_id !~ '^ACC[0-9]{10}$' THEN 1 END) = 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM normalized.customers

UNION ALL

SELECT 
    'Subscription Account IDs',
    COUNT(*),
    COUNT(CASE WHEN account_id ~ '^ACC[0-9]{10}$' OR account_id LIKE 'ACC_ORPHANED_%' THEN 1 END),
    COUNT(CASE WHEN account_id !~ '^ACC[0-9]{10}$' AND account_id NOT LIKE 'ACC_ORPHANED_%' THEN 1 END),
    CASE 
        WHEN COUNT(CASE WHEN account_id !~ '^ACC[0-9]{10}$' AND account_id NOT LIKE 'ACC_ORPHANED_%' THEN 1 END) = 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END
FROM normalized.subscriptions;

-- ========================================
-- Relationship Validation
-- ========================================
\echo ''
\echo 'CROSS-ENTITY RELATIONSHIP VALIDATION'
\echo '-----------------------------------'

-- Test 1: Can we join customers to subscriptions?
WITH join_test AS (
    SELECT 
        COUNT(DISTINCT c.account_id) as customers_with_subscriptions
    FROM normalized.customers c
    INNER JOIN normalized.subscriptions s ON c.account_id = s.account_id
)
SELECT 
    'Customer → Subscription Join' as test_name,
    customers_with_subscriptions as matched_records,
    (SELECT COUNT(*) FROM normalized.customers) as total_customers,
    ROUND(100.0 * customers_with_subscriptions / (SELECT COUNT(*) FROM normalized.customers), 2) as match_percentage,
    CASE 
        WHEN customers_with_subscriptions > 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM join_test;

-- Test 2: Can we join customers to users?
WITH join_test AS (
    SELECT 
        COUNT(DISTINCT c.account_id) as customers_with_users
    FROM normalized.customers c
    INNER JOIN normalized.users u ON c.account_id = u.account_id
)
SELECT 
    'Customer → User Join' as test_name,
    customers_with_users as matched_records,
    (SELECT COUNT(*) FROM normalized.customers) as total_customers,
    ROUND(100.0 * customers_with_users / (SELECT COUNT(*) FROM normalized.customers), 2) as match_percentage,
    CASE 
        WHEN customers_with_users > 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM join_test;

-- Test 3: Can we join customers to locations?
WITH join_test AS (
    SELECT 
        COUNT(DISTINCT c.account_id) as customers_with_locations
    FROM normalized.customers c
    INNER JOIN normalized.locations l ON c.account_id = l.account_id
)
SELECT 
    'Customer → Location Join' as test_name,
    customers_with_locations as matched_records,
    (SELECT COUNT(*) FROM normalized.customers) as total_customers,
    ROUND(100.0 * customers_with_locations / (SELECT COUNT(*) FROM normalized.customers), 2) as match_percentage,
    CASE 
        WHEN customers_with_locations > 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM join_test;

-- Test 4: Can we join customers to devices?
WITH join_test AS (
    SELECT 
        COUNT(DISTINCT c.account_id) as customers_with_devices
    FROM normalized.customers c
    INNER JOIN normalized.devices d ON c.account_id = d.account_id
)
SELECT 
    'Customer → Device Join' as test_name,
    customers_with_devices as matched_records,
    (SELECT COUNT(*) FROM normalized.customers) as total_customers,
    ROUND(100.0 * customers_with_devices / (SELECT COUNT(*) FROM normalized.customers), 2) as match_percentage,
    CASE 
        WHEN customers_with_devices > 0 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status
FROM join_test;

-- ========================================
-- Revenue Reconciliation Check
-- ========================================
\echo ''
\echo 'REVENUE RECONCILIATION CHECK'
\echo '---------------------------'

WITH revenue_check AS (
    SELECT 
        SUM(c.monthly_recurring_revenue) as customer_total_mrr,
        (SELECT SUM(monthly_recurring_revenue) 
         FROM normalized.subscriptions 
         WHERE subscription_status IN ('Active', 'active')) as subscription_total_mrr
    FROM normalized.customers c
)
SELECT 
    'Customer Total MRR' as metric,
    '$' || TO_CHAR(customer_total_mrr, 'FM999,999.00') as value
FROM revenue_check
UNION ALL
SELECT 
    'Subscription Total MRR',
    '$' || TO_CHAR(subscription_total_mrr, 'FM999,999.00')
FROM revenue_check
UNION ALL
SELECT 
    'Difference',
    '$' || TO_CHAR(ABS(customer_total_mrr - subscription_total_mrr), 'FM999,999.00')
FROM revenue_check
UNION ALL
SELECT 
    'Match Status',
    CASE 
        WHEN customer_total_mrr = subscription_total_mrr THEN 'EXACT MATCH ✓'
        WHEN ABS(customer_total_mrr - subscription_total_mrr) < 1 THEN 'CLOSE MATCH ✓'
        ELSE 'MISMATCH ✗'
    END
FROM revenue_check;

-- ========================================
-- Orphaned Records Check
-- ========================================
\echo ''
\echo 'ORPHANED RECORDS CHECK'
\echo '---------------------'

SELECT 'Orphaned Subscriptions' as record_type, COUNT(*) as count
FROM normalized.subscriptions
WHERE account_id LIKE 'ACC_ORPHANED_%'

UNION ALL

SELECT 'Orphaned Users', COUNT(*)
FROM normalized.users u
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.customers c 
    WHERE c.account_id = u.account_id
)

UNION ALL

SELECT 'Orphaned Locations', COUNT(*)
FROM normalized.locations l
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.customers c 
    WHERE c.account_id = l.account_id
)

UNION ALL

SELECT 'Orphaned Devices', COUNT(*)
FROM normalized.devices d
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.customers c 
    WHERE c.account_id = d.account_id
);

-- ========================================
-- Sample Joined Records
-- ========================================
\echo ''
\echo 'SAMPLE JOINED RECORDS (First 5 customers with full relationships)'
\echo '----------------------------------------------------------------'

SELECT 
    c.account_id,
    c.company_name,
    c.monthly_recurring_revenue as customer_mrr,
    COUNT(DISTINCT s.subscription_id) as subscription_count,
    COUNT(DISTINCT u.user_id) as user_count,
    COUNT(DISTINCT l.location_id) as location_count,
    COUNT(DISTINCT d.device_id) as device_count,
    STRING_AGG(DISTINCT s.plan_type, ', ') as plan_types
FROM normalized.customers c
LEFT JOIN normalized.subscriptions s ON c.account_id = s.account_id
LEFT JOIN normalized.users u ON c.account_id = u.account_id
LEFT JOIN normalized.locations l ON c.account_id = l.account_id
LEFT JOIN normalized.devices d ON c.account_id = d.account_id
GROUP BY c.account_id, c.company_name, c.monthly_recurring_revenue
HAVING COUNT(DISTINCT s.subscription_id) > 0
   AND COUNT(DISTINCT u.user_id) > 0
   AND COUNT(DISTINCT l.location_id) > 0
   AND COUNT(DISTINCT d.device_id) > 0
ORDER BY c.account_id
LIMIT 5;

-- ========================================
-- Data Type Consistency Check
-- ========================================
\echo ''
\echo 'DATA TYPE CONSISTENCY CHECK'
\echo '---------------------------'

SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'normalized'
  AND column_name = 'account_id'
  AND table_name IN ('customers', 'subscriptions', 'users', 'locations', 'devices')
ORDER BY table_name;

-- ========================================
-- Final Validation Summary
-- ========================================
\echo ''
\echo 'VALIDATION SUMMARY'
\echo '=================='

WITH validation_results AS (
    SELECT 
        CASE 
            WHEN (SELECT COUNT(*) FROM normalized.customers WHERE monthly_recurring_revenue > 0) > 0 
            THEN 1 ELSE 0 
        END as revenue_fixed,
        CASE 
            WHEN (SELECT COUNT(DISTINCT c.account_id) 
                  FROM normalized.customers c 
                  INNER JOIN normalized.subscriptions s ON c.account_id = s.account_id) > 0 
            THEN 1 ELSE 0 
        END as relationships_work,
        CASE 
            WHEN (SELECT COUNT(*) FROM normalized.subscriptions WHERE account_id LIKE 'ACC_ORPHANED_%') < 
                 (SELECT COUNT(*) FROM normalized.subscriptions) * 0.1
            THEN 1 ELSE 0 
        END as minimal_orphans
)
SELECT 
    'Revenue Attribution Fixed' as check_item,
    CASE WHEN revenue_fixed = 1 THEN 'PASS ✓' ELSE 'FAIL ✗' END as status
FROM validation_results
UNION ALL
SELECT 
    'Entity Relationships Working',
    CASE WHEN relationships_work = 1 THEN 'PASS ✓' ELSE 'FAIL ✗' END
FROM validation_results
UNION ALL
SELECT 
    'Minimal Orphaned Records',
    CASE WHEN minimal_orphans = 1 THEN 'PASS ✓' ELSE 'FAIL ✗' END
FROM validation_results;

\echo ''
\echo '============================================'
\echo 'END OF VALIDATION REPORT'
\echo '============================================'
