-- ============================================================
-- Business Analytics Assessment for TapFlow Analytics Platform
-- ============================================================

-- 1. EXECUTIVE SUMMARY METRICS
-- ------------------------------------------------------------
WITH summary_metrics AS (
    SELECT 
        -- Customer metrics
        COUNT(DISTINCT a.id) as total_accounts,
        COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,
        COUNT(DISTINCT l.id) as total_locations,
        COUNT(DISTINCT d.id) as total_devices,
        COUNT(DISTINCT u.id) as total_users,
        
        -- Subscription metrics
        COUNT(DISTINCT s.id) as total_subscriptions,
        COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.id END) as active_subscriptions,
        
        -- Revenue metrics
        SUM(CASE WHEN s.status = 'active' THEN s.monthly_price ELSE 0 END) as monthly_recurring_revenue,
        AVG(CASE WHEN s.status = 'active' THEN s.monthly_price ELSE NULL END) as avg_subscription_value
        
    FROM raw.app_database_accounts a
    LEFT JOIN raw.app_database_locations l ON l.customer_id = a.id
    LEFT JOIN raw.app_database_devices d ON d.location_id = l.id
    LEFT JOIN raw.app_database_users u ON u.customer_id = a.id
    LEFT JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
)
SELECT 
    'Executive Summary' as metric_category,
    'Total Accounts' as metric_name,
    total_accounts::varchar as metric_value
FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Active Accounts', active_accounts::varchar FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Total Locations', total_locations::varchar FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Total Devices', total_devices::varchar FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Total Users', total_users::varchar FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Active Subscriptions', active_subscriptions::varchar FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Monthly Recurring Revenue', '$' || TO_CHAR(monthly_recurring_revenue, 'FM999,999.00') FROM summary_metrics
UNION ALL
SELECT 'Executive Summary', 'Average Revenue Per Account', '$' || TO_CHAR(avg_subscription_value, 'FM999,999.00') FROM summary_metrics;

-- 2. CUSTOMER SEGMENTATION ANALYSIS
-- ------------------------------------------------------------
WITH customer_segments AS (
    SELECT 
        a.id,
        a.name,
        a.industry,
        a.employee_count,
        a.annual_revenue,
        COUNT(DISTINCT l.id) as location_count,
        COUNT(DISTINCT d.id) as device_count,
        COUNT(DISTINCT u.id) as user_count,
        s.plan_name,
        s.monthly_price,
        CASE 
            WHEN s.monthly_price >= 9999 THEN 'Enterprise'
            WHEN s.monthly_price >= 2999 THEN 'Business'
            WHEN s.monthly_price >= 999 THEN 'Professional'
            ELSE 'Starter'
        END as tier,
        CASE 
            WHEN COUNT(DISTINCT d.id) >= 500 THEN 'Large'
            WHEN COUNT(DISTINCT d.id) >= 100 THEN 'Medium'
            WHEN COUNT(DISTINCT d.id) >= 50 THEN 'Small'
            ELSE 'Micro'
        END as deployment_size
    FROM raw.app_database_accounts a
    LEFT JOIN raw.app_database_locations l ON l.customer_id = a.id
    LEFT JOIN raw.app_database_devices d ON d.location_id = l.id
    LEFT JOIN raw.app_database_users u ON u.customer_id = a.id
    LEFT JOIN raw.app_database_subscriptions s ON s.customer_id = a.id AND s.status = 'active'
    WHERE a.status = 'active'
    GROUP BY a.id, a.name, a.industry, a.employee_count, a.annual_revenue, s.plan_name, s.monthly_price
)
SELECT 
    'Customer Segmentation' as metric_category,
    'By Tier - ' || tier as metric_name,
    COUNT(*)::varchar || ' accounts' as metric_value
FROM customer_segments
GROUP BY tier
UNION ALL
SELECT 
    'Customer Segmentation',
    'By Deployment - ' || deployment_size,
    COUNT(*)::varchar || ' accounts'
