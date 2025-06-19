-- Comprehensive Data Quality and Business Analytics Profile
-- Execution Script for SaaS Platform Data
-- Generated: Current Date

-- ========================================
-- SECTION 1: DATA VOLUME AND COMPLETENESS
-- ========================================

\echo '================================================'
\echo 'DATA QUALITY & BUSINESS ANALYTICS PROFILE REPORT'
\echo '================================================'
\echo ''
\echo 'SECTION 1: DATA VOLUME AND COMPLETENESS'
\echo '---------------------------------------'

-- Customer Entity Volume
WITH customer_stats AS (
    SELECT 
        'entity_customers' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT account_id) as unique_accounts,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) as null_account_ids,
        SUM(CASE WHEN company_name IS NULL THEN 1 ELSE 0 END) as null_company_names,
        SUM(CASE WHEN monthly_recurring_revenue IS NULL THEN 1 ELSE 0 END) as null_mrr,
        MIN(created_at) as earliest_record,
        MAX(created_at) as latest_record
    FROM entity.entity_customers
)
SELECT 
    table_name,
    total_records,
    unique_accounts,
    ROUND(100.0 * (total_records - null_account_ids) / total_records, 2) as account_id_completeness,
    ROUND(100.0 * (total_records - null_company_names) / total_records, 2) as company_name_completeness,
    ROUND(100.0 * (total_records - null_mrr) / total_records, 2) as mrr_completeness,
    earliest_record::date,
    latest_record::date
FROM customer_stats;

-- Device Entity Volume
WITH device_stats AS (
    SELECT 
        'entity_devices' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT device_id) as unique_devices,
        SUM(CASE WHEN device_id IS NULL THEN 1 ELSE 0 END) as null_device_ids,
        SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) as null_location_ids,
        SUM(CASE WHEN overall_health_score IS NULL THEN 1 ELSE 0 END) as null_health_scores,
        MIN(device_installed_date) as earliest_record,
        MAX(device_installed_date) as latest_record
    FROM entity.entity_devices
)
SELECT 
    table_name,
    total_records,
    unique_devices,
    ROUND(100.0 * (total_records - null_device_ids) / total_records, 2) as device_id_completeness,
    ROUND(100.0 * (total_records - null_location_ids) / total_records, 2) as location_id_completeness,
    ROUND(100.0 * (total_records - null_health_scores) / total_records, 2) as health_score_completeness,
    earliest_record::date,
    latest_record::date
FROM device_stats;

-- User Entity Volume
WITH user_stats AS (
    SELECT 
        'entity_users' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as null_user_ids,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) as null_account_ids,
        SUM(CASE WHEN engagement_score IS NULL THEN 1 ELSE 0 END) as null_engagement_scores,
        MIN(first_seen_date) as earliest_record,
        MAX(first_seen_date) as latest_record
    FROM entity.entity_users
)
SELECT 
    table_name,
    total_records,
    unique_users,
    ROUND(100.0 * (total_records - null_user_ids) / total_records, 2) as user_id_completeness,
    ROUND(100.0 * (total_records - null_account_ids) / total_records, 2) as account_id_completeness,
    ROUND(100.0 * (total_records - null_engagement_scores) / total_records, 2) as engagement_completeness,
    earliest_record::date,
    latest_record::date
FROM user_stats;

-- Location Entity Volume
WITH location_stats AS (
    SELECT 
        'entity_locations' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT location_id) as unique_locations,
        SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) as null_location_ids,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) as null_account_ids,
        MIN(created_at) as earliest_record,
        MAX(created_at) as latest_record
    FROM entity.entity_locations
)
SELECT 
    table_name,
    total_records,
    unique_locations,
    ROUND(100.0 * (total_records - null_location_ids) / total_records, 2) as location_id_completeness,
    ROUND(100.0 * (total_records - null_account_ids) / total_records, 2) as account_id_completeness,
    earliest_record::date,
    latest_record::date
FROM location_stats;

