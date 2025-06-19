-- TECHNICAL VALIDATION SCRIPT: Data Quality Issues Demonstration
-- ==============================================================
-- This script provides specific examples of data quality issues
-- for engineering team investigation

\echo '======================================================='
\echo 'TECHNICAL VALIDATION: DATA QUALITY ISSUES DEMONSTRATION'
\echo '======================================================='
\echo ''

-- ========================================
-- ISSUE #1: Account ID Mismatch
-- ========================================
\echo 'ISSUE #1: ACCOUNT ID MISMATCH PREVENTING JOINS'
\echo '----------------------------------------------'
\echo ''

-- Show sample IDs from each entity
\echo 'Sample Account IDs by Entity:'
WITH id_samples AS (
    SELECT 'customers' as entity, MIN(account_id) as min_id, MAX(account_id) as max_id, COUNT(DISTINCT account_id) as unique_count
    FROM entity.entity_customers
    UNION ALL
    SELECT 'subscriptions', MIN(account_id), MAX(account_id), COUNT(DISTINCT account_id)
    FROM entity.entity_subscriptions
    WHERE account_id IS NOT NULL
)
SELECT entity, min_id, max_id, unique_count FROM id_samples;

\echo ''
\echo 'Attempting Join Between Customers and Subscriptions:'
SELECT 
    'Direct Join' as join_type,
    COUNT(*) as matches
FROM entity.entity_customers c
INNER JOIN entity.entity_subscriptions s ON c.account_id = s.account_id

UNION ALL

SELECT 
    'Cast to Text Join',
    COUNT(*)
FROM entity.entity_customers c
INNER JOIN entity.entity_subscriptions s ON c.account_id::text = s.account_id::text

UNION ALL

SELECT 
    'Loose Pattern Match',
    COUNT(*)
FROM entity.entity_customers c
INNER JOIN entity.entity_subscriptions s ON s.account_id LIKE '%' || c.account_id || '%';

-- Show specific examples
\echo ''
\echo 'Example Customer IDs vs Subscription IDs:'
SELECT 'Customer IDs' as source, STRING_AGG(account_id::text, ', ' ORDER BY account_id::text) as sample_ids
FROM (SELECT DISTINCT account_id FROM entity.entity_customers ORDER BY account_id LIMIT 10) c
UNION ALL
SELECT 'Subscription IDs', STRING_AGG(account_id::text, ', ' ORDER BY account_id::text)
FROM (SELECT DISTINCT account_id FROM entity.entity_subscriptions WHERE account_id IS NOT NULL ORDER BY account_id LIMIT 10) s;

-- ========================================
-- ISSUE #2: Device Health Score Problem
-- ========================================
\echo ''
\echo 'ISSUE #2: DEVICE HEALTH SCORES - ONLY TWO VALUES'
\echo '-----------------------------------------------'

-- Show distribution of health scores
SELECT 
    overall_health_score,
    COUNT(*) as device_count,
    MIN(device_installed_date) as earliest_install,
    MAX(device_installed_date) as latest_install,
    STRING_AGG(DISTINCT operational_status, ', ') as statuses
FROM entity.entity_devices
GROUP BY overall_health_score
ORDER BY overall_health_score;

-- Check if scores are being calculated
\echo ''
\echo 'Health Score Components Check:'
SELECT 
    COUNT(*) as total_devices,
    COUNT(DISTINCT overall_health_score) as unique_health_scores,
    COUNT(DISTINCT performance_score) as unique_performance_scores,
    COUNT(DISTINCT uptime_score) as unique_uptime_scores,
    COUNT(DISTINCT alert_score) as unique_alert_scores
FROM entity.entity_devices;

-- ========================================
-- ISSUE #3: Data Type Mismatches
-- ========================================
\echo ''
\echo 'ISSUE #3: DATA TYPE INCONSISTENCIES ACROSS ENTITIES'
\echo '--------------------------------------------------'

SELECT 
    c.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.numeric_precision
FROM information_schema.columns c
WHERE c.table_schema = 'entity'
    AND c.column_name = 'account_id'
    AND c.table_name IN ('entity_customers', 'entity_subscriptions', 'entity_users', 'entity_locations')
ORDER BY c.table_name;

