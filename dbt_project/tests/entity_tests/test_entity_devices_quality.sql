-- Test: Entity Devices Performance and Health Validation
-- Ensures device health scores and performance metrics are logical and consistent

select 
    device_id,
    device_key,
    account_id,
    location_id,
    device_health_score,
    uptime_percentage_30d,
    events_30d,
    events_7d,
    performance_score
from {{ ref('entity_devices') }}
where 
    -- Health score validation
    device_health_score < 0 
    or device_health_score > 1
    
    -- Uptime validation
    or uptime_percentage_30d < 0
    or uptime_percentage_30d > 100
    
    -- Event count validation
    or events_30d < 0
    or events_7d < 0
    or events_7d > events_30d  -- 7-day events can't exceed 30-day events
    
    -- Performance score validation
    or performance_score < 0
    or performance_score > 1
    
    -- Required field validation
    or device_key is null
    or account_id is null
    or location_id is null
    or device_status is null
    
    -- Logical consistency checks
    or (device_status = 'active' and events_30d = 0 and events_7d = 0)  -- Active devices should have some events
    or (device_status = 'inactive' and (events_7d > 0 or uptime_percentage_30d > 10))  -- Inactive devices shouldn't have recent activity
