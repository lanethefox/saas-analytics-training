-- Comprehensive Data Quality and Business Analytics Profile
-- Fixed version with correct schema mappings

\echo '================================================'
\echo 'DATA QUALITY & BUSINESS ANALYTICS PROFILE REPORT'
\echo '================================================'
\echo ''
\echo 'Report Generated:' `date`
\echo ''

-- ========================================
-- SECTION 1: ENTITY RECORD COUNTS
-- ========================================
\echo 'SECTION 1: ENTITY RECORD COUNTS AND DATA COVERAGE'
\echo '-------------------------------------------------'

WITH entity_counts AS (
    SELECT 'Customers' as entity_type, COUNT(*) as record_count FROM entity.entity_customers
    UNION ALL
    SELECT 'Devices', COUNT(*) FROM entity.entity_devices
    UNION ALL
    SELECT 'Users', COUNT(*) FROM entity.entity_users
    UNION ALL
    SELECT 'Locations', COUNT(*) FROM entity.entity_locations
    UNION ALL
    SELECT 'Subscriptions', COUNT(*) FROM entity.entity_subscriptions
    UNION ALL
    SELECT 'Campaigns', COUNT(*) FROM entity.entity_campaigns
    UNION ALL
    SELECT 'Features', COUNT(*) FROM entity.entity_features
)
SELECT entity_type, record_count FROM entity_counts ORDER BY record_count DESC;

-- ========================================
-- SECTION 2: CUSTOMER DATA QUALITY
-- ========================================
\echo ''
\echo 'SECTION 2: CUSTOMER DATA QUALITY ANALYSIS'
\echo '----------------------------------------'

WITH customer_quality AS (
    SELECT 
        COUNT(*) as total_customers,
        COUNT(DISTINCT account_id) as unique_accounts,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) as null_account_ids,
        SUM(CASE WHEN company_name IS NULL THEN 1 ELSE 0 END) as null_company_names,
        SUM(CASE WHEN monthly_recurring_revenue IS NULL THEN 1 ELSE 0 END) as null_mrr,
        SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END) as zero_mrr,
        SUM(CASE WHEN monthly_recurring_revenue < 0 THEN 1 ELSE 0 END) as negative_mrr,
        MIN(created_at)::date as earliest_created,
        MAX(created_at)::date as latest_created,
        MIN(monthly_recurring_revenue) as min_mrr,
        MAX(monthly_recurring_revenue) as max_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        STDDEV(monthly_recurring_revenue) as stddev_mrr
    FROM entity.entity_customers
)
SELECT 
    'Total Customers' as metric, total_customers::text as value
FROM customer_quality
UNION ALL
SELECT 'Unique Account IDs', unique_accounts::text FROM customer_quality
UNION ALL  
SELECT 'Null Account IDs', null_account_ids::text FROM customer_quality
UNION ALL
SELECT 'Null Company Names', null_company_names::text FROM customer_quality
UNION ALL
SELECT 'Null MRR Values', null_mrr::text FROM customer_quality
UNION ALL
SELECT 'Zero MRR Values', zero_mrr::text FROM customer_quality
UNION ALL
SELECT 'Negative MRR Values', negative_mrr::text FROM customer_quality
UNION ALL
SELECT 'Date Range', earliest_created || ' to ' || latest_created FROM customer_quality
UNION ALL
SELECT 'MRR Range', '$' || min_mrr || ' to $' || max_mrr FROM customer_quality
UNION ALL
SELECT 'Average MRR', '$' || ROUND(avg_mrr, 2)::text FROM customer_quality
UNION ALL
SELECT 'MRR Std Dev', '$' || ROUND(stddev_mrr, 2)::text FROM customer_quality;

-- ========================================
-- SECTION 3: DEVICE HEALTH ANALYSIS
-- ========================================
\echo ''
\echo 'SECTION 3: DEVICE HEALTH AND OPERATIONAL STATUS'
\echo '----------------------------------------------'

WITH device_analysis AS (
    SELECT 
        operational_status,
        COUNT(*) as device_count,
        AVG(overall_health_score) as avg_health_score,
        AVG(uptime_percentage_30d) as avg_uptime,
        MIN(device_installed_date)::date as earliest_install,
        MAX(device_installed_date)::date as latest_install
    FROM entity.entity_devices
    GROUP BY operational_status
)
SELECT 
    operational_status,
    device_count,
    ROUND(avg_health_score, 2) as avg_health_score,
    ROUND(avg_uptime, 2) as avg_uptime_pct,
    earliest_install,
    latest_install
FROM device_analysis
ORDER BY device_count DESC;

-- Device Health Score Distribution
\echo ''
\echo 'Device Health Score Distribution:'

SELECT 
    CASE 
        WHEN overall_health_score >= 90 THEN '90-100 (Excellent)'
        WHEN overall_health_score >= 70 THEN '70-89 (Good)'
        WHEN overall_health_score >= 50 THEN '50-69 (Fair)'
        WHEN overall_health_score >= 0 THEN '0-49 (Poor)'
        ELSE 'Invalid (<0 or >100)'
    END as health_range,
    COUNT(*) as device_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM entity.entity_devices
