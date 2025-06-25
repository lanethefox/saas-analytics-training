-- Data Quality Report SQL
-- Generated for Medium-Scale Data Load

-- 1. Raw Data Table Row Counts
WITH raw_counts AS (
    SELECT 'Accounts' as table_name, COUNT(*) as row_count FROM raw.app_database_accounts
    UNION ALL
    SELECT 'Devices', COUNT(*) FROM raw.app_database_devices
    UNION ALL
    SELECT 'Locations', COUNT(*) FROM raw.app_database_locations
    UNION ALL
    SELECT 'Users', COUNT(*) FROM raw.app_database_users
    UNION ALL
    SELECT 'Subscriptions', COUNT(*) FROM raw.app_database_subscriptions
    UNION ALL
    SELECT 'Tap Events', COUNT(*) FROM raw.app_database_tap_events
    UNION ALL
    SELECT 'Feature Usage', COUNT(*) FROM raw.app_database_feature_usage
    UNION ALL
    SELECT 'Page Views', COUNT(*) FROM raw.app_database_page_views
    UNION ALL
    SELECT 'User Sessions', COUNT(*) FROM raw.app_database_user_sessions
),

-- 2. Data Quality Checks
quality_checks AS (
    -- Null checks for critical fields
    SELECT 'Accounts Missing Name' as issue, COUNT(*) as count 
    FROM raw.app_database_accounts WHERE name IS NULL
    UNION ALL
    SELECT 'Devices Missing Location', COUNT(*) 
    FROM raw.app_database_devices WHERE location_id IS NULL
    UNION ALL
    SELECT 'Users Missing Customer', COUNT(*) 
    FROM raw.app_database_users WHERE customer_id IS NULL
    UNION ALL
    SELECT 'Subscriptions Missing Customer', COUNT(*) 
    FROM raw.app_database_subscriptions WHERE customer_id IS NULL
),

-- 3. Referential Integrity Checks
integrity_checks AS (
    SELECT 'Orphaned Devices (No Location)' as issue, COUNT(*) as count
    FROM raw.app_database_devices d
    LEFT JOIN raw.app_database_locations l ON d.location_id = l.id
    WHERE l.id IS NULL
    UNION ALL
    SELECT 'Orphaned Users (No Account)', COUNT(*)
    FROM raw.app_database_users u
    LEFT JOIN raw.app_database_accounts a ON u.customer_id = a.id
    WHERE a.id IS NULL
),

-- 4. Business Metrics Summary
metrics_summary AS (
    SELECT 
        COUNT(DISTINCT account_id) as total_customers,
        COUNT(DISTINCT CASE WHEN subscription_status = 'active' THEN account_id END) as active_customers,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        COUNT(DISTINCT CASE WHEN subscription_status = 'trial' THEN account_id END) as trial_customers
    FROM entity.entity_customers
),

-- 5. Device Health Summary
device_summary AS (
    SELECT 
        COUNT(*) as total_devices,
        COUNT(CASE WHEN operational_status = 'operational' THEN 1 END) as online_devices,
        ROUND(AVG(overall_health_score), 3) as avg_health_score,
        COUNT(CASE WHEN requires_immediate_attention THEN 1 END) as devices_needing_attention
    FROM entity.entity_devices
),

-- 6. Location Summary
location_summary AS (
    SELECT 
        COUNT(*) as total_locations,
        COUNT(CASE WHEN operational_status = 'operational' THEN 1 END) as operational_locations,
        AVG(total_devices) as avg_devices_per_location,
        SUM(total_devices) as total_devices_deployed
    FROM entity.entity_locations
)

-- Output all results
SELECT '=== DATA QUALITY REPORT ===' as report_section
UNION ALL
SELECT ''
UNION ALL
SELECT '1. RAW DATA VOLUMES:' 
UNION ALL
SELECT '-------------------'
UNION ALL
SELECT CONCAT('  ', table_name, ': ', TO_CHAR(row_count, 'FM999,999,999'), ' records') 
FROM raw_counts
UNION ALL
SELECT ''
UNION ALL
SELECT '2. DATA QUALITY ISSUES:'
UNION ALL
SELECT '---------------------'
UNION ALL
SELECT CONCAT('  ', issue, ': ', count) 
FROM quality_checks WHERE count > 0
UNION ALL
SELECT CONCAT('  ', issue, ': ', count) 
FROM integrity_checks WHERE count > 0
UNION ALL
SELECT ''
UNION ALL
SELECT '3. BUSINESS METRICS SUMMARY:'
UNION ALL
SELECT '--------------------------'
UNION ALL
SELECT CONCAT('  Total Customers: ', total_customers) FROM metrics_summary
UNION ALL
SELECT CONCAT('  Active Customers: ', active_customers) FROM metrics_summary
UNION ALL
SELECT CONCAT('  Total MRR: $', TO_CHAR(total_mrr, 'FM999,999.00')) FROM metrics_summary
UNION ALL
SELECT CONCAT('  Average MRR: $', TO_CHAR(avg_mrr, 'FM999.00')) FROM metrics_summary
UNION ALL
SELECT CONCAT('  Trial Customers: ', trial_customers) FROM metrics_summary
UNION ALL
SELECT ''
UNION ALL
SELECT '4. DEVICE OPERATIONS:'
UNION ALL
SELECT '-------------------'
UNION ALL
SELECT CONCAT('  Total Devices: ', TO_CHAR(total_devices, 'FM999,999')) FROM device_summary
UNION ALL
SELECT CONCAT('  Online Devices: ', online_devices) FROM device_summary
UNION ALL
SELECT CONCAT('  Avg Health Score: ', avg_health_score) FROM device_summary
UNION ALL
SELECT CONCAT('  Devices Needing Attention: ', devices_needing_attention) FROM device_summary
UNION ALL
SELECT ''
UNION ALL
SELECT '5. LOCATION METRICS:'
UNION ALL
SELECT '------------------'
UNION ALL
SELECT CONCAT('  Total Locations: ', total_locations) FROM location_summary
UNION ALL
SELECT CONCAT('  Operational Locations: ', operational_locations) FROM location_summary
UNION ALL
SELECT CONCAT('  Avg Devices per Location: ', ROUND(avg_devices_per_location, 1)) FROM location_summary
UNION ALL
SELECT CONCAT('  Total Devices Deployed: ', TO_CHAR(total_devices_deployed, 'FM999,999')) FROM location_summary;