            WHEN 'refrigerator' THEN 4
            WHEN 'dishwasher' THEN 45
            WHEN 'oven' THEN 25
            WHEN 'tap_system' THEN 8
            ELSE 22
        END,
        CASE device_type
            WHEN 'freezer' THEN 2
            WHEN 'refrigerator' THEN 1
            WHEN 'dishwasher' THEN 10
            WHEN 'oven' THEN 5
            ELSE 3
        END
    ),
    temperature_avg_24h = temperature_current + normalized.generate_normal_random(0, 0.5),
    temperature_max_24h = temperature_current + ABS(normalized.generate_normal_random(2, 1)),
    temperature_min_24h = temperature_current - ABS(normalized.generate_normal_random(2, 1)),
    
    -- Temperature events based on device type
    high_temp_events_30d = CASE 
        WHEN overall_health_score > 80 THEN FLOOR(normalized.generate_normal_random(2, 2))
        ELSE FLOOR(normalized.generate_normal_random(10, 5))
    END,
    low_temp_events_30d = CASE 
        WHEN overall_health_score > 80 THEN FLOOR(normalized.generate_normal_random(1, 1))
        ELSE FLOOR(normalized.generate_normal_random(5, 3))
    END,
    
    -- Pressure metrics (in PSI)
    pressure_current = CASE 
        WHEN device_type IN ('tap_system', 'dishwasher') THEN 
            normalized.generate_normal_random(45, 5)
        ELSE NULL
    END,
    pressure_avg_24h = pressure_current + normalized.generate_normal_random(0, 1),
    
    -- Pressure events
    high_pressure_events_30d = CASE 
        WHEN device_type IN ('tap_system', 'dishwasher') THEN 
            FLOOR(normalized.generate_normal_random(3, 2))
        ELSE 0
    END,
    low_pressure_events_30d = CASE 
        WHEN device_type IN ('tap_system', 'dishwasher') THEN 
            FLOOR(normalized.generate_normal_random(2, 2))
        ELSE 0
    END;

-- ========================================
-- Generate Usage and Performance Metrics
-- ========================================

UPDATE normalized.devices
SET 
    -- Usage minutes (higher for operational devices)
    usage_minutes_30d = CASE 
        WHEN operational_status = 'operational' THEN 
            FLOOR(normalized.generate_normal_random(20000, 5000))
        WHEN operational_status = 'maintenance' THEN 
            FLOOR(normalized.generate_normal_random(10000, 3000))
        ELSE 
            FLOOR(normalized.generate_normal_random(1000, 500))
    END,
    
    -- Active hours
    active_hours_30d = ROUND(usage_minutes_30d / 60.0, 2),
    
    -- Utilization percentage
    utilization_percentage = CASE 
        WHEN operational_status = 'operational' THEN 
            LEAST(100, normalized.generate_beta_random(3, 5) * 100)
        ELSE 
            LEAST(100, normalized.generate_normal_random(20, 15))
    END,
    
    -- Power consumption (kWh)
    power_consumption_kwh_30d = CASE device_type
        WHEN 'freezer' THEN normalized.generate_normal_random(150, 20)
        WHEN 'refrigerator' THEN normalized.generate_normal_random(100, 15)
        WHEN 'dishwasher' THEN normalized.generate_normal_random(80, 20)
        WHEN 'oven' THEN normalized.generate_normal_random(120, 30)
        WHEN 'tap_system' THEN normalized.generate_normal_random(30, 10)
        ELSE normalized.generate_normal_random(50, 20)
    END,
    
    -- Network metrics
    network_latency_ms_avg = normalized.generate_normal_random(25, 10),
    packet_loss_rate = GREATEST(0, normalized.generate_normal_random(0.1, 0.1)),
    bandwidth_usage_gb_30d = normalized.generate_normal_random(50, 20),
    
    -- System metrics
    cpu_usage_avg = CASE 
        WHEN operational_status = 'operational' THEN 
            normalized.generate_normal_random(35, 15)
        ELSE 
            normalized.generate_normal_random(60, 20)
    END,
    memory_usage_avg = normalized.generate_normal_random(45, 15),
    storage_usage_pct = normalized.generate_normal_random(30, 20);

-- ========================================
-- Generate Maintenance Metrics
-- ========================================

