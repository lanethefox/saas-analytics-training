-- Test int_devices__performance_health for performance metrics
WITH device_metrics AS (
    SELECT 
        COUNT(*) AS total_devices,
        COUNT(DISTINCT device_id) AS unique_devices,
        SUM(CASE WHEN uptime_score < 0 OR uptime_score > 1 THEN 1 ELSE 0 END) AS invalid_uptime,
        SUM(CASE WHEN performance_score < 0 OR performance_score > 1 THEN 1 ELSE 0 END) AS invalid_performance,
        SUM(CASE WHEN alert_score < 0 OR alert_score > 1 THEN 1 ELSE 0 END) AS invalid_alert_score,
        SUM(CASE WHEN avg_flow_rate_30d < 0 THEN 1 ELSE 0 END) AS negative_flow_rate,
        SUM(CASE WHEN overall_device_health_score < 0 OR overall_device_health_score > 1 THEN 1 ELSE 0 END) AS invalid_health_score
    FROM {{ ref('int_devices__performance_health') }}
),
performance_thresholds AS (
    SELECT 
        COUNT(*) AS critical_devices
    FROM {{ ref('int_devices__performance_health') }}
    WHERE overall_device_health_score < 0.5
      AND uptime_score > 0.95  -- High uptime but low health indicates other issues
),
invalid_metrics AS (
    SELECT *
    FROM device_metrics
    WHERE invalid_uptime > 0
       OR invalid_performance > 0
       OR invalid_alert_score > 0
       OR negative_flow_rate > 0
       OR invalid_health_score > 0
       OR unique_devices != total_devices
)
-- Test fails if performance metrics are invalid
SELECT 
    m.*,
    p.critical_devices
FROM invalid_metrics m
CROSS JOIN performance_thresholds p
WHERE m.invalid_uptime > 0
   OR m.invalid_performance > 0
   OR m.invalid_alert_score > 0
   OR m.negative_flow_rate > 0
   OR m.invalid_health_score > 0