-- ========================================
-- ISSUE #4: Zero MRR Investigation
-- ========================================
\echo ''
\echo 'ISSUE #4: ZERO MRR IN CUSTOMERS BUT POSITIVE IN SUBSCRIPTIONS'
\echo '------------------------------------------------------------'

-- Show MRR distribution
WITH mrr_analysis AS (
    SELECT 
        'Customers' as source,
        COUNT(*) as total_records,
        SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END) as zero_mrr_count,
        SUM(CASE WHEN monthly_recurring_revenue > 0 THEN 1 ELSE 0 END) as positive_mrr_count,
        MIN(monthly_recurring_revenue) as min_mrr,
        MAX(monthly_recurring_revenue) as max_mrr,
        SUM(monthly_recurring_revenue) as total_mrr
    FROM entity.entity_customers
    
    UNION ALL
    
    SELECT 
        'Subscriptions',
        COUNT(*),
        SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN monthly_recurring_revenue > 0 THEN 1 ELSE 0 END),
        MIN(monthly_recurring_revenue),
        MAX(monthly_recurring_revenue),
        SUM(monthly_recurring_revenue)
    FROM entity.entity_subscriptions
)
SELECT * FROM mrr_analysis;

-- Show subscriptions that should contribute to customer MRR
\echo ''
\echo 'Active Subscriptions with Positive MRR (Top 10):'
SELECT 
    subscription_id,
    account_id,
    subscription_status,
    plan_type,
    monthly_recurring_revenue,
    annual_recurring_revenue
FROM entity.entity_subscriptions
WHERE subscription_status IN ('Active', 'active')
    AND monthly_recurring_revenue > 0
ORDER BY monthly_recurring_revenue DESC
LIMIT 10;

-- ========================================
-- ISSUE #5: Historical Data Coverage
-- ========================================
\echo ''
\echo 'ISSUE #5: LIMITED HISTORICAL DATA'
\echo '--------------------------------'

SELECT 
    table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CASE 
        WHEN table_name LIKE '%customers%' THEN account_id::text
        WHEN table_name LIKE '%devices%' THEN device_id::text
        WHEN table_name LIKE '%users%' THEN user_id::text
    END) as unique_entities,
    MIN(valid_from)::date as min_date,
    MAX(COALESCE(valid_to, CURRENT_DATE))::date as max_date,
    (MAX(COALESCE(valid_to, CURRENT_DATE)) - MIN(valid_from))::integer as days_of_history
FROM (
    SELECT 'entity_customers_history' as table_name, account_id, NULL as device_id, NULL as user_id, valid_from, valid_to
    FROM entity.entity_customers_history
    UNION ALL
    SELECT 'entity_devices_history', NULL, device_id, NULL, valid_from, valid_to
    FROM entity.entity_devices_history
    UNION ALL
    SELECT 'entity_users_history', NULL, NULL, user_id, valid_from, valid_to
    FROM entity.entity_users_history
) history_data
GROUP BY table_name
ORDER BY days_of_history DESC;

-- ========================================
-- VALIDATION QUERIES FOR FIXES
-- ========================================
\echo ''
\echo 'VALIDATION QUERIES TO RUN AFTER FIXES:'
\echo '-------------------------------------'
\echo ''
\echo '1. After fixing account IDs, this should return 100:'
\echo '   SELECT COUNT(DISTINCT c.account_id) FROM entity.entity_customers c'
\echo '   INNER JOIN entity.entity_subscriptions s ON c.account_id = s.account_id;'
\echo ''
\echo '2. After fixing MRR calculation, this should return 0:'
\echo '   SELECT COUNT(*) FROM entity.entity_customers'
\echo '   WHERE customer_status = ''active'' AND monthly_recurring_revenue = 0;'
\echo ''
\echo '3. After fixing device health, this should return >2:'
\echo '   SELECT COUNT(DISTINCT overall_health_score) FROM entity.entity_devices;'
\echo ''
\echo '4. After fixing data types, this should return 1 row:'
\echo '   SELECT DISTINCT data_type FROM information_schema.columns'
\echo '   WHERE table_schema = ''entity'' AND column_name = ''account_id'';'

\echo ''
\echo '======================================================='
\echo 'END OF TECHNICAL VALIDATION SCRIPT'
\echo '======================================================='
