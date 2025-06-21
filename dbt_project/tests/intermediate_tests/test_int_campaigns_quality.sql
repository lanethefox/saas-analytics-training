-- Test int_campaigns__core for data quality
WITH campaign_validation AS (
    SELECT 
        COUNT(*) AS total_campaigns,
        COUNT(DISTINCT campaign_id) AS unique_campaigns,
        COUNT(DISTINCT campaign_source) AS unique_sources,
        SUM(CASE WHEN total_spend < 0 THEN 1 ELSE 0 END) AS negative_spend_count,
        SUM(CASE WHEN impressions < 0 THEN 1 ELSE 0 END) AS negative_impressions,
        SUM(CASE WHEN clicks < 0 THEN 1 ELSE 0 END) AS negative_clicks,
        SUM(CASE WHEN conversions < 0 THEN 1 ELSE 0 END) AS negative_conversions,
        SUM(CASE WHEN clicks > impressions THEN 1 ELSE 0 END) AS invalid_click_rate,
        SUM(CASE WHEN conversions > clicks THEN 1 ELSE 0 END) AS invalid_conversion_rate
    FROM {{ ref('int_campaigns__core') }}
),
invalid_counts AS (
    SELECT *
    FROM campaign_validation
    WHERE negative_spend_count > 0
       OR negative_impressions > 0
       OR negative_clicks > 0
       OR negative_conversions > 0
       OR invalid_click_rate > 0
       OR invalid_conversion_rate > 0
       OR unique_campaigns != total_campaigns
)
-- Test fails if any data quality issues found
SELECT * FROM invalid_counts