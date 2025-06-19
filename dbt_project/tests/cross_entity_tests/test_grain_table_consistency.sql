-- Test: Grain Table Temporal Consistency
-- Ensures grain tables (daily, weekly, monthly, hourly) maintain logical temporal patterns

-- Test 1: Customer Daily Grain Consistency
select 
    'customers_daily_inconsistency' as test_type,
    account_id,
    snapshot_date,
    device_events,
    lag(device_events) over (partition by account_id order by snapshot_date) as previous_day_events
from {{ ref('entity_customers_daily') }}
where 
    -- Check for impossible daily event spikes (>500% increase day-over-day)
    device_events > (lag(device_events) over (partition by account_id order by snapshot_date) * 5)
    and lag(device_events) over (partition by account_id order by snapshot_date) > 0

union all

-- Test 2: Device Hourly Grain Consistency
select 
    'devices_hourly_inconsistency' as test_type,
    device_id,
    hour_timestamp::text,
    hourly_events::text,
    lag(hourly_events) over (partition by device_id order by hour_timestamp)::text as previous_hour_events
from {{ ref('entity_devices_hourly') }}
where 
    -- Check for impossible hourly event spikes (>1000% increase hour-over-hour)
    hourly_events > (lag(hourly_events) over (partition by device_id order by hour_timestamp) * 10)
    and lag(hourly_events) over (partition by device_id order by hour_timestamp) > 0

union all

-- Test 3: Users Weekly Grain Consistency  
select 
    'users_weekly_inconsistency' as test_type,
    user_id,
    week_start_date::text,
    weekly_sessions::text,
    lag(weekly_sessions) over (partition by user_id order by week_start_date)::text as previous_week_sessions
from {{ ref('entity_users_weekly') }}
where 
    -- Check for impossible weekly session spikes (>300% increase week-over-week)
    weekly_sessions > (lag(weekly_sessions) over (partition by user_id order by week_start_date) * 3)
    and lag(weekly_sessions) over (partition by user_id order by week_start_date) > 0

union all

-- Test 4: Locations Monthly Grain Consistency
select 
    'locations_monthly_inconsistency' as test_type,
    location_id,
    month_start_date::text,
    monthly_device_events::text,
    lag(monthly_device_events) over (partition by location_id order by month_start_date)::text as previous_month_events
from {{ ref('entity_locations_monthly') }}
where 
    -- Check for impossible monthly event drops (>90% decrease month-over-month)
    monthly_device_events < (lag(monthly_device_events) over (partition by location_id order by month_start_date) * 0.1)
    and lag(monthly_device_events) over (partition by location_id order by month_start_date) > 100