\echo ''
\echo 'SECTION 2: BUSINESS METRICS SUMMARY'
\echo '-----------------------------------'

-- Revenue Metrics
WITH revenue_metrics AS (
    SELECT 
        COUNT(DISTINCT account_id) as total_customers,
        COUNT(DISTINCT CASE WHEN customer_status = 'active' THEN account_id END) as active_customers,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_recurring_revenue) as median_mrr,
        MAX(monthly_recurring_revenue) as max_mrr,
        SUM(annual_recurring_revenue) as total_arr
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    'Total Customers' as metric,
    total_customers::text as value
FROM revenue_metrics
UNION ALL
SELECT 
    'Active Customers',
    active_customers::text
FROM revenue_metrics
UNION ALL
SELECT 
    'Total MRR',
    '$' || TO_CHAR(total_mrr, 'FM999,999,999.00')
FROM revenue_metrics
UNION ALL
SELECT 
    'Average MRR per Customer',
    '$' || TO_CHAR(avg_mrr, 'FM999,999.00')
FROM revenue_metrics
UNION ALL
SELECT 
    'Median MRR',
    '$' || TO_CHAR(median_mrr, 'FM999,999.00')
FROM revenue_metrics
UNION ALL
SELECT 
    'Max MRR (Largest Customer)',
    '$' || TO_CHAR(max_mrr, 'FM999,999.00')
FROM revenue_metrics
UNION ALL
SELECT 
    'Total ARR',
    '$' || TO_CHAR(total_arr, 'FM999,999,999.00')
FROM revenue_metrics;

\echo ''
\echo 'SECTION 3: CUSTOMER SEGMENTATION'
\echo '--------------------------------'

-- Customer Tier Distribution
SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    SUM(monthly_recurring_revenue) as tier_mrr,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr_per_customer
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY customer_tier
ORDER BY customer_tier;

\echo ''
\echo 'SECTION 4: DEVICE HEALTH ANALYTICS'
\echo '----------------------------------'

-- Device Health Distribution
WITH device_health AS (
    SELECT 
        CASE 
            WHEN overall_health_score >= 90 THEN 'Excellent (90-100)'
            WHEN overall_health_score >= 70 THEN 'Good (70-89)'
            WHEN overall_health_score >= 50 THEN 'Fair (50-69)'
            ELSE 'Poor (<50)'
        END as health_category,
        COUNT(*) as device_count,
        AVG(uptime_percentage_30d) as avg_uptime
    FROM entity.entity_devices
    WHERE operational_status = 'active'
    GROUP BY health_category
)
SELECT 
    health_category,
    device_count,
    ROUND(100.0 * device_count / SUM(device_count) OVER (), 2) as percentage,
    ROUND(avg_uptime, 2) as avg_uptime_pct
FROM device_health
ORDER BY 
    CASE health_category
        WHEN 'Excellent (90-100)' THEN 1
        WHEN 'Good (70-89)' THEN 2
        WHEN 'Fair (50-69)' THEN 3
        ELSE 4
    END;

\echo ''
\echo 'SECTION 5: USER ENGAGEMENT METRICS'
\echo '---------------------------------'

-- User Engagement Summary
WITH engagement_metrics AS (
    SELECT 
        COUNT(DISTINCT user_id) as total_users,
        COUNT(DISTINCT CASE WHEN is_active = TRUE THEN user_id END) as active_users,
        AVG(engagement_score) as avg_engagement_score,
        AVG(days_since_last_activity) as avg_days_since_activity,
        COUNT(DISTINCT CASE WHEN days_since_last_activity <= 7 THEN user_id END) as active_last_7d,
        COUNT(DISTINCT CASE WHEN days_since_last_activity <= 30 THEN user_id END) as active_last_30d
    FROM entity.entity_users
)
SELECT 
    'Total Users' as metric,
    total_users::text as value
FROM engagement_metrics
UNION ALL
SELECT 
    'Active Users',
    active_users::text
