-- Create normalized.campaigns table
-- Core campaign attributes without derived metrics

DROP TABLE IF EXISTS normalized.campaigns CASCADE;

CREATE TABLE normalized.campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_key TEXT NOT NULL,
    platform TEXT NOT NULL,
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(50),
    campaign_status VARCHAR(50),
    is_active BOOLEAN DEFAULT FALSE,
    campaign_lifecycle_stage TEXT,
    campaign_created_at TIMESTAMP WITH TIME ZONE,
    campaign_updated_at TIMESTAMP WITH TIME ZONE,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    -- Core metrics that would come from source systems
    total_spend NUMERIC(12,2),
    impressions INTEGER,
    clicks INTEGER,
    conversions NUMERIC(10,2),
    conversion_value NUMERIC(12,2),
    -- Targeting attributes
    target_audience TEXT,
    target_location TEXT,
    bid_strategy VARCHAR(100),
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_campaigns_platform ON normalized.campaigns(platform);
CREATE INDEX idx_campaigns_status ON normalized.campaigns(campaign_status);
CREATE INDEX idx_campaigns_type ON normalized.campaigns(campaign_type);
CREATE INDEX idx_campaigns_created ON normalized.campaigns(campaign_created_at);
CREATE INDEX idx_campaigns_active ON normalized.campaigns(is_active);
CREATE INDEX idx_campaigns_dates ON normalized.campaigns(start_date, end_date);

-- Insert data from entity table
INSERT INTO normalized.campaigns (
    campaign_id,
    campaign_key,
    platform,
    campaign_name,
    campaign_type,
    campaign_status,
    is_active,
    campaign_lifecycle_stage,
    campaign_created_at,
    campaign_updated_at,
    start_date,
    end_date,
    total_spend,
    impressions,
    clicks,
    conversions,
    conversion_value,
    target_audience,
    target_location,
    bid_strategy
)
SELECT 
    campaign_id,
    campaign_key,
    platform,
    campaign_name,
    campaign_type,
    campaign_status,
    is_active,
    campaign_lifecycle_stage,
    campaign_created_at,
    campaign_updated_at,
    start_date,
    end_date,
    total_spend,
    impressions,
    clicks,
    conversions,
    conversion_value::INTEGER as conversion_value,
    target_audience,
    target_location,
    bid_strategy
FROM entity.entity_campaigns;

-- Show results
SELECT COUNT(*) as campaign_count FROM normalized.campaigns;

-- Show sample data
SELECT 
    campaign_id,
    platform,
    campaign_type,
    campaign_status,
    is_active,
    total_spend,
    impressions,
    clicks,
    conversions
FROM normalized.campaigns
LIMIT 5;

-- Show distribution by platform
SELECT 
    platform,
    COUNT(*) as campaign_count,
    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_campaigns,
    SUM(total_spend) as total_platform_spend,
    AVG(conversions) as avg_conversions
FROM normalized.campaigns
GROUP BY platform
ORDER BY campaign_count DESC;

-- Show distribution by status
SELECT 
    campaign_status,
    COUNT(*) as campaign_count,
    AVG(total_spend) as avg_spend,
    SUM(impressions) as total_impressions
FROM normalized.campaigns
GROUP BY campaign_status
ORDER BY campaign_count DESC;

-- Show campaign lifecycle distribution
SELECT 
    campaign_lifecycle_stage,
    COUNT(*) as campaign_count,
    AVG(EXTRACT(DAY FROM (end_date - start_date))) as avg_duration_days
FROM normalized.campaigns
WHERE start_date IS NOT NULL AND end_date IS NOT NULL
GROUP BY campaign_lifecycle_stage
ORDER BY campaign_count DESC;
