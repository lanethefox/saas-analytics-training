-- Test int_devices__performance_health for performance metrics
WITH device_metrics AS (
    SELECT 
        COUNT(*) AS total_devices,
        COUNT(DISTINCT device_id) AS unique_devices,
        SUM(CASE WHEN uptime_percentage < 0 OR uptime_percentage > 100 THEN 1 ELSE 0 END) AS invalid_uptime,
        SUM(CASE WHEN response_time_avg < 0 THEN 1 ELSE 0 END) AS negative_response_time,
        SUM(CASE WHEN error_rate < 0 OR error_rate > 100 THEN 1 ELSE 0 END) AS invalid_error_rate,
        SUM(CASE WHEN throughput_avg < 0 THEN 1 ELSE 0 END) AS negative_throughput,
        SUM(CASE WHEN health_score < 0 OR health_score > 100 THEN 1 ELSE 0 END) AS invalid_health_score
    FROM {{ ref('int_devices__performance_health') }}
),
performance_thresholds AS (
    SELECT 
        COUNT(*) AS critical_devices
    FROM {{ ref('int_devices__performance_health') }}
    WHERE health_score < 50
      AND uptime_percentage > 95  -- High uptime but low health indicates other issues
),
invalid_metrics AS (
    SELECT *
    FROM device_metrics
    WHERE invalid_uptime > 0
       OR negative_response_time > 0
       OR invalid_error_rate > 0
       OR negative_throughput > 0
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
   OR m.negative_response_time > 0
   OR m.invalid_error_rate > 0
   OR m.negative_throughput > 0
   OR m.invalid_health_score > 0