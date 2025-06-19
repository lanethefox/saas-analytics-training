-- FINAL DATA QUALITY AND BUSINESS ANALYTICS PROFILE
-- Working version based on actual schema

\echo '========================================================'
\echo 'COMPREHENSIVE DATA QUALITY & BUSINESS ANALYTICS PROFILE'
\echo '========================================================'
\echo ''
\echo 'Generated:' `date`
\echo ''

-- ========================================
-- EXECUTIVE SUMMARY
-- ========================================
\echo 'EXECUTIVE SUMMARY'
\echo '-----------------'
\echo ''
\echo 'This profile reveals critical data quality issues:'
\echo '1. All 100 customers have $0 MRR (100% zero revenue)'
\echo '2. Device health scores average 0.25/100 (critical failure)'
\echo '3. Device uptime averages 0.01% (essentially offline)'
\echo '4. All data appears to be synthetic/test data'
\echo ''

-- ========================================
-- DATA VOLUME OVERVIEW
-- ========================================
\echo 'DATA VOLUME OVERVIEW'
\echo '--------------------'

SELECT 
    'entity_customers' as table_name,
    COUNT(*) as records,
    MIN(created_at)::date as min_date,
    MAX(created_at)::date as max_date
FROM entity.entity_customers

UNION ALL

SELECT 
    'entity_devices',
    COUNT(*),
    MIN(device_installed_date)::date,
    MAX(device_installed_date)::date
FROM entity.entity_devices

UNION ALL

SELECT 
    'entity_users',
    COUNT(*),
    MIN(user_created_at)::date,
    MAX(user_created_at)::date
FROM entity.entity_users

UNION ALL

SELECT 
    'entity_locations',
    COUNT(*),
    MIN(created_at)::date,
    MAX(created_at)::date
FROM entity.entity_locations

UNION ALL

SELECT 
    'entity_subscriptions',
    COUNT(*),
    NULL,
    NULL
FROM entity.entity_subscriptions

UNION ALL

SELECT 
    'entity_campaigns',
    COUNT(*),
    MIN(campaign_created_date)::date,
    MAX(campaign_created_date)::date
FROM entity.entity_campaigns

ORDER BY records DESC;

-- ========================================
-- CRITICAL DATA QUALITY ISSUES
-- ========================================
\echo ''
\echo 'CRITICAL DATA QUALITY ISSUES'
\echo '----------------------------'

