-- Location Operations Profile
-- This script analyzes location performance and operational metrics

-- ========================================
-- 5. LOCATION OPERATIONS PROFILE
-- ========================================

WITH location_overview AS (
    SELECT 
        -- Basic counts
        COUNT(*) as total_locations,
        COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_locations,
        COUNT(DISTINCT account_id) as unique_accounts,
        
        -- Operational status
        COUNT(CASE WHEN operational_status = 'fully_operational' THEN 1 END) as fully_operational,
        COUNT(CASE WHEN operational_status = 'degraded' THEN 1 END) as degraded,
        COUNT(CASE WHEN operational_status = 'maintenance' THEN 1 END) as maintenance,
        COUNT(CASE WHEN operational_status = 'offline' THEN 1 END) as offline,
        
        -- Health metrics
        AVG(operational_health_score) as avg_health_score,
        MIN(operational_health_score) as min_health_score,
        MAX(operational_health_score) as max_health_score,
        
        -- Device metrics
        SUM(active_devices) as total_active_devices,
        AVG(active_devices) as avg_devices_per_location,
        AVG(device_utilization_rate) as avg_device_utilization,
        
        -- Performance metrics
        AVG(average_device_health) as avg_device_health,
        AVG(customer_satisfaction_score) as avg_satisfaction,
        SUM(support_tickets_30d) as total_support_tickets,
        
        -- Revenue
        SUM(revenue_per_location) as total_location_revenue,
        AVG(revenue_per_location) as avg_revenue_per_location
        
    FROM entity.entity_locations
),
location_by_region AS (
    SELECT 
        region,
        COUNT(*) as location_count,
        AVG(operational_health_score) as avg_health,
        SUM(active_devices) as total_devices,
        AVG(revenue_per_location) as avg_revenue
    FROM entity.entity_locations
    WHERE is_active = TRUE
    GROUP BY region
),
weekly_performance AS (
    SELECT 
        week_start_date,
        COUNT(DISTINCT location_id) as active_locations,
        AVG(weekly_operational_score) as avg_operational_score,
        SUM(weekly_device_events) as total_events,
        AVG(weekly_revenue) as avg_weekly_revenue,
        SUM(CASE WHEN weekly_activity_level = 'high' THEN 1 ELSE 0 END) as high_activity_locations
    FROM entity.entity_locations_weekly
    WHERE week_start_date >= CURRENT_DATE - INTERVAL '4 weeks'
    GROUP BY week_start_date
    ORDER BY week_start_date DESC
),
top_performing_locations AS (
    SELECT 
        location_name,
        city || ', ' || state as location,
        operational_health_score,
        active_devices,
        revenue_per_location
    FROM entity.entity_locations
    WHERE is_active = TRUE
    ORDER BY operational_health_score DESC
    LIMIT 10
),
locations_needing_attention AS (
    SELECT 
        location_name,
        city || ', ' || state as location,
        operational_health_score,
        support_tickets_30d,
        CASE 
            WHEN operational_status = 'degraded' THEN 'Degraded Performance'
            WHEN operational_status = 'offline' THEN 'Offline'
            WHEN support_tickets_30d > 10 THEN 'High Support Volume'
            WHEN device_utilization_rate < 50 THEN 'Low Utilization'
            ELSE 'Other Issues'
        END as primary_issue
    FROM entity.entity_locations
    WHERE operational_health_score < 70
       OR operational_status IN ('degraded', 'offline')
       OR support_tickets_30d > 10
    ORDER BY operational_health_score ASC
    LIMIT 10
)
SELECT 'LOCATION OPERATIONS PROFILE' as profile_section, '==========================' as value
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'LOCATION OVERVIEW', '-----------------'
UNION ALL
SELECT 'Total Locations', total_locations::text FROM location_overview
UNION ALL
SELECT 'Active Locations', active_locations::text || ' (' || ROUND(active_locations::numeric/total_locations*100, 1) || '%)' FROM location_overview
UNION ALL
SELECT 'Unique Accounts', unique_accounts::text FROM location_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'OPERATIONAL STATUS', '-----------------'
UNION ALL
SELECT 'Fully Operational', fully_operational::text || ' (' || ROUND(fully_operational::numeric/total_locations*100, 1) || '%)' FROM location_overview
UNION ALL
SELECT 'Degraded', degraded::text || ' (' || ROUND(degraded::numeric/total_locations*100, 1) || '%)' FROM location_overview
UNION ALL
SELECT 'Maintenance', maintenance::text || ' (' || ROUND(maintenance::numeric/total_locations*100, 1) || '%)' FROM location_overview
UNION ALL
SELECT 'Offline', offline::text || ' (' || ROUND(offline::numeric/total_locations*100, 1) || '%)' FROM location_overview
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'PERFORMANCE METRICS', '------------------'
UNION ALL
SELECT 'Avg Health Score', ROUND(avg_health_score, 2)::text FROM location_overview
UNION ALL
SELECT 'Avg Device Utilization', ROUND(avg_device_utilization, 1)::text || '%' FROM location_overview
UNION ALL
SELECT 'Avg Customer Satisfaction', ROUND(avg_satisfaction, 1)::text FROM location_overview
UNION ALL
SELECT 'Total Support Tickets (30d)', total_support_tickets::text FROM location_overview
UNION ALL
SELECT 'Avg Revenue per Location', '$' || TO_CHAR(avg_revenue_per_location, 'FM999,999.00') FROM location_overview;