FROM customer_segments
GROUP BY deployment_size
ORDER BY 1, 2;

-- 3. DEVICE HEALTH AND OPERATIONS
-- ------------------------------------------------------------
WITH device_metrics AS (
    SELECT 
        d.status,
        d.device_type,
        COUNT(*) as device_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
    FROM raw.app_database_devices d
    GROUP BY d.status, d.device_type
)
SELECT 
    'Device Operations' as metric_category,
    'Status: ' || status as metric_name,
    device_count::varchar || ' devices (' || percentage || '%)' as metric_value
FROM device_metrics
WHERE device_type = 'tap'
ORDER BY device_count DESC;

-- 4. USER ENGAGEMENT METRICS
-- ------------------------------------------------------------
WITH user_activity AS (
    SELECT 
        u.role,
        COUNT(DISTINCT u.id) as user_count,
        COUNT(DISTINCT CASE WHEN u.is_active = true THEN u.id END) as active_users,
        AVG(u.login_count) as avg_logins,
        MAX(u.last_login_at) as most_recent_login
    FROM raw.app_database_users u
    GROUP BY u.role
)
SELECT 
    'User Engagement' as metric_category,
    'Role: ' || role as metric_name,
    user_count::varchar || ' users (' || 
    ROUND(active_users * 100.0 / user_count, 1) || '% active)' as metric_value
FROM user_activity
ORDER BY user_count DESC;

-- 5. REVENUE ANALYSIS BY INDUSTRY
-- ------------------------------------------------------------
WITH industry_revenue AS (
    SELECT 
        a.industry,
        COUNT(DISTINCT a.id) as customer_count,
        SUM(CASE WHEN s.status = 'active' THEN s.monthly_price ELSE 0 END) as mrr,
        AVG(CASE WHEN s.status = 'active' THEN s.monthly_price ELSE NULL END) as avg_revenue
    FROM raw.app_database_accounts a
    LEFT JOIN raw.app_database_subscriptions s ON s.customer_id = a.id
    GROUP BY a.industry
    HAVING COUNT(DISTINCT a.id) >= 5
)
SELECT 
    'Revenue by Industry' as metric_category,
    industry as metric_name,
    '$' || TO_CHAR(mrr, 'FM999,999') || ' MRR (' || customer_count || ' customers)' as metric_value
FROM industry_revenue
ORDER BY mrr DESC
LIMIT 10;

-- 6. GEOGRAPHIC DISTRIBUTION
-- ------------------------------------------------------------
WITH location_stats AS (
    SELECT 
        l.state,
        COUNT(DISTINCT l.id) as location_count,
        COUNT(DISTINCT d.id) as device_count,
        COUNT(DISTINCT l.customer_id) as customer_count
    FROM raw.app_database_locations l
    LEFT JOIN raw.app_database_devices d ON d.location_id = l.id
    WHERE l.is_active = true
    GROUP BY l.state
    HAVING COUNT(DISTINCT l.id) >= 10
)
SELECT 
    'Geographic Distribution' as metric_category,
    state as metric_name,
    location_count::varchar || ' locations, ' || 
    device_count::varchar || ' devices' as metric_value
FROM location_stats
ORDER BY location_count DESC
LIMIT 10;

-- 7. SUBSCRIPTION LIFECYCLE METRICS
-- ------------------------------------------------------------
WITH subscription_lifecycle AS (
    SELECT 
        s.plan_name,
        COUNT(*) as total_subs,
        COUNT(CASE WHEN s.status = 'active' THEN 1 END) as active_subs,
        COUNT(CASE WHEN s.status = 'canceled' THEN 1 END) as canceled_subs,
        AVG(CASE 
            WHEN s.status = 'active' THEN 
                EXTRACT(EPOCH FROM (CURRENT_DATE - s.start_date)) / 86400
            WHEN s.end_date IS NOT NULL THEN 
                EXTRACT(EPOCH FROM (s.end_date - s.start_date)) / 86400
            ELSE NULL
        END) as avg_lifetime_days
    FROM raw.app_database_subscriptions s
    GROUP BY s.plan_name
)
SELECT 
    'Subscription Lifecycle' as metric_category,
    plan_name as metric_name,
    active_subs::varchar || ' active / ' || 
    total_subs::varchar || ' total (' ||
    ROUND(avg_lifetime_days)::varchar || ' day avg lifetime)' as metric_value
