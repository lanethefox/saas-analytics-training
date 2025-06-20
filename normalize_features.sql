-- Create normalized.features table
-- Core feature attributes without usage metrics

DROP TABLE IF EXISTS normalized.features CASCADE;

CREATE TABLE normalized.features (
    feature_id SERIAL PRIMARY KEY,
    feature_key TEXT NOT NULL UNIQUE,
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    feature_category TEXT,
    -- Feature metadata
    first_usage_date TIMESTAMP,
    last_usage_date TIMESTAMP,
    feature_age_days NUMERIC,
    -- Feature lifecycle
    lifecycle_stage TEXT,
    feature_maturity TEXT,
    strategic_importance TEXT,
    market_fit_segment TEXT,
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_features_category ON normalized.features(feature_category);
CREATE INDEX idx_features_lifecycle ON normalized.features(lifecycle_stage);
CREATE INDEX idx_features_importance ON normalized.features(strategic_importance);
CREATE INDEX idx_features_first_usage ON normalized.features(first_usage_date);

-- Insert data from entity table
INSERT INTO normalized.features (
    feature_key,
    feature_name,
    feature_category,
    first_usage_date,
    last_usage_date,
    feature_age_days,
    lifecycle_stage,
    feature_maturity,
    strategic_importance,
    market_fit_segment
)
SELECT 
    feature_key,
    feature_name,
    feature_category,
    first_usage_date,
    last_usage_date,
    feature_age_days,
    lifecycle_stage,
    feature_maturity,
    strategic_importance,
    market_fit_segment
FROM entity.entity_features;

-- Show results
SELECT COUNT(*) as feature_count FROM normalized.features;

-- Show all features with key attributes
SELECT 
    feature_id,
    feature_name,
    feature_category,
    lifecycle_stage,
    strategic_importance,
    market_fit_segment
FROM normalized.features
ORDER BY feature_id;

-- Show distribution by category
SELECT 
    feature_category,
    COUNT(*) as feature_count,
    STRING_AGG(feature_name, ', ' ORDER BY feature_name) as features
FROM normalized.features
GROUP BY feature_category
ORDER BY feature_count DESC;

-- Show strategic importance distribution
SELECT 
    strategic_importance,
    COUNT(*) as feature_count,
    STRING_AGG(feature_name, ', ' ORDER BY feature_name) as features
FROM normalized.features
GROUP BY strategic_importance
ORDER BY 
    CASE strategic_importance
        WHEN 'Core' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        ELSE 5
    END;

-- Create feature_usage table for tracking usage by account/user
DROP TABLE IF EXISTS normalized.feature_usage CASCADE;

CREATE TABLE normalized.feature_usage (
    usage_id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    account_id VARCHAR NOT NULL,
    user_id INTEGER,
    usage_date DATE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    total_duration_minutes NUMERIC(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usage_feature FOREIGN KEY (feature_id) 
        REFERENCES normalized.features(feature_id),
    CONSTRAINT fk_usage_account FOREIGN KEY (account_id) 
        REFERENCES normalized.customers(account_id),
    CONSTRAINT fk_usage_user FOREIGN KEY (user_id) 
        REFERENCES normalized.users(user_id)
);

-- Create indexes for feature usage
CREATE INDEX idx_feature_usage_feature ON normalized.feature_usage(feature_id);
CREATE INDEX idx_feature_usage_account ON normalized.feature_usage(account_id);
CREATE INDEX idx_feature_usage_user ON normalized.feature_usage(user_id);
CREATE INDEX idx_feature_usage_date ON normalized.feature_usage(usage_date);
CREATE INDEX idx_feature_usage_composite ON normalized.feature_usage(feature_id, account_id, usage_date);

COMMENT ON TABLE normalized.feature_usage IS 'Tracks daily feature usage by account and user';
