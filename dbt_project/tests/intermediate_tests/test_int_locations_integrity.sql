-- Test int_locations__core for location data quality
WITH location_validation AS (
    SELECT 
        COUNT(*) AS total_locations,
        COUNT(DISTINCT location_id) AS unique_locations,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS missing_account_id,
        SUM(CASE WHEN location_name IS NULL OR TRIM(location_name) = '' THEN 1 ELSE 0 END) AS missing_location_name,
        SUM(CASE WHEN latitude < -90 OR latitude > 90 THEN 1 ELSE 0 END) AS invalid_latitude,
        SUM(CASE WHEN longitude < -180 OR longitude > 180 THEN 1 ELSE 0 END) AS invalid_longitude,
        SUM(CASE WHEN created_at > CURRENT_DATE THEN 1 ELSE 0 END) AS future_created_dates
    FROM {{ ref('int_locations__core') }}
),
duplicate_locations AS (
    SELECT 
        location_id,
        COUNT(*) AS occurrences
    FROM {{ ref('int_locations__core') }}
    GROUP BY location_id
    HAVING COUNT(*) > 1
),
location_account_check AS (
    -- Ensure all locations belong to valid accounts
    SELECT 
        COUNT(*) AS orphaned_locations
    FROM {{ ref('int_locations__core') }} l
    LEFT JOIN {{ ref('int_customers__core') }} c
        ON l.account_id = c.account_id
    WHERE c.account_id IS NULL
),
invalid_data AS (
    SELECT 
        v.*,
        a.orphaned_locations,
        (SELECT COUNT(*) FROM duplicate_locations) AS duplicate_count
    FROM location_validation v
    CROSS JOIN location_account_check a
    WHERE v.missing_account_id > 0
       OR v.missing_location_name > 0
       OR v.invalid_latitude > 0
       OR v.invalid_longitude > 0
       OR v.future_created_dates > 0
       OR v.unique_locations != v.total_locations
       OR a.orphaned_locations > 0
)
-- Test fails if location data is invalid
SELECT * FROM invalid_data