-- Test entity_campaigns for campaign integrity and consistency
WITH campaign_validation AS (
    SELECT 
        COUNT(*) AS total_campaigns,
        COUNT(DISTINCT campaign_id) AS unique_campaigns,
        SUM(CASE WHEN performance_score < 0 OR performance_score > 100 THEN 1 ELSE 0 END) AS invalid_performance_score,
        SUM(CASE WHEN cost_per_acquisition < 0 THEN 1 ELSE 0 END) AS negative_cpa,
        SUM(CASE WHEN return_on_ad_spend < -100 THEN 1 ELSE 0 END) AS invalid_roas,
        SUM(CASE WHEN performance_tier NOT IN ('top', 'high', 'medium', 'low', 'poor') THEN 1 ELSE 0 END) AS invalid_tier
    FROM {{ ref('entity_campaigns') }}
),
metric_consistency AS (
    -- Check that performance score aligns with tier
    SELECT 
        COUNT(*) AS inconsistent_tiers
    FROM {{ ref('entity_campaigns') }}
    WHERE (performance_score >= 80 AND performance_tier NOT IN ('top', 'high'))
       OR (performance_score < 40 AND performance_tier NOT IN ('low', 'poor'))
       OR (performance_score BETWEEN 40 AND 60 AND performance_tier != 'medium')
),
attribution_validation AS (
    -- Validate attribution metrics
    SELECT 
        COUNT(*) AS invalid_attribution
    FROM {{ ref('entity_campaigns') }}
    WHERE total_attributed_revenue < 0
       OR (total_conversions = 0 AND total_attributed_revenue > 0)
       OR (total_spend = 0 AND total_impressions > 0)
),
invalid_data AS (
    SELECT 
        v.*,
        mc.inconsistent_tiers,
        av.invalid_attribution
    FROM campaign_validation v
    CROSS JOIN metric_consistency mc
    CROSS JOIN attribution_validation av
    WHERE v.invalid_performance_score > 0
       OR v.negative_cpa > 0
       OR v.invalid_roas > 0
       OR v.invalid_tier > 0
       OR mc.inconsistent_tiers > 0
       OR av.invalid_attribution > 0
)
-- Test fails if campaign entity data is invalid
SELECT * FROM invalid_data