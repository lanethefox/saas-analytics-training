-- Row count check for Raw and Entity layers
-- Run this against your Docker PostgreSQL instance

-- Raw Layer Counts
SELECT 'RAW LAYER' as layer, '==================' as separator
UNION ALL
SELECT 'raw_accounts' as table_name, COUNT(*)::text as row_count FROM raw_accounts
UNION ALL
SELECT 'raw_devices' as table_name, COUNT(*)::text as row_count FROM raw_devices
UNION ALL
SELECT 'raw_locations' as table_name, COUNT(*)::text as row_count FROM raw_locations
UNION ALL
SELECT 'raw_users' as table_name, COUNT(*)::text as row_count FROM raw_users
UNION ALL
SELECT 'raw_subscriptions' as table_name, COUNT(*)::text as row_count FROM raw_subscriptions
UNION ALL
SELECT 'raw_feature_usage' as table_name, COUNT(*)::text as row_count FROM raw_feature_usage
UNION ALL
SELECT 'raw_page_views' as table_name, COUNT(*)::text as row_count FROM raw_page_views
UNION ALL
SELECT 'raw_user_sessions' as table_name, COUNT(*)::text as row_count FROM raw_user_sessions
UNION ALL
SELECT 'raw_tap_events' as table_name, COUNT(*)::text as row_count FROM raw_tap_events
UNION ALL
-- Entity Layer Counts
SELECT 'ENTITY LAYER' as table_name, '==================' as row_count
UNION ALL
SELECT 'entity_customers' as table_name, COUNT(*)::text as row_count FROM entity_customers
UNION ALL
SELECT 'entity_customers_daily' as table_name, COUNT(*)::text as row_count FROM entity_customers_daily
UNION ALL
SELECT 'entity_customers_history' as table_name, COUNT(*)::text as row_count FROM entity_customers_history
UNION ALL
SELECT 'entity_devices' as table_name, COUNT(*)::text as row_count FROM entity_devices
UNION ALL
SELECT 'entity_devices_hourly' as table_name, COUNT(*)::text as row_count FROM entity_devices_hourly
UNION ALL
SELECT 'entity_devices_history' as table_name, COUNT(*)::text as row_count FROM entity_devices_history
UNION ALL
SELECT 'entity_locations' as table_name, COUNT(*)::text as row_count FROM entity_locations
UNION ALL
SELECT 'entity_locations_weekly' as table_name, COUNT(*)::text as row_count FROM entity_locations_weekly
UNION ALL
SELECT 'entity_locations_history' as table_name, COUNT(*)::text as row_count FROM entity_locations_history
UNION ALL
SELECT 'entity_users' as table_name, COUNT(*)::text as row_count FROM entity_users
UNION ALL
SELECT 'entity_users_weekly' as table_name, COUNT(*)::text as row_count FROM entity_users_weekly
UNION ALL
SELECT 'entity_users_history' as table_name, COUNT(*)::text as row_count FROM entity_users_history
UNION ALL
SELECT 'entity_subscriptions' as table_name, COUNT(*)::text as row_count FROM entity_subscriptions
UNION ALL
SELECT 'entity_subscriptions_monthly' as table_name, COUNT(*)::text as row_count FROM entity_subscriptions_monthly
UNION ALL
SELECT 'entity_subscriptions_history' as table_name, COUNT(*)::text as row_count FROM entity_subscriptions_history
UNION ALL
SELECT 'entity_campaigns' as table_name, COUNT(*)::text as row_count FROM entity_campaigns
UNION ALL
SELECT 'entity_campaigns_daily' as table_name, COUNT(*)::text as row_count FROM entity_campaigns_daily
UNION ALL
SELECT 'entity_campaigns_history' as table_name, COUNT(*)::text as row_count FROM entity_campaigns_history
UNION ALL
SELECT 'entity_features' as table_name, COUNT(*)::text as row_count FROM entity_features
UNION ALL
SELECT 'entity_features_monthly' as table_name, COUNT(*)::text as row_count FROM entity_features_monthly
UNION ALL
SELECT 'entity_features_history' as table_name, COUNT(*)::text as row_count FROM entity_features_history
ORDER BY 1;