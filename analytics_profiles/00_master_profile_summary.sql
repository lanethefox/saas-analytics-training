-- Master Data Quality and Analytics Profile
-- Run this script to get a comprehensive view of your data

-- ========================================
-- DATA QUALITY SUMMARY
-- ========================================

WITH data_quality_checks AS (
    SELECT 
        'Customers' as entity,
        COUNT(*) as record_count,
        COUNT(DISTINCT account_id) as unique_ids,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) as null_ids,
        SUM(CASE WHEN monthly_recurring_revenue < 0 THEN 1 ELSE 0 END) as invalid_values,
        MIN(created_at)::date as earliest_date,
        MAX(created_at)::date as latest_date
    FROM entity.entity_customers
    
    UNION ALL
    
    SELECT 
        'Devices' as entity,
        COUNT(*) as record_count,
        COUNT(DISTINCT device_id) as unique_ids,
        SUM(CASE WHEN device_id IS NULL THEN 1 ELSE 0 END) as null_ids,
        SUM(CASE WHEN overall_health_score < 0 OR overall_health_score > 100 THEN 1 ELSE 0 END) as invalid_values,
        MIN(device_installed_date)::date as earliest_date,
        MAX(device_installed_date)::date as latest_date
    FROM entity.entity_devices
    
    UNION ALL
    
    SELECT 
        'Users' as entity,
        COUNT(*) as record_count,
        COUNT(DISTINCT user_id) as unique_ids,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as null_ids,
        SUM(CASE WHEN engagement_score < 0 OR engagement_score > 100 THEN 1 ELSE 0 END) as invalid_values,
        MIN(created_at)::date as earliest_date,
        MAX(created_at)::date as latest_date
    FROM entity.entity_users
    
    UNION ALL
    
    SELECT 
        'Locations' as entity,
        COUNT(*) as record_count,
        COUNT(DISTINCT location_id) as unique_ids,
        SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) as null_ids,
        SUM(CASE WHEN operational_health_score < 0 OR operational_health_score > 100 THEN 1 ELSE 0 END) as invalid_values,
        MIN(created_at)::date as earliest_date,
        MAX(created_at)::date as latest_date
    FROM entity.entity_locations
    
    UNION ALL
    
    SELECT 
        'Subscriptions' as entity,
        COUNT(*) as record_count,
        COUNT(DISTINCT subscription_id) as unique_ids,
        SUM(CASE WHEN subscription_id IS NULL THEN 1 ELSE 0 END) as null_ids,
        SUM(CASE WHEN monthly_recurring_revenue < 0 THEN 1 ELSE 0 END) as invalid_values,
        MIN(start_date)::date as earliest_date,
        MAX(start_date)::date as latest_date
    FROM entity.entity_subscriptions
),
key_metrics_summary AS (
    SELECT 
        -- Revenue
        (SELECT SUM(monthly_recurring_revenue) FROM entity.entity_customers) as total_mrr,
        (SELECT COUNT(*) FROM entity.entity_customers WHERE is_active = TRUE) as active_customers,
        
        -- Devices
        (SELECT COUNT(*) FROM entity.entity_devices WHERE operational_status = 'active') as active_devices,
        (SELECT AVG(uptime_percentage_30d) FROM entity.entity_devices) as avg_device_uptime,
        
        -- Users
        (SELECT COUNT(*) FROM entity.entity_users WHERE is_active = TRUE) as active_users,
        (SELECT AVG(engagement_score) FROM entity.entity_users WHERE is_active = TRUE) as avg_user_engagement,
        
        -- Locations
        (SELECT COUNT(*) FROM entity.entity_locations WHERE is_active = TRUE) as active_locations,
        (SELECT AVG(operational_health_score) FROM entity.entity_locations) as avg_location_health
)
SELECT '==================================' as separator
UNION ALL
SELECT 'DATA QUALITY AND ANALYTICS PROFILE' as separator
UNION ALL
SELECT '==================================' as separator
UNION ALL
SELECT '' as separator
UNION ALL
SELECT 'DATA QUALITY SUMMARY' as separator
UNION ALL
SELECT '-------------------' as separator
UNION ALL
SELECT entity || ': ' || record_count || ' records, ' || 
       unique_ids || ' unique, ' ||
       null_ids || ' nulls, ' ||
       invalid_values || ' invalid'
FROM data_quality_checks
UNION ALL
SELECT '' as separator
UNION ALL
SELECT 'DATE RANGES' as separator
UNION ALL
SELECT '-----------' as separator
UNION ALL
SELECT entity || ': ' || earliest_date || ' to ' || latest_date
FROM data_quality_checks
UNION ALL
SELECT '' as separator
UNION ALL
SELECT 'KEY METRICS SUMMARY' as separator
UNION ALL
SELECT '------------------' as separator
UNION ALL
SELECT 'Total MRR: $' || TO_CHAR(total_mrr, 'FM999,999,999.00') FROM key_metrics_summary
UNION ALL
SELECT 'Active Customers: ' || active_customers FROM key_metrics_summary
UNION ALL
SELECT 'Active Devices: ' || active_devices || ' (' || ROUND(avg_device_uptime, 1) || '% uptime)' FROM key_metrics_summary
UNION ALL
SELECT 'Active Users: ' || active_users || ' (' || ROUND(avg_user_engagement, 1) || ' engagement)' FROM key_metrics_summary
UNION ALL
SELECT 'Active Locations: ' || active_locations || ' (' || ROUND(avg_location_health, 1) || ' health)' FROM key_metrics_summary
UNION ALL
SELECT '' as separator
UNION ALL
SELECT '===================================' as separator
UNION ALL
SELECT 'Run individual profile scripts for detailed analysis:' as separator
UNION ALL
SELECT '- 01_customer_data_profile.sql' as separator
UNION ALL
SELECT '- 02_device_usage_profile.sql' as separator
UNION ALL
SELECT '- 03_business_analytics_profile.sql' as separator
UNION ALL
SELECT '- 04_user_engagement_profile.sql' as separator
UNION ALL
SELECT '- 05_location_operations_profile.sql' as separator;