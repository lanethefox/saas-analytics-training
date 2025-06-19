-- Data Normalization Monitoring Script
-- This script monitors the progress and status of data normalization

-- Check record counts for all entity tables
RAISE NOTICE 'ENTITY TABLE RECORD COUNTS:';
RAISE NOTICE '===========================';
SELECT 
    'entity.entity_customers' AS table_name, COUNT(*) AS records 
FROM entity.entity_customers
UNION ALL
SELECT 'entity.entity_subscriptions', COUNT(*) FROM entity.entity_subscriptions
UNION ALL
SELECT 'entity.entity_users', COUNT(*) FROM entity.entity_users
UNION ALL
SELECT 'entity.entity_locations', COUNT(*) FROM entity.entity_locations
UNION ALL
SELECT 'entity.entity_devices', COUNT(*) FROM entity.entity_devices
UNION ALL
SELECT 'entity.entity_campaigns', COUNT(*) FROM entity.entity_campaigns
UNION ALL
SELECT 'entity.entity_features', COUNT(*) FROM entity.entity_features
ORDER BY table_name;

-- Check normalized tables that exist
RAISE NOTICE '';
RAISE NOTICE 'NORMALIZED TABLES CREATED:';
RAISE NOTICE '==========================';
SELECT 
    table_schema,
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE c.table_schema = tables.table_schema 
     AND c.table_name = tables.table_name) AS column_count
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check mapping table statistics
RAISE NOTICE '';
RAISE NOTICE 'ID MAPPING STATISTICS:';
RAISE NOTICE '=====================';
SELECT 
    COUNT(*) AS total_mappings,
    COUNT(DISTINCT normalized_account_id) AS unique_normalized_ids,
    COUNT(DISTINCT customer_account_id) AS mapped_customers,
    COUNT(DISTINCT subscription_account_id) AS mapped_subscriptions,
    COUNT(DISTINCT user_account_id) AS mapped_users,
    COUNT(DISTINCT location_account_id) AS mapped_locations,
    AVG(confidence_score) AS avg_confidence_score
FROM normalized.account_id_mapping;

-- Check data quality issues
RAISE NOTICE '';
RAISE NOTICE 'DATA QUALITY CHECK:';
RAISE NOTICE '==================';
WITH quality_checks AS (
    SELECT 
        'Customers with $0 MRR' AS issue,
        COUNT(*) AS count
    FROM entity.entity_customers
    WHERE customer_health_score = 0
    UNION ALL
    SELECT 
        'Devices with low health score',
        COUNT(*)
    FROM entity.entity_devices
    WHERE device_health_score < 0.3
    UNION ALL
    SELECT 
        'Users with no engagement',
        COUNT(*)
    FROM entity.entity_users
    WHERE engagement_score = 0
)
SELECT * FROM quality_checks WHERE count > 0;

-- Check normalized subscriptions if exists
RAISE NOTICE '';
RAISE NOTICE 'NORMALIZED SUBSCRIPTIONS STATUS:';
RAISE NOTICE '================================';
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'normalized' 
               AND table_name = 'subscriptions') THEN
        RAISE NOTICE 'Table exists - checking data...';
        PERFORM COUNT(*) FROM normalized.subscriptions;
    ELSE
        RAISE NOTICE 'Table does not exist yet';
    END IF;
END $$;

-- Show current database time
SELECT 'Current Time' AS info, NOW() AS value;
