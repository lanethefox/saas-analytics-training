-- Test int_locations__operational_metrics for operational data quality
WITH operational_validation AS (
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT location_id) AS unique_locations,
        SUM(CASE WHEN device_count < 0 THEN 1 ELSE 0 END) AS negative_device_count,
        SUM(CASE WHEN active_device_percentage < 0 OR active_device_percentage > 100 THEN 1 ELSE 0 END) AS invalid_active_percentage,
        SUM(CASE WHEN avg_device_health < 0 OR avg_device_health > 100 THEN 1 ELSE 0 END) AS invalid_avg_health,
        SUM(CASE WHEN total_events_processed < 0 THEN 1 ELSE 0 END) AS negative_events,
        SUM(CASE WHEN operational_efficiency < 0 OR operational_efficiency > 100 THEN 1 ELSE 0 END) AS invalid_efficiency
    FROM {{ ref('int_locations__operational_metrics') }}
),
metric_consistency AS (
    -- Check metric consistency
    SELECT 
        COUNT(*) AS inconsistent_metrics
    FROM {{ ref('int_locations__operational_metrics') }}
    WHERE device_count = 0 
      AND (active_device_percentage > 0 OR total_events_processed > 0)  -- No devices but activity
),
invalid_metrics AS (
    SELECT 
        v.*,
        c.inconsistent_metrics
    FROM operational_validation v
    CROSS JOIN metric_consistency c
    WHERE v.negative_device_count > 0
       OR v.invalid_active_percentage > 0
       OR v.invalid_avg_health > 0
       OR v.negative_events > 0
       OR v.invalid_efficiency > 0
       OR c.inconsistent_metrics > 0
)
-- Test fails if operational metrics are invalid
SELECT * FROM invalid_metrics
WHERE negative_device_count > 0
   OR invalid_active_percentage > 0
   OR invalid_avg_health > 0
   OR negative_events > 0
   OR invalid_efficiency > 0
   OR inconsistent_metrics > 0