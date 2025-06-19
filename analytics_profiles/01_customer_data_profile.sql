-- Data Quality Profile for SaaS Platform
-- This script generates comprehensive data quality metrics

-- ========================================
-- 1. CUSTOMER DATA PROFILE
-- ========================================

WITH customer_profile AS (
    SELECT 
        -- Basic counts
        COUNT(*) as total_customers,
        COUNT(DISTINCT account_id) as unique_accounts,
        COUNT(DISTINCT company_name) as unique_companies,
        
        -- Status distribution
        SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_customers,
        SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as inactive_customers,
        
        -- Health score distribution
        AVG(customer_health_score) as avg_health_score,
        MIN(customer_health_score) as min_health_score,
        MAX(customer_health_score) as max_health_score,
        STDDEV(customer_health_score) as stddev_health_score,
        
        -- Churn risk distribution
        AVG(churn_risk_score) as avg_churn_risk,
        SUM(CASE WHEN churn_risk_score >= 70 THEN 1 ELSE 0 END) as high_risk_customers,
        SUM(CASE WHEN churn_risk_score BETWEEN 40 AND 69 THEN 1 ELSE 0 END) as medium_risk_customers,
        SUM(CASE WHEN churn_risk_score < 40 THEN 1 ELSE 0 END) as low_risk_customers,
        
        -- Revenue metrics
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr,
        MIN(monthly_recurring_revenue) as min_mrr,
        MAX(monthly_recurring_revenue) as max_mrr,
        
        -- Device and location counts
        SUM(total_devices) as total_devices_all_customers,
        AVG(total_devices) as avg_devices_per_customer,
        SUM(active_locations) as total_active_locations,
        AVG(active_locations) as avg_locations_per_customer,
        
        -- User engagement
        SUM(active_users) as total_active_users,
        AVG(active_users) as avg_users_per_customer,
        AVG(avg_user_engagement_score) as overall_avg_engagement
        
    FROM entity.entity_customers
),
customer_segments AS (
    SELECT 
        customer_segment,
        COUNT(*) as customer_count,
        AVG(monthly_recurring_revenue) as avg_mrr,
        AVG(customer_health_score) as avg_health
    FROM entity.entity_customers
    GROUP BY customer_segment
),
customer_lifecycle AS (
    SELECT 
        customer_lifecycle_stage,
        COUNT(*) as customer_count,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(churn_risk_score) as avg_churn_risk
    FROM entity.entity_customers
    GROUP BY customer_lifecycle_stage
)
SELECT 'CUSTOMER DATA PROFILE' as profile_section, '====================' as value
UNION ALL
SELECT 'Total Customers', total_customers::text FROM customer_profile
UNION ALL
SELECT 'Active Customers', active_customers::text FROM customer_profile
UNION ALL
SELECT 'Inactive Customers', inactive_customers::text FROM customer_profile
UNION ALL
SELECT 'Average Health Score', ROUND(avg_health_score, 2)::text FROM customer_profile
UNION ALL
SELECT 'High Risk Customers', high_risk_customers::text FROM customer_profile
UNION ALL
SELECT 'Total MRR', '$' || TO_CHAR(total_mrr, 'FM999,999,999.00') FROM customer_profile
UNION ALL
SELECT 'Average MRR per Customer', '$' || TO_CHAR(avg_mrr, 'FM999,999.00') FROM customer_profile
UNION ALL
SELECT 'Total Devices', total_devices_all_customers::text FROM customer_profile
UNION ALL
SELECT 'Avg Devices per Customer', ROUND(avg_devices_per_customer, 1)::text FROM customer_profile
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'CUSTOMER SEGMENTS', '----------------'
UNION ALL
SELECT customer_segment || ' (' || customer_count || ')', 
       'Avg MRR: $' || TO_CHAR(avg_mrr, 'FM999,999.00') || ', Health: ' || ROUND(avg_health, 1)::text
FROM customer_segments
ORDER BY 
    CASE 
        WHEN profile_section = 'CUSTOMER DATA PROFILE' THEN 1
        WHEN profile_section = 'Total Customers' THEN 2
        WHEN profile_section = 'Active Customers' THEN 3
        WHEN profile_section = 'Inactive Customers' THEN 4
        WHEN profile_section = 'Average Health Score' THEN 5
        WHEN profile_section = 'High Risk Customers' THEN 6
        WHEN profile_section = 'Total MRR' THEN 7
        WHEN profile_section = 'Average MRR per Customer' THEN 8
        WHEN profile_section = 'Total Devices' THEN 9
        WHEN profile_section = 'Avg Devices per Customer' THEN 10
        WHEN profile_section = '' THEN 11
        WHEN profile_section = 'CUSTOMER SEGMENTS' THEN 12
        ELSE 13
    END;