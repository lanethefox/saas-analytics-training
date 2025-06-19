-- Test: Entity Locations Operational Health Validation
-- Ensures location health scores and operational metrics are logical

select 
    location_id,
    location_key,
    account_id,
    location_health_score,
    operational_efficiency_score,
    capacity_utilization_pct,
    active_devices,
    total_events_30d,
    support_tickets_open
from {{ ref('entity_locations') }}
where 
    -- Health score validation
    location_health_score < 0 
    or location_health_score > 1
    
    -- Operational efficiency validation
    or operational_efficiency_score < 0
    or operational_efficiency_score > 1
    
    -- Capacity utilization validation
    or capacity_utilization_pct < 0
    or capacity_utilization_pct > 100
    
    -- Device count validation
    or active_devices < 0
    or active_devices > 100  -- Reasonable upper bound per location
    
    -- Event count validation
    or total_events_30d < 0
    
    -- Support ticket validation
    or support_tickets_open < 0
    or support_tickets_open > 20  -- Reasonable upper bound
    
    -- Required field validation
    or location_key is null
    or account_id is null
    or location_name is null
    or location_status is null
    
    -- Logical consistency checks
    or (location_status = 'active' and active_devices = 0)  -- Active locations should have devices
    or (active_devices > 0 and total_events_30d = 0)  -- Locations with devices should have events
    or (support_tickets_open > 5 and location_health_score > 0.8)  -- High support tickets should impact health score
