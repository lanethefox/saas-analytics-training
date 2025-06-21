-- Test: Device Health and Performance Logic Validation
-- Ensures device health metrics align with operational reality

select 
    device_id,
    account_id,
    location_id,
    device_health_score,
    performance_score,
    uptime_percentage_30d,
    events_30d,
    events_7d,
    device_status,
    last_maintenance_date
from {{ ref('entity_devices') }}
where 
    -- High uptime should correlate with good health score
    (uptime_percentage_30d >= 95 and device_health_score < 0.7)
    
    -- Low uptime should indicate poor health
    or (uptime_percentage_30d < 80 and device_health_score > 0.6)
    
    -- High event volume should indicate good performance
    or (events_30d >= 1000 and performance_score < 0.6)
    
    -- Recent activity (7-day) should be reasonable proportion of 30-day
    or (events_7d > events_30d * 0.5)  -- 7-day events shouldn't exceed 50% of 30-day
    
    -- Inactive devices should have minimal events
    or (device_status = 'inactive' and events_7d > 10)
    
    -- Active devices with zero events for a week indicate problems
    or (device_status = 'active' and events_7d = 0 and device_health_score > 0.5)
    
    -- Devices with poor performance should have lower health scores
    or (performance_score < 0.4 and device_health_score > 0.6)
    
    -- Maintenance overdue should impact health score
    or (last_maintenance_date < current_date - 180 and device_health_score > 0.7)
    
    -- Never maintained devices should have health score considerations
    or (last_maintenance_date is null and device_health_score > 0.8 and 
        (current_date - device_created_at::date) > 90)
