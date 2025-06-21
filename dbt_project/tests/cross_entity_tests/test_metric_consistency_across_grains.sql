-- Test metric consistency across entity tables
WITH customer_metrics AS (
    -- Compare metrics between atomic and daily grain
    SELECT 
        a.account_id,
        a.monthly_recurring_revenue AS atomic_mrr,
        d.monthly_recurring_revenue AS daily_mrr,
        a.churn_risk_score AS atomic_churn_risk,
        d.churn_risk_score AS daily_churn_risk
    FROM {{ ref('entity_customers') }} a
    JOIN {{ ref('entity_customers_daily') }} d
        ON a.account_id = d.account_id
        AND d.snapshot_date = CURRENT_DATE - 1
),
metric_discrepancies AS (
    SELECT 
        COUNT(*) AS customers_with_discrepancies,
        AVG(ABS(atomic_mrr - daily_mrr)) AS avg_mrr_difference,
        MAX(ABS(atomic_mrr - daily_mrr)) AS max_mrr_difference,
        AVG(ABS(atomic_churn_risk - daily_churn_risk)) AS avg_risk_difference
    FROM customer_metrics
    WHERE ABS(atomic_mrr - daily_mrr) > 0.01
       OR ABS(atomic_churn_risk - daily_churn_risk) > 1
),
device_metrics AS (
    -- Compare device metrics between atomic and hourly
    SELECT 
        a.device_id,
        a.overall_health_score AS atomic_health,
        h.health_score AS hourly_health,
        a.uptime_percentage_30d AS atomic_uptime,
        AVG(h.uptime_percentage) AS avg_hourly_uptime
    FROM {{ ref('entity_devices') }} a
    JOIN {{ ref('entity_devices_hourly') }} h
        ON a.device_id = h.device_id
        AND h.hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
    GROUP BY 1, 2, 3, 4
),
device_discrepancies AS (
    SELECT 
        COUNT(*) AS devices_with_discrepancies,
        AVG(ABS(atomic_health - hourly_health)) AS avg_health_difference,
        AVG(ABS(atomic_uptime - avg_hourly_uptime)) AS avg_uptime_difference
    FROM device_metrics
    WHERE ABS(atomic_health - hourly_health) > 5
       OR ABS(atomic_uptime - avg_hourly_uptime) > 2
),
consistency_issues AS (
    SELECT 
        'customer_metrics' AS entity_type,
        m.customers_with_discrepancies AS records_affected,
        m.avg_mrr_difference,
        m.max_mrr_difference
    FROM metric_discrepancies m
    WHERE m.customers_with_discrepancies > 0
    
    UNION ALL
    
    SELECT 
        'device_metrics' AS entity_type,
        d.devices_with_discrepancies AS records_affected,
        d.avg_health_difference AS avg_mrr_difference,
        d.avg_uptime_difference AS max_mrr_difference
    FROM device_discrepancies d
    WHERE d.devices_with_discrepancies > 0
)
-- Test fails if metrics are inconsistent across tables
SELECT * FROM consistency_issues