GROUP BY health_range
ORDER BY 
    CASE 
        WHEN overall_health_score >= 90 THEN 1
        WHEN overall_health_score >= 70 THEN 2
        WHEN overall_health_score >= 50 THEN 3
        WHEN overall_health_score >= 0 THEN 4
        ELSE 5
    END;

-- ========================================
-- SECTION 4: USER ENGAGEMENT ANALYSIS
-- ========================================
\echo ''
\echo 'SECTION 4: USER ENGAGEMENT METRICS'
\echo '---------------------------------'

WITH user_engagement AS (
    SELECT 
        COUNT(*) as total_users,
        AVG(engagement_score) as avg_engagement,
        MIN(engagement_score) as min_engagement,
        MAX(engagement_score) as max_engagement,
        AVG(days_since_last_activity) as avg_days_inactive,
        SUM(CASE WHEN days_since_last_activity <= 7 THEN 1 ELSE 0 END) as active_7d,
        SUM(CASE WHEN days_since_last_activity <= 30 THEN 1 ELSE 0 END) as active_30d,
        SUM(CASE WHEN days_since_last_activity > 90 THEN 1 ELSE 0 END) as inactive_90d,
        AVG(total_sessions_30d) as avg_sessions_30d,
        AVG(features_used_30d) as avg_features_used
    FROM entity.entity_users
)
SELECT 
    'Total Users' as metric, total_users::text as value
FROM user_engagement
UNION ALL
SELECT 'Avg Engagement Score', ROUND(avg_engagement, 2)::text FROM user_engagement
UNION ALL
SELECT 'Engagement Range', min_engagement || ' - ' || max_engagement FROM user_engagement
UNION ALL
SELECT 'Avg Days Since Last Activity', ROUND(avg_days_inactive, 1)::text FROM user_engagement
UNION ALL
SELECT 'Active Last 7 Days', active_7d || ' (' || ROUND(100.0 * active_7d / total_users, 1) || '%)' FROM user_engagement
UNION ALL
SELECT 'Active Last 30 Days', active_30d || ' (' || ROUND(100.0 * active_30d / total_users, 1) || '%)' FROM user_engagement
UNION ALL
SELECT 'Inactive 90+ Days', inactive_90d || ' (' || ROUND(100.0 * inactive_90d / total_users, 1) || '%)' FROM user_engagement
UNION ALL
SELECT 'Avg Sessions (30d)', ROUND(avg_sessions_30d, 1)::text FROM user_engagement
UNION ALL
SELECT 'Avg Features Used (30d)', ROUND(avg_features_used, 1)::text FROM user_engagement;

-- User Role Distribution
\echo ''
\echo 'User Role Distribution:'

SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    ROUND(AVG(engagement_score), 2) as avg_engagement
FROM entity.entity_users
GROUP BY role_type_standardized
ORDER BY user_count DESC
LIMIT 10;

-- ========================================
-- SECTION 5: LOCATION OPERATIONS
-- ========================================
\echo ''
\echo 'SECTION 5: LOCATION OPERATIONS ANALYSIS'
\echo '--------------------------------------'

WITH location_metrics AS (
    SELECT 
        COUNT(*) as total_locations,
        AVG(operational_health_score) as avg_health,
        AVG(device_count) as avg_devices,
        AVG(user_count) as avg_users,
        AVG(revenue_per_location) as avg_revenue,
        SUM(device_count) as total_devices,
        SUM(revenue_per_location) as total_revenue
    FROM entity.entity_locations
)
SELECT 
    'Total Locations' as metric, total_locations::text as value
FROM location_metrics
UNION ALL
SELECT 'Avg Health Score', ROUND(avg_health, 2)::text FROM location_metrics
UNION ALL
SELECT 'Avg Devices per Location', ROUND(avg_devices, 1)::text FROM location_metrics
UNION ALL
SELECT 'Avg Users per Location', ROUND(avg_users, 1)::text FROM location_metrics
UNION ALL
SELECT 'Avg Revenue per Location', '$' || TO_CHAR(avg_revenue, 'FM999,999.00') FROM location_metrics
UNION ALL
SELECT 'Total Devices Across Locations', total_devices::text FROM location_metrics
UNION ALL
SELECT 'Total Revenue Across Locations', '$' || TO_CHAR(total_revenue, 'FM999,999,999.00') FROM location_metrics;

-- ========================================
-- SECTION 6: SUBSCRIPTION ANALYSIS
-- ========================================
\echo ''
\echo 'SECTION 6: SUBSCRIPTION METRICS'
\echo '------------------------------'

WITH subscription_metrics AS (
    SELECT 
        subscription_status,
        COUNT(*) as sub_count,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        MIN(start_date)::date as earliest_start,
        MAX(start_date)::date as latest_start
    FROM entity.entity_subscriptions
    GROUP BY subscription_status
)
SELECT 
    subscription_status,
    sub_count,
    '$' || TO_CHAR(total_mrr, 'FM999,999.00') as total_mrr,
    '$' || TO_CHAR(avg_mrr, 'FM999,999.00') as avg_mrr,
    earliest_start,
    latest_start
