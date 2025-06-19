-- Row count check for Raw and Entity layers
-- Raw Layer Counts
SELECT 'RAW LAYER' as layer, '==================' as count
UNION ALL
SELECT 'raw.app_database_accounts', COUNT(*)::text FROM raw.app_database_accounts
UNION ALL
SELECT 'raw.app_database_devices', COUNT(*)::text FROM raw.app_database_devices
UNION ALL
SELECT 'raw.app_database_locations', COUNT(*)::text FROM raw.app_database_locations
UNION ALL
SELECT 'raw.app_database_users', COUNT(*)::text FROM raw.app_database_users
UNION ALL
SELECT 'raw.app_database_subscriptions', COUNT(*)::text FROM raw.app_database_subscriptions
UNION ALL
-- Entity Layer Counts
SELECT 'ENTITY LAYER', '=================='
UNION ALL
SELECT 'entity.entity_customers', COUNT(*)::text FROM entity.entity_customers
UNION ALL
SELECT 'entity.entity_customers_daily', COUNT(*)::text FROM entity.entity_customers_daily
UNION ALL
SELECT 'entity.entity_customers_history', COUNT(*)::text FROM entity.entity_customers_history
UNION ALL
SELECT 'entity.entity_devices', COUNT(*)::text FROM entity.entity_devices
UNION ALL
SELECT 'entity.entity_devices_hourly', COUNT(*)::text FROM entity.entity_devices_hourly
UNION ALL
SELECT 'entity.entity_devices_history', COUNT(*)::text FROM entity.entity_devices_history
UNION ALL
SELECT 'entity.entity_locations', COUNT(*)::text FROM entity.entity_locations
UNION ALL
SELECT 'entity.entity_users', COUNT(*)::text FROM entity.entity_users
UNION ALL
SELECT 'entity.entity_subscriptions', COUNT(*)::text FROM entity.entity_subscriptions
ORDER BY 1;