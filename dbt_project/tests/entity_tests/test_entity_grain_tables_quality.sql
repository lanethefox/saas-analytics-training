-- Test all entity grain tables for aggregation accuracy
WITH grain_validation AS (
    -- Customers Daily
    SELECT 
        'entity_customers_daily' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT account_id || '|' || snapshot_date) AS unique_snapshots,
        SUM(CASE WHEN snapshot_date > CURRENT_DATE THEN 1 ELSE 0 END) AS future_dates,
        SUM(CASE WHEN trailing_30d_revenue < 0 THEN 1 ELSE 0 END) AS negative_metrics
    FROM {{ ref('entity_customers_daily') }}
    
    UNION ALL
    
    -- Devices Hourly
    SELECT 
        'entity_devices_hourly' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT device_id || '|' || hour_timestamp) AS unique_snapshots,
        SUM(CASE WHEN hour_timestamp > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates,
        SUM(CASE WHEN avg_throughput < 0 OR downtime_minutes < 0 THEN 1 ELSE 0 END) AS negative_metrics
    FROM {{ ref('entity_devices_hourly') }}
    
    UNION ALL
    
    -- Users Weekly
    SELECT 
        'entity_users_weekly' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT user_id || '|' || week_start_date) AS unique_snapshots,
        SUM(CASE WHEN week_start_date > CURRENT_DATE THEN 1 ELSE 0 END) AS future_dates,
        SUM(CASE WHEN weekly_sessions < 0 OR weekly_engagement_score < 0 THEN 1 ELSE 0 END) AS negative_metrics
    FROM {{ ref('entity_users_weekly') }}
),
duplicate_grain_records AS (
    -- Check for duplicate grain records
    SELECT 
        'customers_daily_duplicates' AS check_type,
        COUNT(*) AS duplicate_count
    FROM (
        SELECT account_id, snapshot_date, COUNT(*) AS cnt
        FROM {{ ref('entity_customers_daily') }}
        GROUP BY account_id, snapshot_date
        HAVING COUNT(*) > 1
    ) dups
    
    UNION ALL
    
    SELECT 
        'devices_hourly_duplicates' AS check_type,
        COUNT(*) AS duplicate_count
    FROM (
        SELECT device_id, hour_timestamp, COUNT(*) AS cnt
        FROM {{ ref('entity_devices_hourly') }}
        GROUP BY device_id, hour_timestamp
        HAVING COUNT(*) > 1
    ) dups
),
grain_issues AS (
    SELECT 
        g.*,
        (SELECT SUM(duplicate_count) FROM duplicate_grain_records) AS total_duplicates
    FROM grain_validation g
    WHERE g.future_dates > 0
       OR g.negative_metrics > 0
       OR g.total_records != g.unique_snapshots
)
-- Test fails if grain tables have issues
SELECT * FROM grain_issues
WHERE future_dates > 0
   OR negative_metrics > 0
   OR total_records != unique_snapshots
   OR total_duplicates > 0