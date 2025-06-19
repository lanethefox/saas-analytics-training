-- Create remaining normalized tables with correct column mappings
-- Non-destructive approach - preserving existing data

-- First, let's check which columns actually exist for users
DO $$
BEGIN
    -- Create normalized users table if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'normalized' 
                   AND table_name = 'users') THEN
        
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
            u.last_activity_date AS last_login,
            u.engagement_score,
            u.is_active_user AS is_active,
            u.total_sessions_30d AS sessions_30d,
            u.total_page_views_30d AS page_views_30d,
            u.features_used_30d AS features_used_30d
        FROM entity.entity_users u
        LEFT JOIN normalized.account_id_mapping m ON u.account_id = m.user_account_id;
        
        CREATE INDEX idx_norm_users_account_id ON normalized.users(account_id);
        CREATE INDEX idx_norm_users_email ON normalized.users(email);
        
        RAISE NOTICE 'Created normalized.users table with % records', 
            (SELECT COUNT(*) FROM normalized.users);
    END IF;
END $$;

-- Create normalized locations table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'normalized' 
                   AND table_name = 'locations') THEN
        
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
            l.is_active_location AS is_active,
            l.total_devices AS device_count,
            l.active_devices AS active_device_count,
            l.operational_status,
            l.seating_capacity
        FROM entity.entity_locations l
        LEFT JOIN normalized.account_id_mapping m ON l.account_id = m.location_account_id;
        
        CREATE INDEX idx_norm_locations_account_id ON normalized.locations(account_id);
        
        RAISE NOTICE 'Created normalized.locations table with % records', 
            (SELECT COUNT(*) FROM normalized.locations);
    END IF;
END $$;

-- Create normalized devices table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'normalized' 
                   AND table_name = 'devices') THEN
        
        CREATE TABLE normalized.devices AS
        SELECT 
            d.device_id::VARCHAR AS device_id,
            COALESCE(m.normalized_account_id, d.account_id::VARCHAR) AS account_id,
            d.location_id::VARCHAR AS location_id,
            d.device_type,
            d.device_type || '_' || d.device_id AS device_name,
            d.serial_number,
            COALESCE(d.manufacturer, 'Generic') AS manufacturer,
            d.model,
            d.firmware_version,
            d.device_installed_date AS installation_date,
            d.last_maintenance_date AS last_maintenance_date,
            d.health_score AS health_score,
            d.uptime_percentage_30d,
            d.device_status AS status,
            d.device_created_at AS created_at,
            d.device_updated_at AS updated_at,
            d.connectivity_status,
            d.operational_status,
            d.last_heartbeat_at,
            d.days_since_maintenance,
            d.maintenance_status
        FROM entity.entity_devices d
        LEFT JOIN normalized.account_id_mapping m ON d.account_id::VARCHAR = m.customer_account_id;
        
        CREATE INDEX idx_norm_devices_account_id ON normalized.devices(account_id);
        CREATE INDEX idx_norm_devices_location_id ON normalized.devices(location_id);
        CREATE INDEX idx_norm_devices_type ON normalized.devices(device_type);
        CREATE INDEX idx_norm_devices_status ON normalized.devices(status);
        
        RAISE NOTICE 'Created normalized.devices table with % records', 
            (SELECT COUNT(*) FROM normalized.devices);
    END IF;
END $$;

-- Create normalized campaigns table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'normalized' 
                   AND table_name = 'campaigns') THEN
        
        CREATE TABLE normalized.campaigns AS
        SELECT 
            c.campaign_id::VARCHAR AS campaign_id,
            c.campaign_name,
            c.campaign_type,
            COALESCE(c.campaign_source, c.utm_source, 'direct') AS channel,
            c.campaign_status AS status,
            c.campaign_created_at AS created_at,
            c.campaign_start_date AS start_date,
            c.campaign_end_date AS end_date,
            c.campaign_budget AS budget,
            c.campaign_spend AS spend,
            c.impressions,
            c.clicks,
            c.conversions,
            c.attributed_revenue AS revenue_attributed,
            c.cost_per_click,
            c.cost_per_acquisition,
            c.return_on_ad_spend,
            c.utm_medium,
            c.utm_campaign
        FROM entity.entity_campaigns c;
        
        CREATE INDEX idx_norm_campaigns_status ON normalized.campaigns(status);
        CREATE INDEX idx_norm_campaigns_channel ON normalized.campaigns(channel);
        CREATE INDEX idx_norm_campaigns_dates ON normalized.campaigns(start_date, end_date);
        
        RAISE NOTICE 'Created normalized.campaigns table with % records', 
            (SELECT COUNT(*) FROM normalized.campaigns);
    END IF;
END $$;

-- Create normalized features table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'normalized' 
                   AND table_name = 'features') THEN
        
        CREATE TABLE normalized.features AS
        SELECT 
            f.feature_key AS feature_id,
            f.feature_name,
            f.feature_category,
            f.feature_name || ' - ' || COALESCE(f.feature_category, 'General') AS description,
            f.created_at AS release_date,
            f.adoption_rate,
            f.active_users,
            f.usage_frequency_daily,
            f.average_session_duration,
            f.total_sessions_30d,
            f.unique_users_30d,
            f.revenue_impact,
            f.user_satisfaction_score
        FROM entity.entity_features f;
        
        CREATE INDEX idx_norm_features_category ON normalized.features(feature_category);
        CREATE INDEX idx_norm_features_adoption ON normalized.features(adoption_rate);
        
        RAISE NOTICE 'Created normalized.features table with % records', 
            (SELECT COUNT(*) FROM normalized.features);
    END IF;
END $$;

-- Summary of all normalized tables
SELECT 
    'Normalized Tables Summary' AS report_type,
    table_name,
    (SELECT COUNT(*) 
     FROM information_schema.columns 
     WHERE table_schema = 'normalized' 
     AND table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'normalized'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
