-- DEVICE HEALTH INVESTIGATION: Understanding the 0.25/100 Crisis
-- =============================================================

\echo '============================================'
\echo 'DEVICE HEALTH INVESTIGATION: 0.25/100 CRISIS'
\echo '============================================'
\echo ''

-- Overall device health summary
\echo 'DEVICE HEALTH SUMMARY:'
\echo '---------------------'

SELECT 
    COUNT(*) as total_devices,
    ROUND(AVG(overall_health_score), 4) as avg_health,
    ROUND(MIN(overall_health_score), 4) as min_health,
    ROUND(MAX(overall_health_score), 4) as max_health,
    ROUND(STDDEV(overall_health_score), 4) as health_stddev,
    ROUND(AVG(uptime_percentage_30d), 4) as avg_uptime,
    ROUND(AVG(performance_score), 4) as avg_performance,
    ROUND(AVG(connectivity_score), 4) as avg_connectivity,
    ROUND(AVG(maintenance_score), 4) as avg_maintenance
FROM entity.entity_devices;

-- Health score distribution
\echo ''
\echo 'HEALTH SCORE DISTRIBUTION:'
\echo '-------------------------'

SELECT 
    ROUND(overall_health_score, 2) as health_score,
    COUNT(*) as device_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM entity.entity_devices
GROUP BY ROUND(overall_health_score, 2)
ORDER BY health_score;

-- Investigate component scores
\echo ''
\echo 'COMPONENT SCORE ANALYSIS:'
\echo '------------------------'

WITH score_analysis AS (
    SELECT 
        'Performance' as component,
        AVG(performance_score) as avg_score,
        MIN(performance_score) as min_score,
        MAX(performance_score) as max_score
    FROM entity.entity_devices
    UNION ALL
    SELECT 
        'Connectivity',
        AVG(connectivity_score),
        MIN(connectivity_score),
        MAX(connectivity_score)
    FROM entity.entity_devices
    UNION ALL
    SELECT 
        'Maintenance',
        AVG(maintenance_score),
        MIN(maintenance_score),
        MAX(maintenance_score)
    FROM entity.entity_devices
    UNION ALL
    SELECT 
        'Uptime %',
        AVG(uptime_percentage_30d),
        MIN(uptime_percentage_30d),
        MAX(uptime_percentage_30d)
    FROM entity.entity_devices
)
SELECT 
    component,
    ROUND(avg_score::numeric, 4) as avg_score,
    ROUND(min_score::numeric, 4) as min_score,
    ROUND(max_score::numeric, 4) as max_score
FROM score_analysis;

-- Check device events
\echo ''
\echo 'DEVICE EVENT ANALYSIS:'
\echo '---------------------'

SELECT 
    operational_status,
    COUNT(*) as device_count,
    AVG(total_events_30d) as avg_events_30d,
    AVG(throughput_mbps_30d) as avg_throughput,
    AVG(error_rate_30d) as avg_error_rate,
    AVG(alert_count_30d) as avg_alerts
FROM entity.entity_devices
GROUP BY operational_status;

-- Sample device details
\echo ''
\echo 'SAMPLE DEVICE DETAILS (First 10):'
\echo '--------------------------------'

SELECT 
    device_id,
    device_type,
    operational_status,
    overall_health_score,
    uptime_percentage_30d,
    total_events_30d,
    last_event_at,
    device_installed_date
FROM entity.entity_devices
ORDER BY device_id
LIMIT 10;

-- Check for calculation issues
\echo ''
\echo 'HEALTH SCORE CALCULATION CHECK:'
\echo '------------------------------'

SELECT 
    device_id,
    overall_health_score,
    performance_score,
    connectivity_score,
    maintenance_score,
    uptime_percentage_30d,
    -- Verify if overall health is average of components
    ROUND((performance_score + connectivity_score + maintenance_score) / 3.0, 4) as calculated_health
FROM entity.entity_devices
LIMIT 10;

-- Date range analysis
\echo ''
\echo 'DEVICE INSTALLATION DATE ANALYSIS:'
\echo '---------------------------------'

SELECT 
    EXTRACT(YEAR FROM device_installed_date) as install_year,
    COUNT(*) as device_count,
    AVG(overall_health_score) as avg_health,
    AVG(uptime_percentage_30d) as avg_uptime
FROM entity.entity_devices
GROUP BY EXTRACT(YEAR FROM device_installed_date)
ORDER BY install_year;

-- Check history table for patterns
\echo ''
\echo 'DEVICE HISTORY PATTERNS:'
\echo '-----------------------'

SELECT 
    COUNT(*) as total_history_records,
    COUNT(DISTINCT device_id) as unique_devices,
    MIN(valid_from)::date as earliest_change,
    MAX(valid_from)::date as latest_change,
    AVG(overall_health_score) as avg_historical_health
FROM entity.entity_devices_history
WHERE valid_from >= CURRENT_DATE - INTERVAL '30 days';
