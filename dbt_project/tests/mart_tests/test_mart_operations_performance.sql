-- Test mart_operations__performance for operations metrics
WITH operations_validation AS (
    SELECT 
        COUNT(*) AS total_locations,
        COUNT(DISTINCT location_id) AS unique_locations,
        SUM(CASE WHEN device_availability < 0 OR device_availability > 100 THEN 1 ELSE 0 END) AS invalid_availability,
        SUM(CASE WHEN mean_time_to_repair < 0 THEN 1 ELSE 0 END) AS negative_mttr,
        SUM(CASE WHEN mean_time_between_failures < 0 THEN 1 ELSE 0 END) AS negative_mtbf,
        SUM(CASE WHEN operational_efficiency < 0 OR operational_efficiency > 100 THEN 1 ELSE 0 END) AS invalid_efficiency,
        SUM(CASE WHEN service_level_achievement < 0 OR service_level_achievement > 100 THEN 1 ELSE 0 END) AS invalid_sla
    FROM {{ ref('mart_operations__performance') }}
),
performance_consistency AS (
    -- MTBF should be greater than MTTR
    SELECT 
        COUNT(*) AS inconsistent_metrics
    FROM {{ ref('mart_operations__performance') }}
    WHERE mean_time_between_failures < mean_time_to_repair
      AND mean_time_between_failures > 0
),
sla_validation AS (
    -- Low availability should correlate with low SLA achievement
    SELECT 
        COUNT(*) AS inconsistent_sla
    FROM {{ ref('mart_operations__performance') }}
    WHERE (device_availability < 90 AND service_level_achievement > 95)
       OR (device_availability > 99 AND service_level_achievement < 80)
),
priority_validation AS (
    -- Check priority assignments
    SELECT 
        COUNT(*) AS missing_priorities
    FROM {{ ref('mart_operations__performance') }}
    WHERE operational_efficiency < 70
      AND (priority_level IS NULL OR priority_level NOT IN ('critical', 'high', 'medium', 'low'))
),
invalid_data AS (
    SELECT 
        v.*,
        pc.inconsistent_metrics,
        sv.inconsistent_sla,
        pv.missing_priorities
    FROM operations_validation v
    CROSS JOIN performance_consistency pc
    CROSS JOIN sla_validation sv
    CROSS JOIN priority_validation pv
    WHERE v.invalid_availability > 0
       OR v.negative_mttr > 0
       OR v.negative_mtbf > 0
       OR v.invalid_efficiency > 0
       OR v.invalid_sla > 0
       OR pc.inconsistent_metrics > 0
       OR sv.inconsistent_sla > 0
       OR pv.missing_priorities > 0
)
-- Test fails if operations metrics are invalid
SELECT * FROM invalid_data