FROM engagement_metrics
UNION ALL
SELECT 
    'Average Engagement Score',
    ROUND(avg_engagement_score, 2)::text
FROM engagement_metrics
UNION ALL
SELECT 
    'Active Last 7 Days',
    active_last_7d::text || ' (' || ROUND(100.0 * active_last_7d / total_users, 1) || '%)'
FROM engagement_metrics
UNION ALL
SELECT 
    'Active Last 30 Days',
    active_last_30d::text || ' (' || ROUND(100.0 * active_last_30d / total_users, 1) || '%)'
FROM engagement_metrics;

\echo ''
\echo 'SECTION 6: LOCATION OPERATIONS SUMMARY'
\echo '-------------------------------------'

-- Location Operations Metrics
WITH location_metrics AS (
    SELECT 
        COUNT(DISTINCT location_id) as total_locations,
        COUNT(DISTINCT CASE WHEN is_active = TRUE THEN location_id END) as active_locations,
        AVG(operational_health_score) as avg_health_score,
        AVG(device_count) as avg_devices_per_location,
        AVG(revenue_per_location) as avg_revenue_per_location
    FROM entity.entity_locations
)
SELECT 
    'Total Locations' as metric,
    total_locations::text as value
FROM location_metrics
UNION ALL
SELECT 
    'Active Locations',
    active_locations::text
FROM location_metrics
UNION ALL
SELECT 
    'Average Health Score',
    ROUND(avg_health_score, 2)::text
FROM location_metrics
UNION ALL
SELECT 
    'Avg Devices per Location',
    ROUND(avg_devices_per_location, 1)::text
FROM location_metrics
UNION ALL
SELECT 
    'Avg Revenue per Location',
    '$' || TO_CHAR(avg_revenue_per_location, 'FM999,999.00')
FROM location_metrics;

\echo ''
\echo 'SECTION 7: DATA QUALITY ISSUES'
\echo '-----------------------------'

-- Identify potential data quality issues
WITH quality_issues AS (
    SELECT 'Customers with negative MRR' as issue_type, COUNT(*) as issue_count
    FROM entity.entity_customers
    WHERE monthly_recurring_revenue < 0
    
    UNION ALL
    
    SELECT 'Devices with invalid health scores', COUNT(*)
    FROM entity.entity_devices
    WHERE overall_health_score < 0 OR overall_health_score > 100
    
    UNION ALL
    
    SELECT 'Users with invalid engagement scores', COUNT(*)
    FROM entity.entity_users
    WHERE engagement_score < 0 OR engagement_score > 100
    
    UNION ALL
    
    SELECT 'Locations with missing account_id', COUNT(*)
    FROM entity.entity_locations
    WHERE account_id IS NULL
    
    UNION ALL
    
    SELECT 'Active customers with zero MRR', COUNT(*)
    FROM entity.entity_customers
    WHERE customer_status = 'active' AND monthly_recurring_revenue = 0
)
SELECT * FROM quality_issues WHERE issue_count > 0;

\echo ''
\echo 'SECTION 8: HISTORICAL DATA COVERAGE'
\echo '----------------------------------'

-- Check historical data availability
SELECT 
    'entity_customers_history' as history_table,
    COUNT(*) as total_records,
    MIN(valid_from)::date as earliest_date,
    MAX(valid_to)::date as latest_date,
    COUNT(DISTINCT account_id) as unique_entities
FROM entity.entity_customers_history

UNION ALL

SELECT 
    'entity_devices_history',
    COUNT(*),
    MIN(valid_from)::date,
    MAX(valid_to)::date,
    COUNT(DISTINCT device_id)
FROM entity.entity_devices_history

UNION ALL

SELECT 
    'entity_users_history',
    COUNT(*),
    MIN(valid_from)::date,
    MAX(valid_to)::date,
    COUNT(DISTINCT user_id)
FROM entity.entity_users_history;

\echo ''
\echo '================================================'
\echo 'END OF DATA QUALITY & ANALYTICS PROFILE REPORT'
\echo '================================================'