FROM subscription_metrics
ORDER BY sub_count DESC;

-- Plan Type Distribution
\echo ''
\echo 'Subscription Plan Distribution:'

SELECT 
    plan_name,
    COUNT(*) as subscription_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    SUM(monthly_recurring_revenue) as plan_total_mrr
FROM entity.entity_subscriptions
WHERE subscription_status = 'active'
GROUP BY plan_name
ORDER BY subscription_count DESC
LIMIT 10;

-- ========================================
-- SECTION 7: DATA QUALITY ISSUES SUMMARY
-- ========================================
\echo ''
\echo 'SECTION 7: DATA QUALITY ISSUES DETECTED'
\echo '--------------------------------------'

WITH quality_issues AS (
    -- Customer Issues
    SELECT 'Customers with NULL account_id' as issue, COUNT(*) as count
    FROM entity.entity_customers WHERE account_id IS NULL
    UNION ALL
    SELECT 'Customers with zero MRR', COUNT(*)
    FROM entity.entity_customers WHERE monthly_recurring_revenue = 0
    UNION ALL
    SELECT 'Customers with negative MRR', COUNT(*)
    FROM entity.entity_customers WHERE monthly_recurring_revenue < 0
    
    UNION ALL
    -- Device Issues
    SELECT 'Devices with invalid health scores', COUNT(*)
    FROM entity.entity_devices WHERE overall_health_score < 0 OR overall_health_score > 100
    UNION ALL
    SELECT 'Devices with NULL location_id', COUNT(*)
    FROM entity.entity_devices WHERE location_id IS NULL
    
    UNION ALL
    -- User Issues
    SELECT 'Users with invalid engagement scores', COUNT(*)
    FROM entity.entity_users WHERE engagement_score < 0 OR engagement_score > 100
    UNION ALL
    SELECT 'Users with NULL account_id', COUNT(*)
    FROM entity.entity_users WHERE account_id IS NULL
    
    UNION ALL
    -- Location Issues
    SELECT 'Locations with NULL account_id', COUNT(*)
    FROM entity.entity_locations WHERE account_id IS NULL
    UNION ALL
    SELECT 'Locations with zero devices', COUNT(*)
    FROM entity.entity_locations WHERE device_count = 0
)
SELECT issue, count 
FROM quality_issues 
WHERE count > 0
ORDER BY count DESC;

-- ========================================
-- SECTION 8: CROSS-ENTITY VALIDATION
-- ========================================
\echo ''
\echo 'SECTION 8: CROSS-ENTITY DATA VALIDATION'
\echo '--------------------------------------'

-- Check for orphaned records
WITH orphan_checks AS (
    SELECT 'Devices without valid locations' as check_type, COUNT(*) as orphan_count
    FROM entity.entity_devices d
    LEFT JOIN entity.entity_locations l ON d.location_id = l.location_id
    WHERE l.location_id IS NULL
    
    UNION ALL
    
    SELECT 'Users without valid accounts', COUNT(*)
    FROM entity.entity_users u
    LEFT JOIN entity.entity_customers c ON u.account_id = c.account_id
    WHERE c.account_id IS NULL
    
    UNION ALL
    
    SELECT 'Locations without valid accounts', COUNT(*)
    FROM entity.entity_locations l
    LEFT JOIN entity.entity_customers c ON l.account_id = c.account_id
    WHERE c.account_id IS NULL
)
SELECT * FROM orphan_checks WHERE orphan_count > 0;

-- ========================================
-- SECTION 9: KEY BUSINESS METRICS SUMMARY
-- ========================================
\echo ''
\echo 'SECTION 9: KEY BUSINESS METRICS SUMMARY'
\echo '--------------------------------------'

SELECT 
    'Total Active MRR' as metric,
    '$' || TO_CHAR(SUM(monthly_recurring_revenue), 'FM999,999,999.00') as value
FROM entity.entity_customers
WHERE customer_status = 'active'

UNION ALL

SELECT 
    'Total Active Devices',
    COUNT(*)::text
FROM entity.entity_devices
WHERE operational_status = 'active'

UNION ALL

SELECT 
    'Average Customer Health Score',
    ROUND(AVG(customer_health_score), 2)::text
FROM entity.entity_customers
WHERE customer_status = 'active'

UNION ALL

SELECT 
    'Average Device Uptime %',
    ROUND(AVG(uptime_percentage_30d), 2)::text
FROM entity.entity_devices
WHERE operational_status = 'active'

UNION ALL

SELECT 
    'Total Active Users',
    COUNT(*)::text
FROM entity.entity_users
WHERE days_since_last_activity <= 30;

\echo ''
\echo '================================================'
\echo 'END OF DATA QUALITY & ANALYTICS PROFILE REPORT'
\echo '================================================'
