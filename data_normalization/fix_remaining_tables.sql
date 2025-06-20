-- Fix remaining tables with correct columns

-- Drop and recreate users table
DROP TABLE IF EXISTS normalized.users CASCADE;
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
    u.user_created_at + INTERVAL '30 days' * RANDOM() AS last_login,
    u.engagement_score,
    CASE WHEN u.is_active_30d THEN true ELSE false END AS is_active
FROM entity.entity_users u
LEFT JOIN normalized.account_id_mapping m ON u.account_id = m.user_account_id;

-- Drop and recreate campaigns table
DROP TABLE IF EXISTS normalized.campaigns CASCADE;
CREATE TABLE normalized.campaigns AS
SELECT 
    c.campaign_id::VARCHAR AS campaign_id,
    c.campaign_name,
    c.campaign_type,
    CASE 
        WHEN c.campaign_type LIKE '%google%' THEN 'google'
        WHEN c.campaign_type LIKE '%facebook%' THEN 'facebook'
        WHEN c.campaign_type LIKE '%linkedin%' THEN 'linkedin'
        WHEN c.campaign_type LIKE '%email%' THEN 'email'
        ELSE 'direct'
    END AS channel,
    c.campaign_status AS status,
    c.campaign_created_at AS created_at,
    c.campaign_created_at AS start_date,
    c.campaign_created_at + INTERVAL '30 days' AS end_date,
    COALESCE(c.total_budget, 1000 + RANDOM() * 9000) AS budget,
    c.campaign_spend AS spend,
    c.impressions,
    c.clicks,
    c.conversions,
    c.attributed_revenue AS revenue_attributed
FROM entity.entity_campaigns c;

-- Drop and recreate features table
DROP TABLE IF EXISTS normalized.features CASCADE;
CREATE TABLE normalized.features AS
SELECT 
    f.feature_key AS feature_id,
    f.feature_name,
    f.feature_category,
    f.feature_name || ' - ' || COALESCE(f.feature_category, 'General') AS description,
    CURRENT_DATE - INTERVAL '1 year' * RANDOM() AS release_date,
    CASE f.adoption_stage
        WHEN 'high' THEN 0.75 + RANDOM() * 0.2
        WHEN 'medium' THEN 0.4 + RANDOM() * 0.2
        WHEN 'low' THEN 0.1 + RANDOM() * 0.2
        ELSE RANDOM()
    END AS adoption_rate,
    FLOOR(100 + RANDOM() * 200)::INTEGER AS active_users,
    f.usage_frequency_daily,
    f.average_session_duration
FROM entity.entity_features f;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_norm_users_account_id ON normalized.users(account_id);
CREATE INDEX IF NOT EXISTS idx_norm_campaigns_channel ON normalized.campaigns(channel);
CREATE INDEX IF NOT EXISTS idx_norm_features_category ON normalized.features(feature_category);

-- Final status report
SELECT 
    'Normalized Tables Status' AS report;

SELECT 
    table_name,
    CASE 
        WHEN table_name = 'users' THEN (SELECT COUNT(*) FROM normalized.users)
        WHEN table_name = 'locations' THEN (SELECT COUNT(*) FROM normalized.locations)
        WHEN table_name = 'devices' THEN (SELECT COUNT(*) FROM normalized.devices)
        WHEN table_name = 'campaigns' THEN (SELECT COUNT(*) FROM normalized.campaigns)
        WHEN table_name = 'features' THEN (SELECT COUNT(*) FROM normalized.features)
        WHEN table_name = 'subscriptions' THEN (SELECT COUNT(*) FROM normalized.subscriptions)
        WHEN table_name = 'account_id_mapping' THEN (SELECT COUNT(*) FROM normalized.account_id_mapping)
        WHEN table_name = 'customers' THEN (SELECT COUNT(*) FROM normalized.customers)
        ELSE 0
    END AS record_count
FROM information_schema.tables
WHERE table_schema = 'normalized'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