UPDATE normalized.devices
SET 
    -- Downtime (inverse of uptime)
    downtime_minutes_30d = ROUND((100 - uptime_percentage_30d) * 30 * 24 * 60 / 100),
    
    -- Restart count (more for unhealthy devices)
    restart_count_30d = CASE 
        WHEN overall_health_score > 80 THEN FLOOR(normalized.generate_normal_random(2, 2))
        WHEN overall_health_score > 60 THEN FLOOR(normalized.generate_normal_random(5, 3))
        ELSE FLOOR(normalized.generate_normal_random(15, 8))
    END,
    
    -- MTBF (Mean Time Between Failures) in hours
    mtbf_hours = CASE 
        WHEN overall_health_score > 80 THEN FLOOR(normalized.generate_normal_random(2000, 500))
        WHEN overall_health_score > 60 THEN FLOOR(normalized.generate_normal_random(1000, 300))
        ELSE FLOOR(normalized.generate_normal_random(500, 200))
    END,
    
    -- MTTR (Mean Time To Repair) in hours
    mttr_hours = CASE 
        WHEN overall_health_score > 80 THEN normalized.generate_normal_random(2, 1)
        WHEN overall_health_score > 60 THEN normalized.generate_normal_random(4, 2)
        ELSE normalized.generate_normal_random(8, 4)
    END,
    
    -- Failure prediction score (inverse of health)
    failure_prediction_score = LEAST(100, GREATEST(0, 
        100 - overall_health_score + normalized.generate_normal_random(0, 10)
    )),
    
    -- Maintenance due days (based on device age and health)
    maintenance_due_days = CASE 
        WHEN overall_health_score > 80 THEN FLOOR(normalized.generate_normal_random(90, 30))
        WHEN overall_health_score > 60 THEN FLOOR(normalized.generate_normal_random(30, 15))
        ELSE FLOOR(normalized.generate_normal_random(7, 5))
    END,
    
    -- Total maintenance cost (cumulative based on age)
    maintenance_cost_total = ROUND(
        device_age_days * 0.50 * -- Base cost per day
        (1 + (100 - overall_health_score) / 100) * -- Health factor
        normalized.generate_normal_random(1, 0.2), -- Variance
        2
    );

-- ========================================
-- Update Reliability Score
-- ========================================

UPDATE normalized.devices
SET 
    reliability_score = LEAST(100, GREATEST(0,
        (overall_health_score * 0.3 + 
         uptime_score * 0.3 + 
         performance_score * 0.2 + 
         alert_score * 0.2)
    ));

-- ========================================
-- Generate Score Summary Report
-- ========================================

\echo ''
\echo 'DEVICE METRICS GENERATION SUMMARY'
\echo '================================='
\echo ''
\echo 'Health Score Distribution:'

SELECT 
    CASE 
        WHEN overall_health_score >= 90 THEN '90-100 (Excellent)'
        WHEN overall_health_score >= 70 THEN '70-89 (Good)'
        WHEN overall_health_score >= 50 THEN '50-69 (Fair)'
        WHEN overall_health_score >= 30 THEN '30-49 (Poor)'
        ELSE '0-29 (Critical)'
    END as health_range,
    COUNT(*) as device_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    ROUND(AVG(uptime_percentage_30d), 2) as avg_uptime,
    ROUND(AVG(performance_score), 2) as avg_performance
FROM normalized.devices
GROUP BY health_range
ORDER BY 
    CASE 
        WHEN overall_health_score >= 90 THEN 1
        WHEN overall_health_score >= 70 THEN 2
        WHEN overall_health_score >= 50 THEN 3
        WHEN overall_health_score >= 30 THEN 4
        ELSE 5
    END;

\echo ''
\echo 'Operational Status Metrics:'

SELECT 
    operational_status,
    COUNT(*) as device_count,
    ROUND(AVG(overall_health_score), 2) as avg_health,
    ROUND(AVG(uptime_percentage_30d), 2) as avg_uptime,
    ROUND(AVG(total_events_30d), 0) as avg_events
FROM normalized.devices
GROUP BY operational_status
ORDER BY device_count DESC;

\echo ''
\echo 'Device Type Performance:'

SELECT 
    device_type,
    COUNT(*) as count,
    ROUND(AVG(overall_health_score), 2) as avg_health,
    ROUND(AVG(power_consumption_kwh_30d), 2) as avg_power_kwh,
    ROUND(AVG(maintenance_cost_total), 2) as avg_maint_cost
FROM normalized.devices
GROUP BY device_type
ORDER BY count DESC;

-- Clean up functions
DROP FUNCTION IF EXISTS normalized.generate_beta_random(NUMERIC, NUMERIC);
DROP FUNCTION IF EXISTS normalized.generate_normal_random(NUMERIC, NUMERIC);

\echo ''
\echo 'Device metrics generation completed successfully!'