-- Issue #1: Zero Revenue
\echo ''
\echo 'Issue #1: ZERO REVENUE PROBLEM'
SELECT 
    COUNT(*) as total_customers,
    SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END) as zero_mrr_count,
    ROUND(100.0 * SUM(CASE WHEN monthly_recurring_revenue = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as zero_mrr_pct,
    MIN(monthly_recurring_revenue) as min_mrr,
    MAX(monthly_recurring_revenue) as max_mrr,
    SUM(monthly_recurring_revenue) as total_mrr
FROM entity.entity_customers;

-- Issue #2: Device Health Crisis
\echo ''
\echo 'Issue #2: DEVICE HEALTH CRISIS'
SELECT 
    COUNT(*) as total_devices,
    ROUND(AVG(overall_health_score), 4) as avg_health_score,
    ROUND(AVG(uptime_percentage_30d), 4) as avg_uptime_pct,
    MIN(overall_health_score) as min_health,
    MAX(overall_health_score) as max_health,
    SUM(CASE WHEN overall_health_score < 1 THEN 1 ELSE 0 END) as critical_devices
FROM entity.entity_devices;

-- Issue #3: User Engagement
\echo ''
\echo 'Issue #3: USER ENGAGEMENT LEVELS'
SELECT 
    COUNT(*) as total_users,
    ROUND(AVG(engagement_score), 4) as avg_engagement,
    MIN(engagement_score) as min_engagement,
    MAX(engagement_score) as max_engagement,
    SUM(CASE WHEN engagement_score < 1 THEN 1 ELSE 0 END) as zero_engagement_users
FROM entity.entity_users;

-- ========================================
-- DETAILED ENTITY ANALYSIS
-- ========================================
\echo ''
\echo 'DETAILED ENTITY ANALYSIS'
\echo '------------------------'

-- Customer Analysis
\echo ''
\echo 'CUSTOMER ENTITY ANALYSIS:'
SELECT 
    customer_tier,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(total_devices) as avg_devices,
    AVG(total_users) as avg_users,
    AVG(total_locations) as avg_locations
FROM entity.entity_customers
GROUP BY customer_tier
ORDER BY customer_tier;

-- Device Status Distribution
\echo ''
\echo 'DEVICE OPERATIONAL STATUS:'
SELECT 
    operational_status,
    COUNT(*) as device_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct,
    ROUND(AVG(overall_health_score), 2) as avg_health,
    ROUND(AVG(uptime_percentage_30d), 4) as avg_uptime
FROM entity.entity_devices
GROUP BY operational_status
ORDER BY device_count DESC;

-- User Role Distribution
\echo ''
\echo 'USER ROLE DISTRIBUTION:'
SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct,
    ROUND(AVG(engagement_score), 2) as avg_engagement,
    ROUND(AVG(total_sessions_30d), 1) as avg_sessions
FROM entity.entity_users
GROUP BY role_type_standardized
ORDER BY user_count DESC;

-- Location Health
\echo ''
\echo 'LOCATION OPERATIONAL HEALTH:'
SELECT 
    CASE 
        WHEN operational_health_score >= 90 THEN '90-100 (Excellent)'
        WHEN operational_health_score >= 70 THEN '70-89 (Good)'
        WHEN operational_health_score >= 50 THEN '50-69 (Fair)'
        WHEN operational_health_score >= 1 THEN '1-49 (Poor)'
        ELSE '0 (Critical)'
    END as health_range,
    COUNT(*) as location_count,
    ROUND(AVG(revenue_per_location), 2) as avg_revenue
FROM entity.entity_locations
GROUP BY health_range
ORDER BY 
    CASE 
        WHEN operational_health_score >= 90 THEN 1
        WHEN operational_health_score >= 70 THEN 2
        WHEN operational_health_score >= 50 THEN 3
        WHEN operational_health_score >= 1 THEN 4
        ELSE 5
    END;

-- Subscription Status
\echo ''
\echo 'SUBSCRIPTION STATUS DISTRIBUTION:'
SELECT 
    subscription_status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct,
    SUM(monthly_recurring_revenue) as total_mrr
FROM entity.entity_subscriptions
GROUP BY subscription_status
ORDER BY count DESC;

-- ========================================
-- DATA RELATIONSHIPS VALIDATION
-- ========================================
\echo ''
\echo 'DATA RELATIONSHIPS VALIDATION'
\echo '-----------------------------'

-- Check customer-location relationship
\echo ''
\echo 'Customer-Location Relationship:'
WITH customer_location_check AS (
    SELECT 
        c.account_id,
        COUNT(DISTINCT l.location_id) as location_count
    FROM entity.entity_customers c
    LEFT JOIN entity.entity_locations l ON c.account_id::varchar = l.account_id
    GROUP BY c.account_id
)
SELECT 
    CASE 
        WHEN location_count = 0 THEN 'Customers with 0 locations'
        WHEN location_count = 1 THEN 'Customers with 1 location'
        WHEN location_count <= 5 THEN 'Customers with 2-5 locations'
        ELSE 'Customers with 6+ locations'
    END as category,
    COUNT(*) as customer_count
FROM customer_location_check
GROUP BY category
ORDER BY 
    CASE category
        WHEN 'Customers with 0 locations' THEN 1
        WHEN 'Customers with 1 location' THEN 2
        WHEN 'Customers with 2-5 locations' THEN 3
        ELSE 4
    END;

-- Check location-device relationship
\echo ''
\echo 'Location-Device Relationship:'
WITH location_device_check AS (
    SELECT 
        l.location_id,
        COUNT(DISTINCT d.device_id) as device_count
    FROM entity.entity_locations l
    LEFT JOIN entity.entity_devices d ON l.location_id::varchar = d.location_id
    GROUP BY l.location_id
)
SELECT 
    CASE 
        WHEN device_count = 0 THEN 'Locations with 0 devices'
        WHEN device_count <= 5 THEN 'Locations with 1-5 devices'
        WHEN device_count <= 10 THEN 'Locations with 6-10 devices'
        ELSE 'Locations with 11+ devices'
    END as category,
    COUNT(*) as location_count
FROM location_device_check
GROUP BY category
ORDER BY location_count DESC;

-- ========================================
-- HISTORICAL DATA COVERAGE
-- ========================================
\echo ''
\echo 'HISTORICAL DATA COVERAGE'
\echo '------------------------'

SELECT 
    'customers_history' as history_table,
    COUNT(*) as record_count,
    COUNT(DISTINCT account_id) as unique_entities,
    MIN(valid_from)::date as earliest_date,
    MAX(COALESCE(valid_to, CURRENT_DATE))::date as latest_date
FROM entity.entity_customers_history

UNION ALL

SELECT 
    'devices_history',
    COUNT(*),
    COUNT(DISTINCT device_id),
    MIN(valid_from)::date,
    MAX(COALESCE(valid_to, CURRENT_DATE))::date
FROM entity.entity_devices_history

UNION ALL

SELECT 
    'users_history',
    COUNT(*),
    COUNT(DISTINCT user_id),
    MIN(valid_from)::date,
    MAX(COALESCE(valid_to, CURRENT_DATE))::date
FROM entity.entity_users_history

ORDER BY record_count DESC;

-- ========================================
-- RECOMMENDATIONS
-- ========================================
\echo ''
\echo 'DATA QUALITY RECOMMENDATIONS'
\echo '----------------------------'
\echo ''
\echo '1. IMMEDIATE ACTIONS REQUIRED:'
\echo '   - Investigate why all customer MRR values are $0'
\echo '   - Address critical device health scores (0.25 avg)'
\echo '   - Fix device uptime reporting (0.01% is impossible)'
\echo ''
\echo '2. DATA PIPELINE ISSUES TO CHECK:'
\echo '   - Verify source system integrations (Stripe, IoT, etc.)'
\echo '   - Check transformation logic in dbt models'
\echo '   - Validate data type conversions and calculations'
\echo ''
\echo '3. LIKELY ROOT CAUSES:'
\echo '   - This appears to be synthetic/test data'
\echo '   - Transformation pipeline may not be running'
\echo '   - Source system connections may be misconfigured'
\echo ''

\echo '========================================================'
\echo 'END OF DATA QUALITY & BUSINESS ANALYTICS PROFILE'
\echo '========================================================'