FROM subscription_lifecycle
ORDER BY active_subs DESC;

-- 8. DATA QUALITY METRICS
-- ------------------------------------------------------------
WITH data_quality AS (
    SELECT 
        'Accounts' as entity,
        COUNT(*) as total_records,
        COUNT(CASE WHEN email IS NOT NULL THEN 1 END) as complete_emails,
        COUNT(CASE WHEN industry IS NOT NULL THEN 1 END) as complete_industry,
        COUNT(CASE WHEN website IS NOT NULL THEN 1 END) as complete_website
    FROM raw.app_database_accounts
    UNION ALL
    SELECT 
        'Locations',
        COUNT(*),
        COUNT(CASE WHEN address IS NOT NULL THEN 1 END),
        COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END),
        COUNT(CASE WHEN longitude IS NOT NULL THEN 1 END)
    FROM raw.app_database_locations
    UNION ALL
    SELECT 
        'Users',
        COUNT(*),
        COUNT(CASE WHEN email IS NOT NULL THEN 1 END),
        COUNT(CASE WHEN phone IS NOT NULL THEN 1 END),
        COUNT(CASE WHEN last_login_at IS NOT NULL THEN 1 END)
    FROM raw.app_database_users
)
SELECT 
    'Data Quality' as metric_category,
    entity || ' Completeness' as metric_name,
    ROUND(100.0 * complete_emails / total_records, 1)::varchar || '% complete' as metric_value
FROM data_quality;

-- 9. TEMPORAL CONSISTENCY CHECK
-- ------------------------------------------------------------
WITH temporal_check AS (
    SELECT 
        'Account-Location' as relationship,
        COUNT(CASE 
            WHEN l.install_date < a.created_date THEN 1 
        END) as violations,
        COUNT(*) as total_checks
    FROM raw.app_database_locations l
    JOIN raw.app_database_accounts a ON a.id = l.customer_id
    WHERE l.install_date IS NOT NULL AND a.created_date IS NOT NULL
    UNION ALL
    SELECT 
        'Location-Device',
        COUNT(CASE 
            WHEN d.install_date < l.install_date THEN 1 
        END),
        COUNT(*)
    FROM raw.app_database_devices d
    JOIN raw.app_database_locations l ON l.id = d.location_id
    WHERE d.install_date IS NOT NULL AND l.install_date IS NOT NULL
)
SELECT 
    'Temporal Consistency' as metric_category,
    relationship as metric_name,
    CASE 
        WHEN violations = 0 THEN '✓ No violations'
        ELSE violations::varchar || ' violations found'
    END as metric_value
FROM temporal_check;

-- 10. GROWTH TRENDS (COHORT ANALYSIS)
-- ------------------------------------------------------------
WITH monthly_cohorts AS (
    SELECT 
        DATE_TRUNC('month', created_date) as cohort_month,
        COUNT(DISTINCT id) as accounts_created,
        SUM(COUNT(DISTINCT id)) OVER (ORDER BY DATE_TRUNC('month', created_date)) as cumulative_accounts
    FROM raw.app_database_accounts
    WHERE created_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', created_date)
)
SELECT 
    'Growth Trends' as metric_category,
    TO_CHAR(cohort_month, 'YYYY-MM') as metric_name,
    accounts_created::varchar || ' new (' || 
    cumulative_accounts::varchar || ' total)' as metric_value
FROM monthly_cohorts
ORDER BY cohort_month DESC
LIMIT 12;