-- Simple Data Profile for Superset Dashboard Planning
-- This provides key metrics about your data

SELECT '========================================' as info
UNION ALL
SELECT 'BAR MANAGEMENT SAAS - DATA PROFILE' as info
UNION ALL
SELECT '========================================' as info
UNION ALL
SELECT '' as info
UNION ALL
SELECT 'CUSTOMERS' as info
UNION ALL
SELECT '---------' as info
UNION ALL
SELECT 'Total: ' || COUNT(*) || ' customers' FROM entity.entity_customers
UNION ALL
SELECT 'Total MRR: $' || TO_CHAR(SUM(monthly_recurring_revenue), 'FM999,999.00') FROM entity.entity_customers
UNION ALL
SELECT 'Avg Health Score: ' || ROUND(AVG(customer_health_score), 1) FROM entity.entity_customers
UNION ALL
SELECT 'High Risk (>70): ' || COUNT(*) || ' customers' FROM entity.entity_customers WHERE churn_risk_score > 70
UNION ALL
SELECT '' as info
UNION ALL
SELECT 'DEVICES' as info
UNION ALL
SELECT '-------' as info
UNION ALL
SELECT 'Total: ' || COUNT(*) || ' devices' FROM entity.entity_devices
UNION ALL
SELECT 'Active: ' || COUNT(*) || ' devices' FROM entity.entity_devices WHERE operational_status = 'active'
UNION ALL
SELECT 'Avg Uptime: ' || ROUND(AVG(uptime_percentage_30d), 1) || '%' FROM entity.entity_devices
UNION ALL
SELECT 'Need Attention: ' || COUNT(*) || ' devices' FROM entity.entity_devices WHERE requires_immediate_attention = TRUE
UNION ALL
SELECT '' as info
UNION ALL
SELECT 'USERS' as info
UNION ALL
SELECT '-----' as info
UNION ALL
SELECT 'Total: ' || COUNT(*) || ' users' FROM entity.entity_users
UNION ALL
SELECT 'Avg Engagement: ' || ROUND(AVG(engagement_score), 1) FROM entity.entity_users
UNION ALL
SELECT 'Highly Engaged: ' || COUNT(*) || ' users' FROM entity.entity_users WHERE user_engagement_tier = 'highly_engaged'
UNION ALL
SELECT '' as info
UNION ALL
SELECT 'LOCATIONS' as info
UNION ALL
SELECT '---------' as info
UNION ALL
SELECT 'Total: ' || COUNT(*) || ' locations' FROM entity.entity_locations
UNION ALL
SELECT 'Avg Health Score: ' || ROUND(AVG(operational_health_score), 1) FROM entity.entity_locations
UNION ALL
SELECT '' as info
UNION ALL
SELECT 'SUBSCRIPTIONS' as info
UNION ALL
SELECT '-------------' as info
UNION ALL
SELECT 'Total: ' || COUNT(*) || ' subscriptions' FROM entity.entity_subscriptions
UNION ALL
SELECT 'Active: ' || COUNT(*) || ' subscriptions' FROM entity.entity_subscriptions WHERE subscription_status = 'active'
UNION ALL
SELECT 'Avg Payment Health: ' || ROUND(AVG(payment_health_score), 1) FROM entity.entity_subscriptions;