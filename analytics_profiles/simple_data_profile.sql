-- Simplified Data Quality and Analytics Profile
-- This provides key insights for dashboard creation

-- ========================================
-- EXECUTIVE SUMMARY
-- ========================================

WITH summary_metrics AS (
    SELECT 
        -- Customer Metrics
        (SELECT COUNT(*) FROM entity.entity_customers) as total_customers,
        (SELECT COUNT(*) FROM entity.entity_customers WHERE is_active = TRUE) as active_customers,
        (SELECT SUM(monthly_recurring_revenue) FROM entity.entity_customers) as total_mrr,
        (SELECT AVG(customer_health_score) FROM entity.entity_customers) as avg_customer_health,
        
        -- Device Metrics
        (SELECT COUNT(*) FROM entity.entity_devices) as total_devices,
        (SELECT COUNT(*) FROM entity.entity_devices WHERE operational_status = 'active') as active_devices,
        (SELECT AVG(uptime_percentage_30d) FROM entity.entity_devices) as avg_device_uptime,
        
        -- User Metrics
        (SELECT COUNT(*) FROM entity.entity_users) as total_users,
        (SELECT COUNT(*) FROM entity.entity_users WHERE is_active = TRUE) as active_users,
        (SELECT AVG(engagement_score) FROM entity.entity_users WHERE is_active = TRUE) as avg_engagement,
        
        -- Location Metrics
        (SELECT COUNT(*) FROM entity.entity_locations) as total_locations,
        (SELECT COUNT(*) FROM entity.entity_locations WHERE is_active = TRUE) as active_locations,
        
        -- Subscription Metrics
        (SELECT COUNT(*) FROM entity.entity_subscriptions) as total_subscriptions,
        (SELECT COUNT(*) FROM entity.entity_subscriptions WHERE subscription_status = 'active') as active_subscriptions
),
customer_segments AS (
    SELECT 
        customer_segment,
        COUNT(*) as count,
        SUM(monthly_recurring_revenue) as segment_mrr
    FROM entity.entity_customers
    GROUP BY customer_segment
),
device_health_distribution AS (
    SELECT 
        operational_status,
        COUNT(*) as device_count
    FROM entity.entity_devices
    GROUP BY operational_status
),
subscription_plans AS (
    SELECT 
        plan_name,
        COUNT(*) as count,
        SUM(monthly_recurring_revenue) as plan_mrr
    FROM entity.entity_subscriptions
    WHERE subscription_status = 'active'
    GROUP BY plan_name
    ORDER BY plan_mrr DESC
    LIMIT 5
)
SELECT '========================================' as output
UNION ALL
SELECT 'DATA QUALITY & ANALYTICS PROFILE SUMMARY' as output
UNION ALL
SELECT '========================================' as output
UNION ALL
SELECT '' as output
UNION ALL
SELECT 'CUSTOMER METRICS' as output
UNION ALL
SELECT '----------------' as output
UNION ALL
SELECT 'Total Customers: ' || total_customers || ' (' || active_customers || ' active)' FROM summary_metrics
UNION ALL
SELECT 'Total MRR: $' || TO_CHAR(total_mrr, 'FM999,999,999.00') FROM summary_metrics
UNION ALL
SELECT 'Avg Customer Health: ' || ROUND(avg_customer_health, 1) FROM summary_metrics
UNION ALL
SELECT '' as output
UNION ALL
SELECT 'Customer Segments:' as output
UNION ALL
SELECT '  ' || customer_segment || ': ' || count || ' customers, $' || TO_CHAR(segment_mrr, 'FM999,999.00') || ' MRR'
FROM customer_segments
ORDER BY segment_mrr DESC
LIMIT 5;SELECT '' as output
UNION ALL
SELECT 'DEVICE METRICS' as output
UNION ALL
SELECT '--------------' as output
UNION ALL
SELECT 'Total Devices: ' || total_devices || ' (' || active_devices || ' active)' FROM summary_metrics
UNION ALL
SELECT 'Avg Device Uptime: ' || ROUND(avg_device_uptime, 1) || '%' FROM summary_metrics
UNION ALL
SELECT '' as output
UNION ALL
SELECT 'Device Status Distribution:' as output
UNION ALL
SELECT '  ' || operational_status || ': ' || device_count FROM device_health_distribution
ORDER BY 
    CASE operational_status 
        WHEN 'active' THEN 1
        WHEN 'warning' THEN 2
        WHEN 'critical' THEN 3
        WHEN 'offline' THEN 4
        WHEN 'maintenance' THEN 5
    END
LIMIT 5;SELECT '' as output
UNION ALL
SELECT 'USER ENGAGEMENT' as output
UNION ALL
SELECT '---------------' as output
UNION ALL
SELECT 'Total Users: ' || total_users || ' (' || active_users || ' active)' FROM summary_metrics
UNION ALL
SELECT 'Avg Engagement Score: ' || ROUND(avg_engagement, 1) FROM summary_metrics
UNION ALL
SELECT '' as output
UNION ALL
SELECT 'LOCATION & SUBSCRIPTION METRICS' as output
UNION ALL
SELECT '-------------------------------' as output
UNION ALL
SELECT 'Total Locations: ' || total_locations || ' (' || active_locations || ' active)' FROM summary_metrics
UNION ALL
SELECT 'Total Subscriptions: ' || total_subscriptions || ' (' || active_subscriptions || ' active)' FROM summary_metrics
UNION ALL
SELECT '' as output
UNION ALL
SELECT 'Top 5 Subscription Plans:' as output
UNION ALL
SELECT '  ' || plan_name || ': ' || count || ' subs, $' || TO_CHAR(plan_mrr, 'FM999,999.00') || ' MRR'
FROM subscription_plans
UNION ALL
SELECT '' as output
UNION ALL
SELECT '========================================' as output
UNION ALL
SELECT 'DASHBOARD RECOMMENDATIONS' as output
UNION ALL
SELECT '========================================' as output
UNION ALL
SELECT '' as output
UNION ALL
SELECT '1. Executive Dashboard: Focus on MRR trends, customer health, and churn risk' as output
UNION ALL
SELECT '2. Operations Dashboard: Device uptime, maintenance needs, location performance' as output
UNION ALL
SELECT '3. Customer Success: Health scores, engagement metrics, at-risk accounts' as output
UNION ALL
SELECT '4. Sales Dashboard: Pipeline, new customer acquisition, expansion revenue' as output
UNION ALL
SELECT '5. Product Analytics: Feature adoption, user engagement patterns' as output;