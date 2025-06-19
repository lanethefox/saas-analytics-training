-- Device Usage and Performance Profile
-- This script analyzes device health, usage patterns, and operational metrics

-- ========================================
-- 2. DEVICE USAGE PROFILE
-- ========================================

WITH device_overview AS (
    SELECT 
        -- Basic counts
        COUNT(*) as total_devices,
        COUNT(DISTINCT device_id) as unique_devices,
        COUNT(DISTINCT location_id) as locations_with_devices,
        
        -- Device type distribution
        COUNT(CASE WHEN device_type = 'tap_system' THEN 1 END) as tap_systems,
        COUNT(CASE WHEN device_type = 'pos_terminal' THEN 1 END) as pos_terminals,
        COUNT(CASE WHEN device_type = 'keg_sensor' THEN 1 END) as keg_sensors,
        COUNT(CASE WHEN device_type = 'display_unit' THEN 1 END) as display_units,
        
        -- Operational status
        COUNT(CASE WHEN operational_status = 'active' THEN 1 END) as active_devices,
        COUNT(CASE WHEN operational_status = 'warning' THEN 1 END) as warning_devices,
        COUNT(CASE WHEN operational_status = 'critical' THEN 1 END) as critical_devices,
        COUNT(CASE WHEN operational_status = 'offline' THEN 1 END) as offline_devices,
        COUNT(CASE WHEN operational_status = 'maintenance' THEN 1 END) as maintenance_devices,
        
        -- Health metrics
        AVG(overall_health_score) as avg_health_score,
        MIN(overall_health_score) as min_health_score,
        MAX(overall_health_score) as max_health_score,
        STDDEV(overall_health_score) as stddev_health_score,
        
        -- Uptime metrics
        AVG(uptime_percentage_30d) as avg_uptime_30d,
        COUNT(CASE WHEN uptime_percentage_30d < 95 THEN 1 END) as devices_below_sla,
        
        -- Maintenance
        COUNT(CASE WHEN requires_immediate_attention = TRUE THEN 1 END) as devices_need_attention,
        AVG(days_since_last_maintenance) as avg_days_since_maintenance
        
    FROM entity.entity_devices
),
device_performance_tiers AS (
    SELECT 
        performance_tier,
        device_type,
        COUNT(*) as device_count,
        AVG(overall_health_score) as avg_health,
        AVG(uptime_percentage_30d) as avg_uptime
    FROM entity.entity_devices
    GROUP BY performance_tier, device_type
),
hourly_device_metrics AS (
    SELECT 
        DATE(hour_timestamp) as metric_date,
        AVG(avg_throughput) as daily_avg_throughput,
        SUM(total_events) as daily_total_events,
        AVG(uptime_percentage) as daily_avg_uptime,
        SUM(downtime_minutes) as daily_downtime_minutes,
        SUM(alert_count) as daily_alerts
    FROM entity.entity_devices_hourly
    WHERE hour_timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY DATE(hour_timestamp)
),
device_event_patterns AS (
    SELECT 
        device_type,
        SUM(total_events_30d) as total_events,
        AVG(avg_daily_events) as avg_daily_events,
        MAX(peak_hour_events) as max_peak_hour_events
    FROM entity.entity_devices
    GROUP BY device_type
)
SELECT 'DEVICE USAGE PROFILE' as profile_section, '====================' as value
UNION ALL
SELECT 'Total Devices', total_devices::text FROM device_overview
UNION ALL
SELECT 'Locations with Devices', locations_with_devices::text FROM device_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'DEVICE TYPE DISTRIBUTION', '------------------------'
UNION ALL
SELECT 'Tap Systems', tap_systems::text || ' (' || ROUND(tap_systems::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'POS Terminals', pos_terminals::text || ' (' || ROUND(pos_terminals::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Keg Sensors', keg_sensors::text || ' (' || ROUND(keg_sensors::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Display Units', display_units::text || ' (' || ROUND(display_units::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'OPERATIONAL STATUS', '------------------'
UNION ALL
SELECT 'Active', active_devices::text || ' (' || ROUND(active_devices::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Warning', warning_devices::text || ' (' || ROUND(warning_devices::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Critical', critical_devices::text || ' (' || ROUND(critical_devices::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Offline', offline_devices::text || ' (' || ROUND(offline_devices::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT 'Maintenance', maintenance_devices::text || ' (' || ROUND(maintenance_devices::numeric/total_devices*100, 1) || '%)' FROM device_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'HEALTH METRICS', '--------------'
UNION ALL
SELECT 'Average Health Score', ROUND(avg_health_score, 2)::text FROM device_overview
UNION ALL
SELECT 'Average Uptime (30d)', ROUND(avg_uptime_30d, 2)::text || '%' FROM device_overview
UNION ALL
SELECT 'Devices Below SLA (<95%)', devices_below_sla::text FROM device_overview
UNION ALL
SELECT 'Need Immediate Attention', devices_need_attention::text FROM device_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'LAST 7 DAYS METRICS', '-------------------'
UNION ALL
SELECT TO_CHAR(metric_date, 'Mon DD'), 
       'Events: ' || TO_CHAR(daily_total_events, 'FM999,999') || 
       ', Uptime: ' || ROUND(daily_avg_uptime, 1) || '%' ||
       ', Alerts: ' || daily_alerts
FROM hourly_device_metrics
ORDER BY 
    CASE 
        WHEN profile_section LIKE '%PROFILE%' THEN 1
        WHEN profile_section LIKE 'Total%' THEN 2
        WHEN profile_section LIKE 'Location%' THEN 3
        ELSE 99
    END,
    profile_section;