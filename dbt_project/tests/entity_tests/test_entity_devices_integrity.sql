-- Test: Entity Devices Operational Integrity
-- Ensures device data follows operational rules

WITH device_checks AS (
    SELECT 
        device_id,
        device_name,
        device_type,
        device_status,
        overall_health_score,
        uptime_percentage_30d,
        maintenance_status,
        connectivity_status,
        total_events_30d,
        quality_issue_rate_30d,
        days_since_maintenance,
        
        -- Operational violations
        CASE 
            WHEN device_status = 'active' AND connectivity_status = 'offline' 
                 AND days_since_last_activity < 1 THEN 'Active device showing offline with recent activity'
            WHEN device_status = 'maintenance' AND total_events_30d > 100 THEN 'Device in maintenance with high activity'
            WHEN device_status = 'inactive' AND connectivity_status = 'online' THEN 'Inactive device showing online'
            ELSE NULL
        END as status_violation,
        
        CASE 
            WHEN uptime_percentage_30d > 100 THEN 'Uptime exceeds 100%'
            WHEN uptime_percentage_30d < 0 THEN 'Negative uptime'
            WHEN quality_issue_rate_30d > 100 THEN 'Quality issue rate exceeds 100%'
            WHEN quality_issue_rate_30d < 0 THEN 'Negative quality issue rate'
            ELSE NULL
        END as percentage_violation,
        
        CASE 
            WHEN overall_health_score < 30 AND requires_immediate_attention = FALSE THEN 'Poor health without alert flag'
            WHEN overall_health_score > 90 AND quality_issue_rate_30d > 20 THEN 'High health with high issues'
            WHEN maintenance_status = 'overdue' AND days_since_maintenance < 30 THEN 'Overdue maintenance but recently serviced'
            ELSE NULL
        END as health_violation,
        
        CASE 
            WHEN total_events_30d > 1000000 THEN 'Unusually high event count'
            WHEN device_type = 'tap' AND total_events_30d = 0 AND device_status = 'active' THEN 'Active tap with no events'
            ELSE NULL
        END as activity_violation
        
    FROM {{ ref('entity_devices') }}
)
SELECT 
    device_id,
    device_name,
    device_type,
    device_status,
    COALESCE(status_violation, percentage_violation, health_violation, activity_violation) as violation_type,
    overall_health_score,
    uptime_percentage_30d,
    quality_issue_rate_30d,
    total_events_30d,
    connectivity_status,
    maintenance_status
FROM device_checks
WHERE status_violation IS NOT NULL
   OR percentage_violation IS NOT NULL
   OR health_violation IS NOT NULL
   OR activity_violation IS NOT NULL;