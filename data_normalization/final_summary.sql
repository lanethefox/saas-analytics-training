-- Final Data Normalization Summary Report

SELECT '===========================================' AS line;
SELECT 'DATA NORMALIZATION FINAL STATUS REPORT' AS title;
SELECT '===========================================' AS line;

-- 1. Overall Progress
SELECT 
    'NORMALIZATION PROGRESS' AS section,
    '' AS details;

WITH progress AS (
    SELECT 
        COUNT(*) FILTER (WHERE table_name IN ('customers', 'subscriptions', 'users', 'locations', 'devices', 'campaigns', 'features')) AS completed,
        7 AS total_target
    FROM information_schema.tables
    WHERE table_schema = 'normalized'
    AND table_type = 'BASE TABLE'
)
SELECT 
    completed || ' of ' || total_target || ' tables normalized' AS status,
    ROUND(completed::numeric / total_target * 100, 1) || '% complete' AS percentage
FROM progress;

-- 2. Successfully Normalized Tables
SELECT 
    '' AS blank,
    'SUCCESSFULLY NORMALIZED TABLES' AS section;

SELECT 
    table_name AS "Table",
    pg_size_pretty(pg_total_relation_size('normalized.' || table_name)) AS "Size",
    CASE table_name
        WHEN 'account_id_mapping' THEN (SELECT COUNT(*)::TEXT FROM normalized.account_id_mapping)
        WHEN 'customers' THEN (SELECT COUNT(*)::TEXT FROM normalized.customers)
        WHEN 'subscriptions' THEN (SELECT COUNT(*)::TEXT FROM normalized.subscriptions)
        WHEN 'locations' THEN (SELECT COUNT(*)::TEXT FROM normalized.locations)
        WHEN 'devices' THEN (SELECT COUNT(*)::TEXT FROM normalized.devices)
        ELSE 'N/A'
    END AS "Records"
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_type = 'BASE TABLE'
AND table_name IN ('account_id_mapping', 'customers', 'subscriptions', 'locations', 'devices')
ORDER BY table_name;

-- 3. Key Normalization Achievements
SELECT 
    '' AS blank,
    'KEY ACHIEVEMENTS' AS section;

-- ID Reconciliation
SELECT 
    'ID Reconciliation' AS achievement,
    COUNT(DISTINCT normalized_account_id) || ' unique accounts mapped' AS result
FROM normalized.account_id_mapping;

-- Revenue Normalization
SELECT 
    'Revenue Normalization' AS achievement,
    '$' || TO_CHAR(SUM(monthly_recurring_revenue), 'FM999,999.00') || ' total MRR across ' || 
    COUNT(*) || ' subscriptions' AS result
FROM normalized.subscriptions;

-- Device Health Normalization
SELECT 
    'Device Health Scores' AS achievement,
    COUNT(*) || ' devices with normalized health scores (avg: ' || 
    ROUND(AVG(health_score)::numeric, 2) || ')' AS result
FROM normalized.devices;

-- Customer Health Scores
SELECT 
    'Customer Health' AS achievement,
    COUNT(*) || ' customers with health scores (avg: ' || 
    ROUND(AVG(customer_health_score), 1) || ')' AS result
FROM normalized.customers;

-- 4. Data Quality Improvements
SELECT 
    '' AS blank,
    'DATA QUALITY IMPROVEMENTS' AS section;

-- Before/After MRR
WITH mrr_summary AS (
    SELECT 
        SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END) AS zero_mrr,
        SUM(CASE WHEN monthly_recurring_revenue > 0 THEN 1 ELSE 0 END) AS positive_mrr,
        COUNT(*) AS total
    FROM normalized.subscriptions
)
SELECT 
    'MRR Data Quality' AS metric,
    'Fixed ' || positive_mrr || ' subscriptions with positive MRR (was 0 for all)' AS improvement
FROM mrr_summary;

-- Account ID Consistency
SELECT 
    'Account ID Consistency' AS metric,
    'Reconciled ' || COUNT(DISTINCT normalized_account_id) || 
    ' account IDs across all entities' AS improvement
FROM normalized.account_id_mapping;

-- 5. Next Steps
SELECT 
    '' AS blank,
    'REMAINING WORK' AS section;

SELECT 
    'Missing Tables' AS item,
    'users, campaigns, features tables need normalization' AS status
UNION ALL
SELECT 
    'Historical Data' AS item,
    'Generate 24 months of historical snapshots for ML training'
UNION ALL
SELECT 
    'Feature Engineering' AS item,
    'Create derived features for churn prediction and CLV models'
UNION ALL
SELECT 
    'ML Training Sets' AS item,
    'Build labeled datasets for supervised learning models';

SELECT '===========================================' AS line;
SELECT 'Normalization process monitoring complete!' AS status;
SELECT '===========================================' AS line;
