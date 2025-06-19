-- Create normalized tables with correct column mappings based on actual entity table structure

-- Drop existing normalized tables
DROP TABLE IF EXISTS normalized.subscriptions CASCADE;
DROP TABLE IF EXISTS normalized.users CASCADE;
DROP TABLE IF EXISTS normalized.locations CASCADE;
DROP TABLE IF EXISTS normalized.devices CASCADE;
DROP TABLE IF EXISTS normalized.campaigns CASCADE;
DROP TABLE IF EXISTS normalized.features CASCADE;

-- Create normalized subscriptions table
CREATE TABLE normalized.subscriptions AS
SELECT 
    s.subscription_id::VARCHAR AS subscription_id,
    COALESCE(m.normalized_account_id, s.account_id::VARCHAR) AS account_id,
    s.plan_type AS plan_name,
    CASE 
        WHEN s.monthly_recurring_revenue >= 5000 THEN 'Tier 1'
        WHEN s.monthly_recurring_revenue >= 1000 THEN 'Tier 2'
        WHEN s.monthly_recurring_revenue >= 200 THEN 'Tier 3'
        ELSE 'Tier 4'
    END AS plan_tier,
    s.subscription_status AS status,
    s.subscription_created_at AS created_at,
    s.current_period_end AS updated_at,
    s.subscription_started_at AS start_date,
    s.current_period_end AS end_date,
    s.billing_interval AS billing_cycle,
    COALESCE(s.monthly_recurring_revenue, 0)::NUMERIC(10,2) AS monthly_recurring_revenue,
    CASE WHEN s.subscription_status = 'active' THEN true ELSE false END AS is_active
FROM entity.entity_subscriptions s
LEFT JOIN normalized.account_id_mapping m ON s.account_id::VARCHAR = m.subscription_account_id;

-- Create normalized users table
CREATE TABLE normalized.users AS
SELECT 
    u.user_id::VARCHAR AS user_id,
    COALESCE(m.normalized_account_id, u.account_id::VARCHAR) AS account_id,
    u.email,
    u.first_name,
    u.last_name,
    COALESCE(u.user_role, 'standard') AS role,
    u.user_status AS status,
    u.user_created_at AS created_at,
    u.last_activity_at AS last_login,
    u.engagement_score,
    u.is_active_user AS is_active
FROM entity.entity_users u
LEFT JOIN normalized.account_id_mapping m ON u.account_id = m.user_account_id;
-- Create normalized locations table  
CREATE TABLE normalized.locations AS
SELECT 
    l.location_id::VARCHAR AS location_id,
    COALESCE(m.normalized_account_id, l.account_id::VARCHAR) AS account_id,
    l.location_name,
    l.street_address AS address,
    l.city,
    l.state_code AS state,
    l.country_code AS country,
    l.postal_code,
    l.timezone,
    l.location_created_at AS created_at,
    l.is_active_location AS is_active
FROM entity.entity_locations l
LEFT JOIN normalized.account_id_mapping m ON l.account_id = m.location_account_id;

-- Create normalized devices table
CREATE TABLE normalized.devices AS
SELECT 
    d.device_id::VARCHAR AS device_id,
    COALESCE(m.normalized_account_id, d.account_id::VARCHAR) AS account_id,
    d.location_id::VARCHAR AS location_id,
    d.device_type,
    d.device_type || '_' || d.device_id AS device_name,
    d.serial_number,
    'Generic' AS manufacturer,
    d.model,
    d.firmware_version,
    d.device_installed_date AS installation_date,
    d.last_maintenance_date AS last_maintenance_date,
    d.device_health_score AS health_score,
    d.uptime_percentage_30d,
    d.device_status AS status,
    d.device_created_at AS created_at,
    d.device_updated_at AS updated_at
FROM entity.entity_devices d
LEFT JOIN normalized.account_id_mapping m ON d.account_id::VARCHAR = m.customer_account_id;
-- Create normalized campaigns table
CREATE TABLE normalized.campaigns AS
SELECT 
    c.campaign_id::VARCHAR AS campaign_id,
    c.campaign_name,
    c.campaign_type,
    c.campaign_medium AS channel,
    c.campaign_status AS status,
    c.campaign_created_at AS created_at,
    c.campaign_start_date AS start_date,
    c.campaign_end_date AS end_date,
    c.campaign_budget AS budget,
    c.campaign_spend AS spend,
    c.impressions,
    c.clicks,
    c.conversions,
    c.attributed_revenue AS revenue_attributed
FROM entity.entity_campaigns c;

-- Create normalized features table
CREATE TABLE normalized.features AS
SELECT 
    f.feature_key AS feature_id,
    f.feature_name,
    f.feature_category,
    f.feature_name || ' Description' AS description,
    f.created_at AS release_date,
    f.adoption_rate,
    f.active_users,
    f.usage_frequency_daily,
    f.average_session_duration
FROM entity.entity_features f;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_norm_subscriptions_account_id ON normalized.subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_norm_users_account_id ON normalized.users(account_id);
CREATE INDEX IF NOT EXISTS idx_norm_locations_account_id ON normalized.locations(account_id);
CREATE INDEX IF NOT EXISTS idx_norm_devices_account_id ON normalized.devices(account_id);
CREATE INDEX IF NOT EXISTS idx_norm_devices_location_id ON normalized.devices(location_id);

-- Show summary
SELECT 
    'normalized.subscriptions' AS table_name, COUNT(*) AS record_count FROM normalized.subscriptions
UNION ALL
SELECT 'normalized.users', COUNT(*) FROM normalized.users
UNION ALL
SELECT 'normalized.locations', COUNT(*) FROM normalized.locations  
UNION ALL
SELECT 'normalized.devices', COUNT(*) FROM normalized.devices
UNION ALL
SELECT 'normalized.campaigns', COUNT(*) FROM normalized.campaigns
UNION ALL
SELECT 'normalized.features', COUNT(*) FROM normalized.features
ORDER BY table_name;