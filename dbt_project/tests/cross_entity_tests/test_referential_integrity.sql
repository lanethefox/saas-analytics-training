-- Test: Cross-Entity Referential Integrity
-- Ensures relationships between entities are valid

WITH customer_location_check AS (
    -- Every location should belong to a valid customer
    SELECT 
        l.location_id,
        l.account_id,
        l.location_name,
        c.company_name
    FROM {{ ref('entity_locations') }} l
    LEFT JOIN {{ ref('entity_customers') }} c ON l.account_id = c.account_id
    WHERE c.account_id IS NULL
),
customer_device_check AS (
    -- Every device should belong to a valid customer
    SELECT 
        d.device_id,
        d.account_id,
        d.device_name,
        c.company_name
    FROM {{ ref('entity_devices') }} d
    LEFT JOIN {{ ref('entity_customers') }} c ON d.account_id = c.account_id
    WHERE c.account_id IS NULL
),
customer_user_check AS (
    -- Every user should belong to a valid customer
    SELECT 
        u.user_id,
        u.account_id,
        u.email,
        c.company_name
    FROM {{ ref('entity_users') }} u
    LEFT JOIN {{ ref('entity_customers') }} c ON u.account_id = c.account_id
    WHERE c.account_id IS NULL
),
aggregate_consistency AS (
    -- Customer aggregate counts should match reality
    SELECT 
        c.account_id,
        c.company_name,
        c.total_locations,
        COUNT(DISTINCT l.location_id) as actual_locations,
        c.total_devices,
        COUNT(DISTINCT d.device_id) as actual_devices,
        c.total_users,
        COUNT(DISTINCT u.user_id) as actual_users
    FROM {{ ref('entity_customers') }} c
    LEFT JOIN {{ ref('entity_locations') }} l ON c.account_id = l.account_id AND l.location_status = 'active'
    LEFT JOIN {{ ref('entity_devices') }} d ON c.account_id = d.account_id AND d.device_status = 'active'
    LEFT JOIN {{ ref('entity_users') }} u ON c.account_id = u.account_id AND u.user_status = 'active'
    WHERE c.customer_status = 'active'
    GROUP BY c.account_id, c.company_name, c.total_locations, c.total_devices, c.total_users
    HAVING c.total_locations != COUNT(DISTINCT l.location_id)
        OR c.total_devices != COUNT(DISTINCT d.device_id)
        OR c.total_users != COUNT(DISTINCT u.user_id)
)
SELECT 'Orphaned Location' as issue_type, location_id as entity_id, location_name as entity_name, account_id FROM customer_location_check
UNION ALL
SELECT 'Orphaned Device' as issue_type, device_id as entity_id, device_name as entity_name, account_id FROM customer_device_check
UNION ALL
SELECT 'Orphaned User' as issue_type, user_id as entity_id, email as entity_name, account_id FROM customer_user_check
UNION ALL
SELECT 'Count Mismatch' as issue_type, account_id::text as entity_id, company_name as entity_name, account_id FROM aggregate_consistency;