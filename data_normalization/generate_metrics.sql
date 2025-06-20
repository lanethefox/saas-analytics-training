-- Generate realistic metrics for normalized data
-- This script enhances the normalized data with realistic business metrics

-- 1. Update device health scores with realistic distribution
UPDATE normalized.devices
SET health_score = 
    CASE 
        WHEN device_type IN ('POS Terminal', 'Payment Processor') THEN 
            -- Critical devices have higher health scores
            0.85 + (RANDOM() * 0.1)
        WHEN maintenance_status = 'overdue' THEN
            -- Overdue maintenance = lower scores
            0.3 + (RANDOM() * 0.2)
        WHEN days_since_maintenance > 180 THEN
            -- Long time since maintenance
            0.4 + (RANDOM() * 0.3)
        WHEN operational_status = 'operational' THEN
            -- Normal operational devices
            0.7 + (RANDOM() * 0.25)
        ELSE
            -- Default range
            0.5 + (RANDOM() * 0.4)
    END
WHERE health_score BETWEEN 0.5 AND 0.9;

-- 2. Update customer health scores based on subscription data
UPDATE normalized.customers c
SET customer_health_score = 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM normalized.subscriptions s 
            WHERE s.account_id = c.account_id 
            AND s.monthly_recurring_revenue > 1000
        ) THEN 85 + (RANDOM() * 10) -- High-value customers
        WHEN EXISTS (
            SELECT 1 FROM normalized.subscriptions s 
            WHERE s.account_id = c.account_id 
            AND s.monthly_recurring_revenue > 200
        ) THEN 70 + (RANDOM() * 15) -- Mid-value customers
        WHEN EXISTS (
            SELECT 1 FROM normalized.subscriptions s 
            WHERE s.account_id = c.account_id 
            AND s.monthly_recurring_revenue > 0
        ) THEN 50 + (RANDOM() * 20) -- Low-value customers
        ELSE 20 + (RANDOM() * 30) -- No active subscriptions
    END;

-- 3. Update location operational metrics
UPDATE normalized.locations l
SET 
    device_count = (
        SELECT COUNT(*) 
        FROM normalized.devices d 
        WHERE d.location_id = l.location_id
    ),
    active_device_count = (
        SELECT COUNT(*) 
        FROM normalized.devices d 
        WHERE d.location_id = l.location_id 
        AND d.status = 'active'
    );

-- 4. Generate subscription growth patterns
WITH subscription_cohorts AS (
    SELECT 
        subscription_id,
        account_id,
        DATE_TRUNC('month', created_at) AS cohort_month,
        monthly_recurring_revenue
    FROM normalized.subscriptions
)
UPDATE normalized.subscriptions s
SET monthly_recurring_revenue = 
    CASE 
        -- Simulate growth for older cohorts
        WHEN s.created_at < CURRENT_DATE - INTERVAL '12 months' THEN
            s.monthly_recurring_revenue * (1.1 + RANDOM() * 0.2)
        WHEN s.created_at < CURRENT_DATE - INTERVAL '6 months' THEN
            s.monthly_recurring_revenue * (1.05 + RANDOM() * 0.1)
        ELSE
            s.monthly_recurring_revenue
    END
WHERE s.status = true AND s.monthly_recurring_revenue > 0;

-- Show results
SELECT 'Metric Generation Complete' AS status;

-- Device health distribution
SELECT 
    'Device Health Metrics' AS metric_type,
    device_type,
    COUNT(*) AS devices,
    ROUND(AVG(health_score)::NUMERIC, 2) AS avg_health,
    ROUND(MIN(health_score)::NUMERIC, 2) AS min_health,
    ROUND(MAX(health_score)::NUMERIC, 2) AS max_health,
    ROUND(STDDEV(health_score)::NUMERIC, 3) AS health_stddev
FROM normalized.devices
GROUP BY device_type
ORDER BY devices DESC
LIMIT 5;

-- Customer health distribution
SELECT 
    'Customer Health Metrics' AS metric_type,
    CASE 
        WHEN customer_health_score >= 80 THEN 'Healthy'
        WHEN customer_health_score >= 60 THEN 'At Risk'
        WHEN customer_health_score >= 40 THEN 'Critical'
        ELSE 'Churned'
    END AS health_category,
    COUNT(*) AS customers,
    ROUND(AVG(customer_health_score), 1) AS avg_score
FROM normalized.customers
GROUP BY health_category
ORDER BY avg_score DESC;

-- Revenue growth simulation
SELECT 
    'Revenue Growth Metrics' AS metric_type,
    plan_tier,
    COUNT(*) AS subscriptions,
    ROUND(SUM(monthly_recurring_revenue)::NUMERIC, 2) AS total_mrr,
    ROUND(AVG(monthly_recurring_revenue)::NUMERIC, 2) AS avg_mrr
FROM normalized.subscriptions
WHERE status = true
GROUP BY plan_tier
ORDER BY total_mrr DESC;
