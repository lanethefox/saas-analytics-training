-- Test marketing staging models for campaign data integrity
WITH marketing_validation AS (
    -- Check Google Ads
    SELECT 
        'google_ads' AS platform,
        COUNT(*) AS total_campaigns,
        SUM(CASE WHEN campaign_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN spend < 0 THEN 1 ELSE 0 END) AS negative_spend,
        SUM(CASE WHEN clicks > impressions THEN 1 ELSE 0 END) AS invalid_metrics
    FROM {{ ref('stg_marketing__google_ads_campaigns') }}
    
    UNION ALL
    
    -- Check Facebook Ads
    SELECT 
        'facebook_ads' AS platform,
        COUNT(*) AS total_campaigns,
        SUM(CASE WHEN campaign_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN spend < 0 THEN 1 ELSE 0 END) AS negative_spend,
        SUM(CASE WHEN clicks > impressions THEN 1 ELSE 0 END) AS invalid_metrics
    FROM {{ ref('stg_marketing__facebook_ads_campaigns') }}
    
    UNION ALL
    
    -- Check LinkedIn Ads
    SELECT 
        'linkedin_ads' AS platform,
        COUNT(*) AS total_campaigns,
        SUM(CASE WHEN campaign_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN spend < 0 THEN 1 ELSE 0 END) AS negative_spend,
        SUM(CASE WHEN clicks > impressions THEN 1 ELSE 0 END) AS invalid_metrics
    FROM {{ ref('stg_marketing__linkedin_ads_campaigns') }}
),
touchpoint_validation AS (
    -- Validate attribution touchpoints
    SELECT 
        COUNT(*) AS total_touchpoints,
        SUM(CASE WHEN touchpoint_id IS NULL THEN 1 ELSE 0 END) AS null_touchpoints,
        SUM(CASE WHEN touchpoint_timestamp > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_touchpoints,
        SUM(CASE WHEN channel NOT IN ('organic', 'paid_search', 'paid_social', 'email', 'direct', 'referral') THEN 1 ELSE 0 END) AS invalid_channels
    FROM {{ ref('stg_marketing__attribution_touchpoints') }}
),
marketing_issues AS (
    SELECT 
        m.*
    FROM marketing_validation m
    WHERE m.null_ids > 0
       OR m.negative_spend > 0
       OR m.invalid_metrics > 0
    
    UNION ALL
    
    SELECT 
        'touchpoints' AS platform,
        total_touchpoints AS total_campaigns,
        null_touchpoints AS null_ids,
        future_touchpoints AS negative_spend,
        invalid_channels AS invalid_metrics
    FROM touchpoint_validation
    WHERE null_touchpoints > 0
       OR future_touchpoints > 0
       OR invalid_channels > 0
)
-- Test fails if marketing data has quality issues
SELECT * FROM marketing_issues