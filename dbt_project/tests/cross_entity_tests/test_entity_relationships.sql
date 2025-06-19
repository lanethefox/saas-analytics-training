-- Test: Cross-Entity Relationship Integrity
-- Ensures referential integrity and logical consistency across entities

-- Test 1: Customer-Device Relationship Consistency
select 
    'customer_device_mismatch' as test_type,
    c.account_id,
    c.account_name,
    c.active_devices as customer_reported_devices,
    count(d.device_id) as actual_active_devices
from {{ ref('entity_customers') }} c
left join {{ ref('entity_devices') }} d 
    on c.account_id = d.account_id 
    and d.device_status = 'active'
group by c.account_id, c.account_name, c.active_devices
having c.active_devices != count(d.device_id)

union all

-- Test 2: Customer-Location Relationship Consistency  
select 
    'customer_location_mismatch' as test_type,
    c.account_id,
    c.account_name,
    c.total_locations as customer_reported_locations,
    count(l.location_id)::text as actual_locations
from {{ ref('entity_customers') }} c
left join {{ ref('entity_locations') }} l 
    on c.account_id = l.account_id
group by c.account_id, c.account_name, c.total_locations
having c.total_locations != count(l.location_id)

union all

-- Test 3: Device-Location Relationship Consistency
select 
    'device_location_orphan' as test_type,
    d.device_id,
    d.location_id,
    d.account_id,
    'device has invalid location reference'
from {{ ref('entity_devices') }} d
left join {{ ref('entity_locations') }} l 
    on d.location_id = l.location_id
where l.location_id is null

union all

-- Test 4: User-Customer Relationship Consistency
select 
    'user_account_orphan' as test_type,
    u.user_id,
    u.account_id,
    u.email,
    'user has invalid account reference'
from {{ ref('entity_users') }} u
left join {{ ref('entity_customers') }} c 
    on u.account_id = c.account_id
where c.account_id is null

union all

-- Test 5: Device Events Aggregation Consistency
select 
    'device_events_mismatch' as test_type,
    d.device_id,
    d.account_id,
    d.events_30d::text as device_reported_events,
    count(te.event_id)::text as actual_events_30d
from {{ ref('entity_devices') }} d
left join {{ ref('stg_app_database__tap_events') }} te 
    on d.device_id = te.device_id 
    and te.event_date >= current_date - 30
group by d.device_id, d.account_id, d.events_30d
having abs(d.events_30d - count(te.event_id)) > 10  -- Allow small variance for timing differences
